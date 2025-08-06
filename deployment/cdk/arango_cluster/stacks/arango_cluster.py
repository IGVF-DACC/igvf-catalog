from dataclasses import dataclass

from aws_cdk import Stack, Duration, Fn

from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk.aws_sns import Topic
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk.aws_cloudwatch_actions import SnsAction
from aws_cdk.aws_ec2 import UserData

from constructs import Construct

from typing import Any, Optional


@dataclass
class ArangoClusterStackProps:
    ami_id: str
    instance_class: ec2.InstanceClass
    instance_size: ec2.InstanceSize
    vpc_id: str
    cluster_size: int
    cluster_id: str
    root_volume_size_gb: int
    data_volume_size_gb: int
    only_create_cluster: bool
    jwt_secret_arn: str
    arango_initial_root_password_arn: str
    source_data_bucket_name: Optional[str] = None


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
                block_devices=self._define_block_devices()
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

    def _define_block_devices(self) -> list[ec2.BlockDevice]:
        if self.props.only_create_cluster:
            return [
                ec2.BlockDevice(
                    device_name='/dev/sda1',  # Root device for Ubuntu 24.04
                    volume=ec2.BlockDeviceVolume.ebs(
                        self.props.root_volume_size_gb
                    )
                )
            ]
        else:
            return [
                ec2.BlockDevice(
                    device_name='/dev/sda1',  # Root device for Ubuntu 24.04
                    volume=ec2.BlockDeviceVolume.ebs(
                        self.props.root_volume_size_gb
                    )
                ),

                ec2.BlockDevice(
                    device_name='/dev/sdf',  # Data volume
                    volume=ec2.BlockDeviceVolume.ebs(
                        self.props.data_volume_size_gb,  # 100GB data volume
                        volume_type=ec2.EbsDeviceVolumeType.GP3
                    )
                )
            ]

    def _create_ec2_user_data(self) -> UserData:
        user_data = ec2.UserData.for_linux()
        data_volume_setup_commands = [
            'sleep 10',
            'echo "Setting up data volume..."',
            """ROOT_DEVICE=$(lsblk -lo NAME,MOUNTPOINT | grep nvme | grep "/" | head -1 | awk '{print $1}' | sed 's/p[0-9]*$//')""",
            """DATA_DEVICE=$(lsblk -o NAME,MOUNTPOINT | grep nvme | grep -v "/" | grep -v "$ROOT_DEVICE" | head -1 | awk '{print $1}')""",
            'echo "ROOT_DEVICE: $ROOT_DEVICE"',
            'echo "DATA_DEVICE: $DATA_DEVICE"',
            'sudo mkfs -t ext4 /dev/$DATA_DEVICE',
            'sudo mkdir -p /data',
            'sudo mount /dev/$DATA_DEVICE /data',
            'echo "/dev/$DATA_DEVICE /data ext4 defaults,noatime 0 2" | sudo tee -a /etc/fstab',
            'sudo chown ubuntu:ubuntu /data',
            'sudo chmod 755 /data',
            'sudo -u ubuntu mkdir -p /data/arangodb',
            'sudo chown -R ubuntu:ubuntu /data/arangodb',
        ]
        service_definition = ['cat > /etc/systemd/system/arangodb.service << EOF',
                              """[Unit]
            Description=ArangoDB Cluster
            After=network.target

            [Service]
            ExecStart=arangodb --starter.mode cluster --starter.join ${JOIN_STRING} --auth.jwt-secret /data/arangodb/jwtSecret --starter.data-dir /data/arangodb
            Restart=always
            RestartSec=10
            User=ubuntu
            Group=ubuntu

            [Install]
            WantedBy=multi-user.target
            """,
                              'EOF'
                              ]

        discover_peers_commands = [
            'PEER_IPS=()',
            'for ((i=1; i<=20; i++)); do',
            f'PEER_IPS=($(aws ec2 describe-instances --region us-west-2 --filters "Name=tag:arango-cluster-id,Values={self.cluster_id}" "Name=instance-state-name,Values=running" --query "Reservations[].Instances[].PrivateIpAddress" --output text))',
            'if [ ${#PEER_IPS[@]} -eq ' +
            str(self.props.cluster_size) + ' ]; then',
            f'echo "Found all {self.props.cluster_size} instances"',
            'break',
            'else',
            'echo "Found ${#PEER_IPS[@]} nodes, waiting to find ' + str(
                self.props.cluster_size) + ' nodes. Waiting for 10 seconds."',
            'sleep 10',
            'fi',
            'if [ "$i" -eq 20 ]; then',
            f'echo "Failed to find all {self.props.cluster_size} instances"',
            'exit 1',
            'fi',
            'done',
            'join_by() { local d=${1-} f=${2-}; if shift 2; then printf %s "$f" "${@/#/$d}"; fi; }',
            'JOIN_LIST=()',
            'for ip in "${PEER_IPS[@]}"; do',
            'JOIN_LIST+=("${ip}")',
            'done',
            'JOIN_STRING=$(join_by "," "${JOIN_LIST[@]}")',
            'echo "IPs: ${JOIN_STRING}"',
        ]
        get_jwt_secret_commands = [
            f'echo getting secret from {self.props.jwt_secret_arn}',
            f'JWT_SECRET=$(aws secretsmanager get-secret-value --region us-west-2 --secret-id {self.props.jwt_secret_arn} --query SecretString --output text | jq .arangocluster_json_web_token |' + """sed 's/"//g')""",
            'echo "${JWT_SECRET}" > /data/arangodb/jwtSecret',
        ]
        service_start_commands = [
            'echo "service defined, reloading and starting"',
            'sudo systemctl daemon-reload',
            'sudo systemctl enable arangodb.service',
            'sudo systemctl start arangodb.service',
            'echo "waiting for arangodb to start"',
            'sleep 10',
        ]
        root_password_change_commands = [
            f'echo getting secret from {self.props.arango_initial_root_password_arn}',
            f'ARANGO_INITIAL_ROOT_PASSWORD=$(aws secretsmanager get-secret-value --region us-west-2 --secret-id {self.props.arango_initial_root_password_arn} --query SecretString --output text | jq .arangopassword | sed \'s/"//g\')',
            'echo "require(\\"@arangodb/users\\").update(\\"root\\", \\"${ARANGO_INITIAL_ROOT_PASSWORD}\\");" > /home/ubuntu/change_password.js',
            'arangosh --server.endpoint localhost:8529 --server.password "" --javascript.execute /home/ubuntu/change_password.js',
            'rm /home/ubuntu/change_password.js'
        ]
        if not self.props.only_create_cluster:
            user_data.add_commands(
                *data_volume_setup_commands,
                *discover_peers_commands,
                *get_jwt_secret_commands,
                *service_definition,
                *service_start_commands,
                *root_password_change_commands
            )
        else:
            user_data.add_commands(
                *discover_peers_commands,
                *service_definition,
            )
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
                'ec2:DescribeInstances'
            ],
            resources=['*']
        ))
        # Add separate policy statement for SecretsManager with restricted access
        role.add_to_policy(iam.PolicyStatement(
            actions=[
                'secretsmanager:GetSecretValue'
            ],
            resources=[self.props.jwt_secret_arn,
                       self.props.arango_initial_root_password_arn]
        ))

        # Add S3 read access for source data bucket if specified
        if self.props.source_data_bucket_name:
            role.add_to_policy(iam.PolicyStatement(
                actions=[
                    's3:GetObject',
                    's3:ListBucket'
                ],
                resources=[
                    f'arn:aws:s3:::{self.props.source_data_bucket_name}',
                    f'arn:aws:s3:::{self.props.source_data_bucket_name}/*'
                ]
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
