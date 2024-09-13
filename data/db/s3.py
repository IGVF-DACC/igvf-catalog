import boto3


class S3:
    def __init__(self, aws_profile, bucket, output_folder):
        self.session = boto3.Session(profile_name=aws_profile)
        self.s3 = self.session.client('s3')
        self.bucket = bucket
        self.output_folder = output_folder

    def download_s3_files(self, collection):
        prefix = collection + '/'

        objects = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=prefix)

        if 'Contents' not in objects:
            raise ValueError('Folder ' + collection +
                             ' does not exist or cannot be accessed.')

        files = []

        for object in objects['Contents']:
            if object['Key'] == prefix:
                continue

            print('Downloading s3://' + self.bucket +
                  '/' + object['Key'] + ' ...')

            output_filepath = self.output_folder + \
                '/' + object['Key'].split('/')[-1]
            self.s3.download_file(self.bucket, object['Key'], output_filepath)
            files.append(output_filepath)

        return files
