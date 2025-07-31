from constructs import Construct
from aws_cdk.aws_ec2 import Vpc

from shared_infrastructure.igvf_dev.connection import CodeStarConnection
from shared_infrastructure.igvf_dev.environment import US_WEST_2 as US_WEST_2
from shared_infrastructure.igvf_dev.domain import DemoDomain
from shared_infrastructure.igvf_dev.secret import DockerHubCredentials
from shared_infrastructure.igvf_dev.notification import Notification
from shared_infrastructure.igvf_dev.bus import Bus


from typing import Any


class Resources(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.network = Network(
            self,
            'DemoNetwork',
        )
        self.domain = DemoDomain(
            self,
            'DemoDomain',
        )
        self.code_star_connection = CodeStarConnection(
            self,
            'CodeStarConnection',
        )
        self.notification = Notification(
            self,
            'Notification',
        )
        self.bus = Bus(
            self,
            'Bus',
        )
        self.docker_hub_credentials = DockerHubCredentials(
            self,
            'DockerHubCredentials',
        )


class Network(Construct):

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.vpc = Vpc.from_lookup(
            self,
            'Vpc',
            vpc_id='vpc-0a5f4ff3233b1b79b'
        )
