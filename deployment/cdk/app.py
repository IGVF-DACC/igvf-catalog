from aws_cdk import App
from aws_cdk import Environment

from arango_cluster.config import config
from arango_cluster.stacks.arango_cluster import ArangoClusterStackProps
from arango_cluster.stacks.arango_cluster import ArangoClusterStack

app = App()

ENV = Environment(account=config['account'], region=config['region'])

arango_cluster_props = ArangoClusterStackProps(
    ami_id=config['ami-id'],
    instance_class=config['instance_class'],
    instance_size=config['instance_size'],
    vpc_id=config['vpc_id'],
    cluster_size=config['cluster_size'],
    cluster_id=config['cluster_id'],
    root_volume_size_gb=config['root_volume_size_gb'],
    jwt_secret_arn=config['jwt_secret_arn'],
    arango_initial_root_password_arn=config['arango_initial_root_password_arn'],
    source_data_bucket_name=config['source_data_bucket_name']
)

stack_name = f'ArangoClusterStack-testing'
arango_cluster_stack = ArangoClusterStack(
    app, stack_name, props=arango_cluster_props, env=ENV)
arango_cluster_stack.add_stack_tag(
    'arango-cluster-id', config['cluster_id'])

app.synth()
