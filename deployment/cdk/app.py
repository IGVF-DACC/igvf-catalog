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
    vpc_id=config['vpc_id']
)

stack_name = f'ArangoClusterStack-testing'
ArangoClusterStack(app, stack_name, props=arango_cluster_props, env=ENV)

app.synth()
