from aws_cdk.aws_ec2 import InstanceClass, InstanceSize

config = {
    'region': 'us-west-2',
    'account': '109189702753',  # igvf-dev
    'vpc_id': 'vpc-0a5f4ff3233b1b79b',
    'instance_class': InstanceClass.R5,
    'instance_size': InstanceSize.XLARGE,
    'ami-id': 'ami-0b49ebef4546aabd7',
    'jwt_secret_arn': 'arn:aws:secretsmanager:us-west-2:109189702753:secret:arango_jwt-s0Gr1V',
    'arango_initial_root_password_arn': 'arn:aws:secretsmanager:us-west-2:109189702753:secret:arangodb_initial_root_password-TUlC7j',
    'cluster_size': 3,
    'root_volume_size_gb': 100,
    'cluster_id': 'testing-arango-cluster'
}
