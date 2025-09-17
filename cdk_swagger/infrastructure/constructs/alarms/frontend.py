from aws_cdk import Duration

from constructs import Construct

from infrastructure.config import Config

from aws_cdk.aws_cloudwatch import TreatMissingData

from aws_cdk.aws_cloudwatch_actions import SnsAction

from aws_cdk.aws_ecs_patterns import ApplicationLoadBalancedFargateService

from aws_cdk.aws_elasticloadbalancingv2 import HttpCodeTarget

from infrastructure.constructs.existing.types import ExistingResources

from dataclasses import dataclass

from typing import Any


CPU_ALARM_THRESHOLD_PERCENT = 85

MEMORY_ALARM_THRESHOLD_PERCENT = 80

LOAD_BALANCER_500_ERROR_THRESHOLD_COUNT = 10


@dataclass
class FrontendAlarmsProps:
    config: Config
    existing_resources: ExistingResources
    fargate_service: ApplicationLoadBalancedFargateService


class FrontendAlarms(Construct):

    props: FrontendAlarmsProps
    alarm_action: SnsAction

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            *,
            props: FrontendAlarmsProps,
            **kwargs: Any
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.props = props
        self._define_alarm_action()
        self._add_cpu_alarm()
        self._add_memory_alarm()
        self._add_load_balancer_500_error_response_alarm()
        self._add_unhealthy_host_alarm()

    def _define_alarm_action(self) -> None:
        # Cloudwatch action targeting SNS topic.
        self.alarm_action = SnsAction(
            self.props.existing_resources.notification.alarm_notification_topic
        )

    def _add_cpu_alarm(self) -> None:
        cpu_alarm = self.props.fargate_service.service.metric_cpu_utilization().create_alarm(
            self,
            'FargateServiceCPUAlarm',
            evaluation_periods=2,
            threshold=CPU_ALARM_THRESHOLD_PERCENT,
        )
        cpu_alarm.add_alarm_action(
            self.alarm_action
        )
        cpu_alarm.add_ok_action(
            self.alarm_action
        )

    def _add_memory_alarm(self) -> None:
        memory_alarm = self.props.fargate_service.service.metric_memory_utilization().create_alarm(
            self,
            'FargateServiceMemoryAlarm',
            evaluation_periods=1,
            threshold=MEMORY_ALARM_THRESHOLD_PERCENT,
        )
        memory_alarm.add_alarm_action(
            self.alarm_action
        )
        memory_alarm.add_ok_action(
            self.alarm_action
        )

    def _add_load_balancer_500_error_response_alarm(self) -> None:
        load_balancer_500_error_response_alarm = self.props.fargate_service.load_balancer.metric_http_code_target(
            code=HttpCodeTarget.TARGET_5XX_COUNT,
        ).create_alarm(
            self,
            'FargateServiceLoadBalancer500Alarm',
            evaluation_periods=1,
            threshold=LOAD_BALANCER_500_ERROR_THRESHOLD_COUNT,
            treat_missing_data=TreatMissingData.NOT_BREACHING,
        )
        load_balancer_500_error_response_alarm.add_alarm_action(
            self.alarm_action
        )
        load_balancer_500_error_response_alarm.add_ok_action(
            self.alarm_action
        )

    def _add_unhealthy_host_alarm(self) -> None:
        unhealthy_host_alarm = self.props.fargate_service.target_group.metric_unhealthy_host_count(
            statistic='max',
            period=Duration.minutes(1),
        ).create_alarm(
            self,
            'TargetGroupUnhealthyHostAlarm',
            evaluation_periods=1,
            threshold=1,
        )
        unhealthy_host_alarm.add_alarm_action(
            self.alarm_action
        )
        unhealthy_host_alarm.add_ok_action(
            self.alarm_action
        )
