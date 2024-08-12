import boto3
import smart_open

from typing import Optional


class Writer:
    def __init__(self):
        pass

    def open(self):
        raise NotImplementedError

    def write(self, content):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError


class S3Writer(Writer):

    def __init__(self, bucket: str, key: str, session: boto3.Session) -> None:
        self.bucket = bucket
        self.key = key
        self.session = session
        self._s3_uri = None
        self.s3_file = None

    def open(self):
        self.s3_file = smart_open.open(self.s3_uri, mode='w', transport_params={
                                       'client': self.session.client('s3')})

    def write(self, content):
        self.s3_file.write(content)

    def close(self):
        self.s3_file.close()

    def _create_s3_uri(self):
        return f's3://{self.bucket}/{self.key}'

    @property
    def s3_uri(self):
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
        self.file = open(self.filepath, mode='w')

    def write(self, content):
        self.file.write(content)

    def close(self):
        self.file.close()


def get_writer(
        filepath: Optional[str] = None,
        bucket: Optional[str] = None,
        key: Optional[str] = None,
        session: Optional[boto3.Session] = None
) -> Writer:
    if filepath is not None:
        return LocalWriter(filepath)
    else:
        return S3Writer(bucket, key, session)
