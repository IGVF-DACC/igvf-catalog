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
    mock_s3_client.get_object_tagging.return_value = {'TagSet': []}
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


def test_s3_writer_close_with_multiple_tags(mocker):
    mock_file = MagicMock()
    mock_session = MagicMock()
    mock_s3_client = mock_session.client('s3')
    mock_s3_client.get_object_tagging.return_value = {'TagSet': []}
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


def test_s3_writer_appends_to_existing_tag_value(mocker):
    mock_file = MagicMock()
    mock_session = MagicMock()
    mock_s3_client = mock_session.client('s3')
    mock_s3_client.get_object_tagging.return_value = {
        'TagSet': [{'Key': 'version', 'Value': 'v101 v100'}]
    }
    mocker.patch('adapters.writer.smart_open.open', return_value=mock_file)
    writer = S3Writer(bucket='test-bucket',
                      key='test-key', session=mock_session, version_tag='v123')
    writer.open()
    writer.write('content')
    writer.close()
    mock_s3_client.put_object_tagging.assert_called_once_with(
        Bucket='test-bucket', Key='test-key',
        Tagging={'TagSet': [{'Key': 'version', 'Value': 'v100 v101 v123'}]}
    )


def test_s3_writer_skips_duplicate_tag_value(mocker):
    mock_file = MagicMock()
    mock_session = MagicMock()
    mock_s3_client = mock_session.client('s3')
    mock_s3_client.get_object_tagging.return_value = {
        'TagSet': [{'Key': 'version', 'Value': 'v123'}]
    }
    mocker.patch('adapters.writer.smart_open.open', return_value=mock_file)
    writer = S3Writer(bucket='test-bucket',
                      key='test-key', session=mock_session, version_tag='v123')
    writer.open()
    writer.write('content')
    writer.close()
    mock_s3_client.put_object_tagging.assert_called_once_with(
        Bucket='test-bucket', Key='test-key',
        Tagging={'TagSet': [{'Key': 'version', 'Value': 'v123'}]}
    )


def test_s3_writer_handles_no_such_key_on_get_tags(mocker):
    mock_file = MagicMock()
    mock_session = MagicMock()
    mock_s3_client = mock_session.client('s3')
    mock_s3_client.exceptions.NoSuchKey = type('NoSuchKey', (Exception,), {})
    mock_s3_client.get_object_tagging.side_effect = mock_s3_client.exceptions.NoSuchKey()
    mocker.patch('adapters.writer.smart_open.open', return_value=mock_file)
    writer = S3Writer(bucket='test-bucket',
                      key='test-key', session=mock_session, version_tag='v123')
    writer.open()
    writer.write('content')
    writer.close()
    mock_s3_client.put_object_tagging.assert_called_once_with(
        Bucket='test-bucket', Key='test-key',
        Tagging={'TagSet': [{'Key': 'version', 'Value': 'v123'}]}
    )


def test_s3_writer_preserves_unrelated_existing_tags(mocker):
    mock_file = MagicMock()
    mock_session = MagicMock()
    mock_s3_client = mock_session.client('s3')
    mock_s3_client.get_object_tagging.return_value = {
        'TagSet': [
            {'Key': 'owner', 'Value': 'otto'},
            {'Key': 'version', 'Value': 'v100'},
        ]
    }
    mocker.patch('adapters.writer.smart_open.open', return_value=mock_file)
    writer = S3Writer(bucket='test-bucket',
                      key='test-key', session=mock_session, version_tag='v123')
    writer.add_tag('source', 'oncotree')
    writer.open()
    writer.write('content')
    writer.close()
    call_args = mock_s3_client.put_object_tagging.call_args
    tag_set = call_args.kwargs['Tagging']['TagSet']
    tags_by_key = {t['Key']: t['Value'] for t in tag_set}
    assert tags_by_key['owner'] == 'otto'
    assert tags_by_key['version'] == 'v100 v123'
    assert tags_by_key['source'] == 'oncotree'


def test_s3_writer_fetches_tags_before_overwriting_object(mocker):
    mock_file = MagicMock()
    mock_session = MagicMock()
    mock_s3_client = mock_session.client('s3')
    mock_s3_client.get_object_tagging.return_value = {'TagSet': []}
    mock_smart_open = mocker.patch(
        'adapters.writer.smart_open.open', return_value=mock_file)
    writer = S3Writer(bucket='test-bucket',
                      key='test-key', session=mock_session, version_tag='v1')
    writer.open()
    writer.write('content')
    # get_object_tagging must be called before smart_open overwrites the object
    mock_s3_client.get_object_tagging.assert_called_once()
    assert mock_s3_client.get_object_tagging.call_args.kwargs['Key'] == 'test-key'


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
