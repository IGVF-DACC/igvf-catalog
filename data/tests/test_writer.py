import pytest
from unittest.mock import MagicMock, mock_open
from adapters.writer import S3Writer, LocalWriter, get_writer


def test_s3_writer_open(mocker):
    mock_session = MagicMock()
    mock_s3_client = MagicMock()
    mocker.patch('adapters.writer.boto3.Session.client',
                 return_value=mock_s3_client)
    mock_smart_open = mocker.patch(
        'adapters.writer.smart_open.open', return_value=MagicMock())

    writer = S3Writer(bucket='test-bucket',
                      key='test-key', session=mock_session)
    writer.open()

    mock_smart_open.assert_called_once_with(
        's3://test-bucket/test-key',
        mode='w',
        transport_params={'client': mock_session.client('s3')}
    )
    assert writer.s3_file is not None


def test_s3_writer_write(mocker):
    mock_file = MagicMock()
    mocker.patch('adapters.writer.smart_open.open', return_value=mock_file)

    writer = S3Writer(bucket='test-bucket',
                      key='test-key', session=MagicMock())
    writer.open()
    writer.write('test content')

    mock_file.write.assert_called_once_with('test content')


def test_s3_writer_close(mocker):
    mock_file = MagicMock()
    mocker.patch('adapters.writer.smart_open.open', return_value=mock_file)

    writer = S3Writer(bucket='test-bucket',
                      key='test-key', session=MagicMock())
    writer.open()
    writer.close()

    mock_file.close.assert_called_once()


def test_s3_writer_close_with_tagging(mocker):
    mock_file = MagicMock()
    mock_add_version_tag = mocker.patch.object(S3Writer, 'add_version_tag')
    mocker.patch('adapters.writer.smart_open.open', return_value=mock_file)
    writer = S3Writer(bucket='test-bucket',
                      key='test-key', session=MagicMock(), version_tag='v123')
    writer.open()
    writer.close()
    mock_file.close.assert_called_once()
    mock_add_version_tag.assert_called_once_with(value='v123')


def test_s3_writer_destination():
    session = MagicMock()
    writer = S3Writer(bucket='test-bucket', key='test-key', session=session)
    assert writer.destination == 's3://test-bucket/test-key'


def test_local_writer_open(mocker):
    mock_open_fn = mocker.patch('builtins.open', mock_open())

    writer = LocalWriter(filepath='/path/to/file.txt')
    writer.open()

    mock_open_fn.assert_called_once_with('/path/to/file.txt', mode='w')
    assert writer.file is not None


def test_local_writer_write(mocker):
    mock_open_instance = mock_open()
    mocker.patch('builtins.open', mock_open_instance)

    writer = LocalWriter(filepath='/path/to/file.txt')
    writer.open()
    writer.write('test content')

    mock_open_instance().write.assert_called_once_with('test content')


def test_local_writer_close(mocker):
    mock_open_instance = mock_open()
    mocker.patch('builtins.open', mock_open_instance)

    writer = LocalWriter(filepath='/path/to/file.txt')
    writer.open()
    writer.close()

    mock_open_instance().close.assert_called_once()


def test_local_writer_destination():
    writer = LocalWriter(filepath='/path/to/file.txt')
    assert writer.destination == '/path/to/file.txt'


def test_get_writer_local(mocker):
    filepath = '/path/to/file.txt'
    writer = get_writer(filepath=filepath)
    assert isinstance(writer, LocalWriter)


def test_get_writer_s3(mocker):
    bucket = 'test-bucket'
    key = 'test-key'
    session = MagicMock()
    writer = get_writer(bucket=bucket, key=key, session=session)
    assert isinstance(writer, S3Writer)
