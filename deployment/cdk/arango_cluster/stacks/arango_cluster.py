from dataclasses import dataclass

from aws_cdk import Stack, Duration, Fn, InstanceClass, InstanceSize

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
    instance_class: InstanceClass
    instance_size: InstanceSize
    vpc_id: str


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
        self.instance_name = 'testing-arango-cluster'
        self.user_data = self._create_ec2_user_data()
        self.vpc = ec2.Vpc.from_lookup(
            self,
            'CatalogDemoVpc',
            vpc_id=self.props.vpc_id
        )
        self.__security_group = None
        self.__role = None
        self.ec2_instance = ec2.Instance(
            self,
            f'ArangoInstance-{self.instance_name}',
            instance_type=ec2.InstanceType.of(
                self.props.instance_class, self.props.instance_size),
            machine_image=ec2.MachineImage.generic_linux(
                {'us-west-2': self.props.ami_id}
            ),
            security_group=self.security_group,
            vpc=self.vpc,
            role=self.role,
            user_data=self.user_data,
            ssm_session_permissions=True
        )
        self._create_cloudwatch_alarms()

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
            'ClickhouseInstanceRole',
            assumed_by=iam.ServicePrincipal('ec2.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    'CloudWatchAgentServerPolicy')
            ]
        )
        return role

    def _define_security_group(self) -> ec2.SecurityGroup:
        security_group = ec2.SecurityGroup(
            self,
            'ArangoInstanceSG',
            vpc=self.vpc,
            allow_all_outbound=True  # Allow all outbound traffic
        )
        # Allow inbound custom TCP traffic to port range 8529-8531 from within this security group
        security_group.add_ingress_rule(
            peer=security_group,  # Self-referencing rule
            connection=ec2.Port.tcp_range(8529, 8531),
            description='Allow ArangoDB cluster communication within the security group on ports 8529-8531'
        )
        return security_group
