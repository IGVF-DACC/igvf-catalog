from abc import ABC, abstractmethod

import boto3
import smart_open

from typing import Optional


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
        # Only finalize (e.g. version-tag) the output when the body completed
        # without raising. Writers open lazily on the first write(), so if the
        # body fails (or produces nothing) before writing, no output file is
        # created at all. Returning False propagates any exception.
        self.close(success=exc_type is None)
        return False


class S3Writer(Writer):

    def __init__(self, bucket: str, key: str, session: boto3.Session, version_tag: Optional[str] = None) -> None:
        self.bucket = bucket
        self.key = key
        self.session = session
        self._s3_uri = None
        self.s3_file = None
        self.s3_tags: list[dict[str, str]] = []
        if version_tag is not None:
            self.add_tag('version', version_tag)

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
            self.s3_file = smart_open.open(self.destination, mode='w', transport_params={
                                           'client': self.session.client('s3')})
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
        version_tag: Optional[str] = None
) -> Writer:
    if filepath is not None:
        return LocalWriter(filepath)
    else:
        return S3Writer(bucket, key, session, version_tag)
