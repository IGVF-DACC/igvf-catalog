import logging
from abc import ABC, abstractmethod
from typing import Optional

import boto3
import smart_open

logger = logging.getLogger(__name__)


# zlib's default compromise. gzip's own default is 9, which spends a lot of CPU
# on repetitive JSONL for a small extra size reduction.
GZIP_COMPRESSLEVEL = 6


def gzip_s3_key(key: str, compress: bool = True) -> str:
    # Callers pass the JSONL name. Compressed objects are gzipped, and ClickHouse
    # detects that from the .gz suffix. Leave a key that is already gzipped alone.
    # Uncompressed objects keep the caller's name, with a trailing .gz removed so
    # the suffix matches the bytes.
    if compress:
        if key.endswith('.gz'):
            return key
        logger.warning(
            'Compress is enabled but S3 key %s does not end with .gz; '
            'the object will be stored as %s.gz',
            key, key,
        )
        return f'{key}.gz'
    if key.endswith('.gz'):
        return key[:-len('.gz')]
    return key


class Writer(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def write(self, content):
        pass

    @abstractmethod
    def close(self, success: bool = True):
        pass

    @property
    @abstractmethod
    def destination(self):
        pass

    def add_tag(self, key: str, value: str):
        pass

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Only finalize (e.g. collections-tag) the output when the body completed
        # without raising. Writers open lazily on the first write(), so if the
        # body fails (or produces nothing) before writing, no output file is
        # created at all. Returning False propagates any exception.
        self.close(success=exc_type is None)
        return False


class S3Writer(Writer):

    def __init__(self, bucket: str, key: str, session: boto3.Session, collections_tag: Optional[str] = None, *, compress: bool = True) -> None:
        self.bucket = bucket
        self.compress = compress
        self.key = gzip_s3_key(key, compress=compress)
        self.session = session
        self._s3_uri = None
        self.s3_file = None
        self.s3_tags: list[dict[str, str]] = []
        if collections_tag is not None:
            self.add_tag('collections', collections_tag)

    def add_tag(self, key: str, value: str):
        for tag in self.s3_tags:
            if tag['Key'] == key:
                tag['Value'] = tag['Value'] + ' ' + value
                return
        self.s3_tags.append({'Key': key, 'Value': value})

    def _put_tags(self):
        if not self.s3_tags:
            return
        client = self.session.client('s3')
        # smart_open finalizes the object with CompleteMultipartUpload. Right
        # after that, PutObjectTagging (a subresource op made through a fresh
        # client) can intermittently return NoSuchKey while the just-completed
        # object propagates. Wait for the object to be visible before tagging.
        client.get_waiter('object_exists').wait(
            Bucket=self.bucket, Key=self.key,
            WaiterConfig={'Delay': 1, 'MaxAttempts': 5},
        )
        client.put_object_tagging(Bucket=self.bucket, Key=self.key, Tagging={
            'TagSet': self.s3_tags
        })

    def open(self):
        # Defer creating the S3 object until the first write so a run that fails
        # (or writes nothing) before producing output leaves no file behind.
        self.s3_file = None

    def write(self, content):
        if self.s3_file is None:
            # Force the compression mode. Inferring it from the key would
            # silently write plain bytes if the S3 stream name did not end in
            # .gz, and compression_kwargs would be ignored. 'disable' writes
            # the bytes as-is. smart-open 9 closes the S3 upload from close(),
            # including the gzip trailer when compressing.
            open_kwargs = {
                'mode': 'w',
                'newline': '\n',
                'transport_params': {'client': self.session.client('s3')},
            }
            if self.compress:
                open_kwargs['compression'] = '.gz'
                open_kwargs['compression_kwargs'] = {
                    'compresslevel': GZIP_COMPRESSLEVEL}
            else:
                open_kwargs['compression'] = 'disable'
            self.s3_file = smart_open.open(self.destination, **open_kwargs)
        self.s3_file.write(content)

    def close(self, success: bool = True):
        if self.s3_file is None:
            # Nothing was written, so no object was created: nothing to
            # finalize or tag.
            return
        self.s3_file.close()
        if success:
            self._put_tags()

    def _create_s3_uri(self):
        return f's3://{self.bucket}/{self.key}'

    @property
    def destination(self):
        if self._s3_uri is None:
            self._s3_uri = self._create_s3_uri()
            return self._s3_uri
        else:
            return self._s3_uri


class LocalWriter(Writer):

    def __init__(self, filepath: str) -> None:
        self.filepath = filepath
        self.file = None

    def open(self):
        # Defer creating the file until the first write so a run that fails
        # (or writes nothing) before producing output leaves no file behind.
        self.file = None

    def write(self, content):
        if self.file is None:
            self.file = open(self.filepath, mode='w')
        self.file.write(content)

    def close(self, success: bool = True):
        if self.file is None:
            # Nothing was written, so no file was created: nothing to close.
            return
        self.file.close()

    @property
    def destination(self):
        return self.filepath


class SpyWriter(Writer):

    def __init__(self) -> None:
        self.container = []

    def open(self):
        pass

    def write(self, content):
        self.container.append(content)

    def close(self, success: bool = True):
        pass

    @property
    def contents(self):
        return self.container

    @property
    def destination(self):
        pass


def get_writer(
        filepath: Optional[str] = None,
        bucket: Optional[str] = None,
        key: Optional[str] = None,
        session: Optional[boto3.Session] = None,
        collections_tag: Optional[str] = None,
        compress: bool = True,
) -> Writer:
    if filepath is not None:
        logger.info(f'Using local writer for filepath: {filepath}')
        return LocalWriter(filepath)
    else:
        if bucket is None or key is None:
            raise ValueError(
                'both bucket and key are required when writing to S3')
        logger.info(f'Using S3 writer for bucket: {bucket}, key: {key}')
        return S3Writer(bucket, key, session, collections_tag, compress=compress)
