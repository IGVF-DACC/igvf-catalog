from dataclasses import dataclass

from aws_cdk import Stack, Duration, Fn

from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk.aws_sns import Topic
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk.aws_cloudwatch_actions import SnsAction
from aws_cdk.aws_ec2 import UserData

from constructs import Construct

from typing import Any


@dataclass
class ArangoClusterStackProps:
    ami_id: str
    instance_class: ec2.InstanceClass
    instance_size: ec2.InstanceSize
    vpc_id: str
    cluster_size: int
    cluster_id: str
    root_volume_size_gb: int = 20  # Default to 20GB if not specified


class ArangoClusterStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        props: ArangoClusterStackProps,
        **kwargs: Any
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.props = props
        self.cluster_id = self.props.cluster_id
        self.user_data = self._create_ec2_user_data()
        self.vpc = ec2.Vpc.from_lookup(
            self,
            'CatalogDemoVpc',
            vpc_id=self.props.vpc_id
        )
        self.__security_group = None
        self.__role = None
        self.cluster_size = self.props.cluster_size
        for i in range(self.cluster_size):
            ec2.Instance(
                self,
                f'ArangoInstance-{self.cluster_id}-{i}',
                instance_type=ec2.InstanceType.of(
                    self.props.instance_class, self.props.instance_size),
                machine_image=ec2.MachineImage.generic_linux(
                    {'us-west-2': self.props.ami_id}
                ),
                security_group=self.security_group,
                vpc=self.vpc,
                role=self.role,
                user_data=self.user_data,
                ssm_session_permissions=True,
                block_devices=[
                    ec2.BlockDevice(
                        device_name='/dev/sda1',  # Root device for Ubuntu 24.04
                        volume=ec2.BlockDeviceVolume.ebs(
                            self.props.root_volume_size_gb
                        )
                    )
                ]
            )

    @property
    def role(self) -> iam.Role:
        if self.__role is None:
            self.__role = self._define_iam_role()
        return self.__role

    @property
    def security_group(self) -> ec2.SecurityGroup:
        if self.__security_group is None:
            self.__security_group = self._define_security_group()
        return self.__security_group

    def _create_ec2_user_data(self) -> UserData:
        user_data = ec2.UserData.for_linux()
        return user_data

    def _define_iam_role(self) -> iam.Role:
        role = iam.Role(
            self,
            'ArangoInstanceRole',
            assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    'CloudWatchAgentServerPolicy')
            ]
        )
        # Add inline policy for EC2 DescribeInstances and SecretsManager GetSecretValue
        role.add_to_policy(iam.PolicyStatement(
            actions=[
                'ec2:DescribeInstances',
                'secretsmanager:GetSecretValue'
            ],
            resources=['*']
        ))
        return role

    def _define_security_group(self) -> ec2.SecurityGroup:
        security_group = ec2.SecurityGroup(
            self,
            'ArangoInstanceSG',
            vpc=self.vpc,
            allow_all_outbound=True  # Allow all outbound traffic
        )
        # Allow inbound custom TCP traffic to port range 8528-8531 from within this security group
        security_group.add_ingress_rule(
            peer=security_group,  # Self-referencing rule
            connection=ec2.Port.tcp_range(8528, 8531),
            description='Allow ArangoDB cluster communication within the security group on ports 8529-8531'
        )
        # Allow SSH access from anywhere
        security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(22),
            description='Allow SSH access from anywhere'
        )
        return security_group
