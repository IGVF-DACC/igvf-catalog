from aws_cdk import Stack
from aws_cdk import Tags

from infrastructure.config import Config
from infrastructure.config import PipelineConfig

from typing import Union


ConfigWithTags = Union[
    Config,
    PipelineConfig,
]


# Cloudformation bug.
# Updating NotificationRule tags causes Internal Failure.
EXCLUDE_RESOURCE_TYPES = [
    'AWS::CodeStarNotifications::NotificationRule'
]


def add_environment_tag(stack: Stack, config: ConfigWithTags) -> None:  # type: ignore
    Tags.of(stack).add(
        'environment',
        config.name,
        exclude_resource_types=EXCLUDE_RESOURCE_TYPES,
    )


def add_project_tag(stack: Stack, config: ConfigWithTags) -> None:  # type: ignore
    Tags.of(stack).add(
        'project',
        config.common.project_name,
        exclude_resource_types=EXCLUDE_RESOURCE_TYPES,
    )


def add_branch_tag(stack: Stack, config: ConfigWithTags) -> None:  # type: ignore
    Tags.of(stack).add(
        'branch',
        config.branch,
        exclude_resource_types=EXCLUDE_RESOURCE_TYPES,
    )


def add_config_tags(stack: Stack, config: ConfigWithTags) -> None:  # type: ignore
    for (key, value) in config.tags:
        Tags.of(stack).add(
            key,
            value,
            exclude_resource_types=EXCLUDE_RESOURCE_TYPES,
        )


def add_tags_to_stack(stack: Stack, config: ConfigWithTags) -> None:  # type: ignore
    add_environment_tag(stack, config)
    add_project_tag(stack, config)
    add_branch_tag(stack, config)
    add_config_tags(stack, config)
