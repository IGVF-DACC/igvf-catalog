from aws_cdk.aws_ec2 import InstanceClass, InstanceSize

config = {
    'region': 'us-west-2',
    'account': '109189702753',  # igvf-dev
    'vpc_id': 'vpc-0a5f4ff3233b1b79b',
    'instance_class': InstanceClass.R5,
    'instance_size': InstanceSize.XLARGE,
    'ami-id': 'ami-03e9a24f577180277',
    'cluster_size': 3,
    'root_volume_size_gb': 100
}
