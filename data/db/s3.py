import boto3
import os


class S3:
    def __init__(self, aws_profile, bucket, output_folder):
        if self.is_ec2_instance():
            self.session = boto3.Session()
        else:
            self.session = boto3.Session(profile_name=aws_profile)
        self.s3 = self.session.client('s3')
        self.bucket = bucket
        self.output_folder = output_folder

    def download_s3_files(self, collection):
        # create output folder if it doesn't exist
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

        prefix = collection + '/'

        paginator = self.s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=self.bucket, Prefix=prefix)

        files = []
        for page in page_iterator:
            if 'Contents' not in page:
                raise ValueError('Folder ' + collection +
                                 ' does not exist or cannot be accessed.')

            for obj in page['Contents']:
                if obj['Key'] == prefix:
                    continue

                print('Downloading s3://' + self.bucket +
                      '/' + obj['Key'] + ' ...')
                output_filepath = self.output_folder + \
                    '/' + obj['Key'].split('/')[-1]
                self.s3.download_file(self.bucket, obj['Key'], output_filepath)
                files.append(output_filepath)

        return files

    def is_ec2_instance(self):
        datasource_file = '/var/lib/cloud/instance/datasource'
        try:
            with open(datasource_file) as f:
                line = f.readlines()
                if 'DataSourceEc2Local' in line[0]:
                    return True
        except FileNotFoundError:
            return False
        return False
