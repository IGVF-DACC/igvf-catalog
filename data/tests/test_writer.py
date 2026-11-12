import gzip

import pytest
import smart_open
from unittest.mock import MagicMock, mock_open
from adapters.writer import S3Writer, LocalWriter, get_writer, GZIP_COMPRESSLEVEL


def test_s3_writer_opens_lazily_on_first_write(mocker):
    mock_session = MagicMock()
    mock_s3_client = MagicMock()
    mocker.patch('adapters.writer.boto3.Session.client',
                 return_value=mock_s3_client)
    mock_smart_open = mocker.patch(
        'adapters.writer.smart_open.open', return_value=MagicMock())

    writer = S3Writer(bucket='test-bucket',
                      key='test-key.gz', session=mock_session)
    writer.open()

    # open() defers: no S3 object is created until something is actually written
    mock_smart_open.assert_not_called()
    assert writer.s3_file is None

    writer.write('content')

    mock_smart_open.assert_called_once_with(
        's3://test-bucket/test-key.gz',
        mode='w',
        newline='\n',
        compression='.gz',
        compression_kwargs={'compresslevel': GZIP_COMPRESSLEVEL},
        transport_params={'client': mock_session.client('s3')},
    )
    assert writer.s3_file is not None


def test_s3_writer_write(mocker):
    mock_file = MagicMock()
    mocker.patch('adapters.writer.smart_open.open', return_value=mock_file)

    writer = S3Writer(bucket='test-bucket',
                      key='test-key.gz', session=MagicMock())
    writer.open()
    writer.write('{"id": "a"}\n')
    writer.write('{"id": "b"}\n')

    assert mock_file.write.call_args_list == [
        mocker.call('{"id": "a"}\n'),
        mocker.call('{"id": "b"}\n'),
    ]


def test_smart_open_gzip_close_roundtrip(tmp_path):
    # smart-open 9 must finish the gzip trailer when close() is called, which
    # is how S3Writer finalizes an upload outside a with-block.
    path = tmp_path / 'rows.jsonl.gz'
    handle = smart_open.open(
        str(path),
        mode='w',
        newline='\n',
        compression='.gz',
        compression_kwargs={'compresslevel': GZIP_COMPRESSLEVEL},
    )
    handle.write('{"id": "a"}\n')
    handle.close()

    with gzip.open(path, 'rt', newline='\n') as gz:
        assert gz.read() == '{"id": "a"}\n'


def test_s3_writer_close(mocker):
    mock_file = MagicMock()
    mocker.patch('adapters.writer.smart_open.open', return_value=mock_file)

    writer = S3Writer(bucket='test-bucket',
                      key='test-key.gz', session=MagicMock())
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
                      key='test-key.gz', session=mock_session, collections_tag='v123')
    writer.open()
    writer.write('content')
    writer.close()
    mock_file.close.assert_called_once()
    mock_s3_client.put_object_tagging.assert_called_once_with(
        Bucket='test-bucket', Key='test-key.gz',
        Tagging={'TagSet': [{'Key': 'collections', 'Value': 'v123'}]}
    )


def test_s3_writer_close_without_write_creates_nothing(mocker):
    mock_session = MagicMock()
    mock_smart_open = mocker.patch(
        'adapters.writer.smart_open.open', return_value=MagicMock())
    writer = S3Writer(bucket='test-bucket',
                      key='test-key.gz', session=mock_session, collections_tag='v123')
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
                      key='test-key.gz', session=mock_session, collections_tag='v123')
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
                      key='test-key.gz', session=mock_session, collections_tag='v123')
    writer.open()
    writer.write('content')
    writer.close()

    # The just-completed multipart object may not be immediately visible to a
    # PutObjectTagging call, so we wait on the object_exists waiter first.
    mock_s3_client.get_waiter.assert_called_once_with('object_exists')
    mock_s3_client.get_waiter.return_value.wait.assert_called_once_with(
        Bucket='test-bucket', Key='test-key.gz',
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
                      key='test-key.gz', session=mock_session)
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
                      key='test-key.gz', session=mock_session, collections_tag='v123')
    writer.add_tag('source', 'oncotree')
    writer.add_tag('format', 'jsonl')
    writer.open()
    writer.write('content')
    writer.close()
    mock_s3_client.put_object_tagging.assert_called_once_with(
        Bucket='test-bucket', Key='test-key.gz',
        Tagging={'TagSet': [
            {'Key': 'collections', 'Value': 'v123'},
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
                      key='test-key.gz', session=mock_session)
    writer.add_tag('portal_accession', 'IGVFFI0001')
    writer.add_tag('portal_accession', 'IGVFFI0002')
    writer.add_tag('portal_accession', 'IGVFFI0003')
    writer.open()
    writer.write('content')
    writer.close()
    mock_s3_client.put_object_tagging.assert_called_once_with(
        Bucket='test-bucket', Key='test-key.gz',
        Tagging={'TagSet': [
            {'Key': 'portal_accession', 'Value': 'IGVFFI0001 IGVFFI0002 IGVFFI0003'},
        ]}
    )


def test_s3_writer_close_no_tags_skips_api_call(mocker):
    mock_file = MagicMock()
    mock_session = MagicMock()
    mocker.patch('adapters.writer.smart_open.open', return_value=mock_file)
    writer = S3Writer(bucket='test-bucket',
                      key='test-key.gz', session=mock_session)
    writer.open()
    writer.write('content')
    writer.close()
    mock_session.client('s3').put_object_tagging.assert_not_called()


def test_s3_writer_destination():
    session = MagicMock()
    writer = S3Writer(bucket='test-bucket', key='test-key.gz', session=session)
    assert writer.destination == 's3://test-bucket/test-key.gz'
    assert writer.key == 'test-key.gz'


def test_s3_writer_keeps_gz_key():
    writer = S3Writer(bucket='test-bucket',
                      key='variants/file.jsonl.gz', session=MagicMock())
    assert writer.key == 'variants/file.jsonl.gz'
    assert writer.destination == 's3://test-bucket/variants/file.jsonl.gz'


def test_s3_writer_rejects_key_without_gz_suffix():
    with pytest.raises(ValueError, match=r'S3 key must end with \.gz'):
        S3Writer(bucket='test-bucket',
                 key='variants/file.jsonl', session=MagicMock())


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


def test_get_writer_local(caplog):
    filepath = '/path/to/file.txt'
    with caplog.at_level('INFO'):
        writer = get_writer(filepath=filepath)
    assert isinstance(writer, LocalWriter)
    assert f'Using local writer for filepath: {filepath}' in caplog.text


def test_get_writer_s3(caplog):
    bucket = 'test-bucket'
    key = 'test-key.gz'
    session = MagicMock()
    with caplog.at_level('INFO'):
        writer = get_writer(bucket=bucket, key=key, session=session)
    assert isinstance(writer, S3Writer)
    assert writer.key == key
    assert f'Using S3 writer for bucket: {bucket}, key: {key}' in caplog.text


def test_get_writer_s3_requires_bucket_and_key(caplog):
    session = MagicMock()
    with caplog.at_level('INFO'):
        with pytest.raises(ValueError, match='both bucket and key are required when writing to S3'):
            get_writer(bucket='test-bucket', session=session)
        with pytest.raises(ValueError, match='both bucket and key are required when writing to S3'):
            get_writer(key='test-key.gz', session=session)
        with pytest.raises(ValueError, match='both bucket and key are required when writing to S3'):
            get_writer(session=session)
    assert 'Using S3 writer' not in caplog.text
