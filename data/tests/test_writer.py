import pytest
from unittest.mock import MagicMock, mock_open
from adapters.writer import S3Writer, LocalWriter, get_writer


def test_s3_writer_opens_lazily_on_first_write(mocker):
    mock_session = MagicMock()
    mock_s3_client = MagicMock()
    mocker.patch('adapters.writer.boto3.Session.client',
                 return_value=mock_s3_client)
    mock_smart_open = mocker.patch(
        'adapters.writer.smart_open.open', return_value=MagicMock())

    writer = S3Writer(bucket='test-bucket',
                      key='test-key', session=mock_session)
    writer.open()

    # open() defers: no S3 object is created until something is actually written
    mock_smart_open.assert_not_called()
    assert writer.s3_file is None

    writer.write('content')

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
    writer.write('content')
    writer.close()

    mock_file.close.assert_called_once()


def test_s3_writer_close_with_tagging(mocker):
    mock_file = MagicMock()
    mock_session = MagicMock()
    mock_s3_client = mock_session.client('s3')
    mocker.patch('adapters.writer.smart_open.open', return_value=mock_file)
    writer = S3Writer(bucket='test-bucket',
                      key='test-key', session=mock_session, version_tag='v123')
    writer.open()
    writer.write('content')
    writer.close()
    mock_file.close.assert_called_once()
    mock_s3_client.put_object_tagging.assert_called_once_with(
        Bucket='test-bucket', Key='test-key',
        Tagging={'TagSet': [{'Key': 'version', 'Value': 'v123'}]}
    )


def test_s3_writer_close_without_write_creates_nothing(mocker):
    mock_session = MagicMock()
    mock_smart_open = mocker.patch(
        'adapters.writer.smart_open.open', return_value=MagicMock())
    writer = S3Writer(bucket='test-bucket',
                      key='test-key', session=mock_session, version_tag='v123')
    writer.open()
    writer.close()
    # No write happened, so no object should be created and no tag applied.
    mock_smart_open.assert_not_called()
    mock_session.client('s3').put_object_tagging.assert_not_called()


def test_s3_writer_context_manager_no_file_on_early_failure(mocker):
    mock_session = MagicMock()
    mock_smart_open = mocker.patch(
        'adapters.writer.smart_open.open', return_value=MagicMock())
    writer = S3Writer(bucket='test-bucket',
                      key='test-key', session=mock_session, version_tag='v123')
    with pytest.raises(RuntimeError):
        with writer:
            raise RuntimeError('setup failed before writing')
    # A failure before any write must not create or tag an (empty) object.
    mock_smart_open.assert_not_called()
    mock_session.client('s3').put_object_tagging.assert_not_called()


def test_s3_writer_waits_for_object_before_tagging(mocker):
    mock_file = MagicMock()
    mock_session = MagicMock()
    mock_s3_client = mock_session.client('s3')
    mocker.patch('adapters.writer.smart_open.open', return_value=mock_file)
    writer = S3Writer(bucket='test-bucket',
                      key='test-key', session=mock_session, version_tag='v123')
    writer.open()
    writer.write('content')
    writer.close()

    # The just-completed multipart object may not be immediately visible to a
    # PutObjectTagging call, so we wait on the object_exists waiter first.
    mock_s3_client.get_waiter.assert_called_once_with('object_exists')
    mock_s3_client.get_waiter.return_value.wait.assert_called_once_with(
        Bucket='test-bucket', Key='test-key',
        WaiterConfig={'Delay': 1, 'MaxAttempts': 5},
    )
    # Tagging must happen only after waiting for the object to exist.
    call_names = [c[0] for c in mock_s3_client.mock_calls]
    wait_index = next(i for i, name in enumerate(call_names)
                      if name.endswith('wait'))
    tag_index = call_names.index('put_object_tagging')
    assert wait_index < tag_index


def test_s3_writer_no_wait_when_no_tags(mocker):
    mock_file = MagicMock()
    mock_session = MagicMock()
    mock_s3_client = mock_session.client('s3')
    mocker.patch('adapters.writer.smart_open.open', return_value=mock_file)
    writer = S3Writer(bucket='test-bucket',
                      key='test-key', session=mock_session)
    writer.open()
    writer.write('content')
    writer.close()

    # No tags => no tagging call and no need to wait on the object.
    mock_s3_client.put_object_tagging.assert_not_called()
    mock_s3_client.get_waiter.assert_not_called()


def test_s3_writer_close_with_multiple_tags(mocker):
    mock_file = MagicMock()
    mock_session = MagicMock()
    mock_s3_client = mock_session.client('s3')
    mocker.patch('adapters.writer.smart_open.open', return_value=mock_file)
    writer = S3Writer(bucket='test-bucket',
                      key='test-key', session=mock_session, version_tag='v123')
    writer.add_tag('source', 'oncotree')
    writer.add_tag('format', 'jsonl')
    writer.open()
    writer.write('content')
    writer.close()
    mock_s3_client.put_object_tagging.assert_called_once_with(
        Bucket='test-bucket', Key='test-key',
        Tagging={'TagSet': [
            {'Key': 'version', 'Value': 'v123'},
            {'Key': 'source', 'Value': 'oncotree'},
            {'Key': 'format', 'Value': 'jsonl'},
        ]}
    )


def test_s3_writer_add_tag_appends_value_for_same_key(mocker):
    mock_file = MagicMock()
    mock_session = MagicMock()
    mock_s3_client = mock_session.client('s3')
    mocker.patch('adapters.writer.smart_open.open', return_value=mock_file)
    writer = S3Writer(bucket='test-bucket',
                      key='test-key', session=mock_session)
    writer.add_tag('portal_accession', 'IGVFFI0001')
    writer.add_tag('portal_accession', 'IGVFFI0002')
    writer.add_tag('portal_accession', 'IGVFFI0003')
    writer.open()
    writer.write('content')
    writer.close()
    mock_s3_client.put_object_tagging.assert_called_once_with(
        Bucket='test-bucket', Key='test-key',
        Tagging={'TagSet': [
            {'Key': 'portal_accession', 'Value': 'IGVFFI0001 IGVFFI0002 IGVFFI0003'},
        ]}
    )


def test_s3_writer_close_no_tags_skips_api_call(mocker):
    mock_file = MagicMock()
    mock_session = MagicMock()
    mocker.patch('adapters.writer.smart_open.open', return_value=mock_file)
    writer = S3Writer(bucket='test-bucket',
                      key='test-key', session=mock_session)
    writer.open()
    writer.write('content')
    writer.close()
    mock_session.client('s3').put_object_tagging.assert_not_called()


def test_s3_writer_destination():
    session = MagicMock()
    writer = S3Writer(bucket='test-bucket', key='test-key', session=session)
    assert writer.destination == 's3://test-bucket/test-key'


def test_local_writer_opens_lazily_on_first_write(mocker):
    mock_open_fn = mocker.patch('builtins.open', mock_open())

    writer = LocalWriter(filepath='/path/to/file.txt')
    writer.open()

    # open() defers: no file is created until something is actually written
    mock_open_fn.assert_not_called()
    assert writer.file is None

    writer.write('content')

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
    writer.write('content')
    writer.close()

    mock_open_instance().close.assert_called_once()


def test_local_writer_close_without_write_creates_nothing(mocker):
    mock_open_fn = mocker.patch('builtins.open', mock_open())

    writer = LocalWriter(filepath='/path/to/file.txt')
    writer.open()
    writer.close()

    # No write happened, so no file should be created.
    mock_open_fn.assert_not_called()


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
