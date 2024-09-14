from unittest.mock import patch, Mock

from db.s3 import S3


@patch('boto3.Session')
def test_s3_constructor_ingests_proper_values_and_instantiates_boto(mock_session):
    aws_profile = 'test_profile'
    bucket = 'test_bucket'
    output_folder = './test'

    s3_mock = Mock()
    mock_session.return_value = s3_mock

    s3 = S3(aws_profile, bucket, output_folder)

    assert s3.bucket == bucket
    assert s3.output_folder == output_folder

    mock_session.assert_called_with(profile_name=aws_profile)
    s3_mock.client.assert_called_with('s3')
    s3_mock.ass


@patch('boto3.Session')
def test_s3_downloads_list_of_files_from_folder(mock_session):
    s3_mock = Mock()
    client_mock = Mock()
    mock_session.return_value = s3_mock
    s3_mock.client.return_value = client_mock
    client_mock.list_objects_v2.return_value = {
        'Contents': [{'Key': 'file1.jsonl'}, {'Key': 'file2.jsonl'}]}

    s3 = S3('aws_profile', 'bucket', 'output_folder')

    files = s3.download_s3_files('genes')

    client_mock.list_objects_v2.assert_called_with(
        Bucket='bucket', Prefix='genes/')
    client_mock.download_file.assert_any_call(
        'bucket', 'file1.jsonl', 'output_folder/file1.jsonl')
    client_mock.download_file.assert_any_call(
        'bucket', 'file2.jsonl', 'output_folder/file2.jsonl')
    assert files == ['output_folder/file1.jsonl', 'output_folder/file2.jsonl']


@patch('boto3.Session')
def test_s3_download_fails_if_objects_are_not_found(mock_session):
    s3_mock = Mock()
    client_mock = Mock()
    mock_session.return_value = s3_mock
    s3_mock.client.return_value = client_mock
    client_mock.list_objects_v2.return_value = {}

    s3 = S3('aws_profile', 'bucket', 'output_folder')

    try:
        s3.download_s3_files('genes')
    except ValueError as e:
        assert str(e) == 'Folder genes does not exist or cannot be accessed.'
