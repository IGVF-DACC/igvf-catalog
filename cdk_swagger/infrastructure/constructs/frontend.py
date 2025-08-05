from aws_cdk import Duration
from aws_cdk import Tags
from aws_cdk import aws_ecs as ecs
from constructs import Construct
from aws_cdk.aws_ecs import AwsLogDriverMode
from aws_cdk.aws_ecs import CfnService
from aws_cdk.aws_ecs import ContainerImage
from aws_cdk.aws_ecs import DeploymentCircuitBreaker
from aws_cdk.aws_ecs import Secret
from aws_cdk.aws_ecs import LogDriver
from aws_cdk.aws_ecs_patterns import ApplicationLoadBalancedFargateService
from aws_cdk.aws_ecs_patterns import ApplicationLoadBalancedTaskImageOptions
from aws_cdk.aws_iam import ManagedPolicy
from aws_cdk.aws_secretsmanager import Secret as SMSecret

from infrastructure.config import Config
from infrastructure.constructs.alarms.frontend import FrontendAlarmsProps
from infrastructure.constructs.alarms.frontend import FrontendAlarms
from infrastructure.constructs.existing.types import ExistingResources

from typing import Any
from typing import cast
from dataclasses import dataclass


def get_url_prefix(config: Config) -> str:
    if config.url_prefix is not None:
        return config.url_prefix
    return f'catalog-api-{config.branch}'


@dataclass
class FrontendProps:
    config: Config
    existing_resources: ExistingResources
    cpu: int
    memory_limit_mib: int
    desired_count: int
    max_capacity: int


class Frontend(Construct):

    props: FrontendProps
    application_image: ContainerImage
    nginx_image: ContainerImage
    domain_name: str
    fargate_service: ApplicationLoadBalancedFargateService

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            *,
            props: FrontendProps,
            **kwargs: Any
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.props = props
        self._define_docker_assets()
        self._define_domain_name()
        self._define_fargate_service()
        self._add_application_container_to_task()
        self._configure_health_check()
        self._add_tags_to_fargate_service()
        self._enable_exec_command()
        self._configure_task_scaling()
        self._add_alarms()

    def _define_docker_assets(self) -> None:
        self.application_image = ContainerImage.from_asset(
            '../',
            file='docker/api/Dockerfile.prod',
        )
        self.nginx_image = ContainerImage.from_asset(
            '../docker/nginx/'
        )

    def _define_domain_name(self) -> None:
        if self.props.config.use_subdomain:
            self.domain_name = (
                f'{get_url_prefix(self.props.config)}.{self.props.existing_resources.domain.name}'
            )
        else:
            self.domain_name = (
                f'{self.props.existing_resources.domain.name}'
            )

    def _define_fargate_service(self) -> None:
        container_name = 'nginx'
        self.fargate_service = ApplicationLoadBalancedFargateService(
            self,
            'Fargate',
            service_name='Catalog-API-Service',
            vpc=self.props.existing_resources.network.vpc,
            cpu=self.props.cpu,
            desired_count=self.props.desired_count,
            circuit_breaker=DeploymentCircuitBreaker(
                rollback=True,
            ),
            task_image_options=ApplicationLoadBalancedTaskImageOptions(
                container_name=container_name,
                image=self.nginx_image,
                log_driver=LogDriver.aws_logs(
                    stream_prefix=container_name,
                    mode=AwsLogDriverMode.NON_BLOCKING,
                ),
            ),
            memory_limit_mib=self.props.memory_limit_mib,
            public_load_balancer=True,
            assign_public_ip=True,
            certificate=self.props.existing_resources.domain.certificate,
            domain_zone=self.props.existing_resources.domain.zone,
            domain_name=self.domain_name,
            redirect_http=True,
        )

    def _add_application_container_to_task(self) -> None:
        container_name = 'swagger'
        # Get AWS Secrets Manager secret
        catalog_db_secret = SMSecret.from_secret_name_v2(
            self,
            'CatalogLLMSecret',
            secret_name='catalog-llm'
        )
        self.fargate_service.task_definition.add_container(
            'ApplicationContainer',
            container_name=container_name,
            image=self.application_image,
            port_mappings=[ecs.PortMapping(
                container_port=2023, host_port=2023)],
            environment={
                'NODE_ENV': 'production',
                'IGVF_CATALOG_PROTOCOL': 'https',
                'IGVF_CATALOG_HOSTNAME': self.domain_name,
                'IGVF_CATALOG_PORT': '2023',
                'IGVF_CATALOG_ARANGODB_URI': self.props.config.backend_url,
            },
            secrets={
                'IGVF_CATALOG_ARANGODB_USERNAME': Secret.from_secrets_manager(catalog_db_secret, 'CATALOG_USERNAME'),
                'IGVF_CATALOG_ARANGODB_PASSWORD': Secret.from_secrets_manager(catalog_db_secret, 'CATALOG_PASSWORD'),
            },
            logging=LogDriver.aws_logs(
                stream_prefix=container_name,
                mode=AwsLogDriverMode.NON_BLOCKING,
            ),
        )

    def _configure_health_check(self) -> None:
        self.fargate_service.target_group.configure_health_check(
            interval=Duration.seconds(60),
            healthy_http_codes='200',
            path='/api/health',
        )

    def _add_tags_to_fargate_service(self) -> None:
        Tags.of(self.fargate_service).add(
            'branch',
            self.props.config.branch
        )
        Tags.of(self.fargate_service).add(
            'backend_url',
            self.props.config.backend_url
        )

    def _enable_exec_command(self) -> None:
        self.fargate_service.task_definition.task_role.add_managed_policy(
            ManagedPolicy.from_aws_managed_policy_name(
                'AmazonSSMManagedInstanceCore'
            )
        )
        # Make mypy happy (default child is Optional[IConstruct]).
        cfn_service = cast(
            CfnService,
            self.fargate_service.service.node.default_child
        )
        cfn_service.enable_execute_command = True

    def _configure_task_scaling(self) -> None:
        scalable_task = self.fargate_service.service.auto_scale_task_count(
            max_capacity=self.props.max_capacity,
        )
        scalable_task.scale_on_request_count(
            'RequestCountScaling',
            requests_per_target=600,
            target_group=self.fargate_service.target_group,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60),
        )

    def _add_alarms(self) -> None:
        FrontendAlarms(
            self,
            'FrontendAlarms',
            props=FrontendAlarmsProps(
                config=self.props.config,
                existing_resources=self.props.existing_resources,
                fargate_service=self.fargate_service
            )
        )
