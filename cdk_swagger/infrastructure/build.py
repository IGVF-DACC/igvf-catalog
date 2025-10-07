from aws_cdk import App

from infrastructure.config import PipelineConfig
from infrastructure.config import build_pipeline_config_from_name
from infrastructure.config import get_pipeline_config_name_from_branch

from infrastructure.naming import prepend_project_name
from infrastructure.naming import prepend_branch_name

from infrastructure.tags import add_tags_to_stack

from infrastructure.stacks.pipeline import pipeline_stack_factory

from dataclasses import dataclass


@dataclass
class Args:
    branch: str
    config_name: str


def branch_name_is_too_long(branch_name: str) -> bool:
    return len(branch_name) > 44


def get_args(app: App) -> Args:
    branch = app.node.try_get_context('branch')
    if branch is None:
        raise ValueError('Must specify branch context: `-c branch=$BRANCH`')
    if branch_name_is_too_long(branch):
        raise ValueError(
            f'Branch length {len(branch)} exceeds the maximum branch length of 44 characters.')
    config_name = (
        app.node.try_get_context('config-name')
        or get_pipeline_config_name_from_branch(branch)
    )
    return Args(
        branch=branch,
        config_name=config_name
    )


def get_config(args: Args) -> PipelineConfig:
    return build_pipeline_config_from_name(
        args.config_name,
        branch=args.branch,
    )


def add_deploy_pipeline_stack_to_app(app: App, config: PipelineConfig) -> None:
    pipeline_class = pipeline_stack_factory(
        config.pipeline
    )
    pipeline = pipeline_class(
        app,
        prepend_project_name(
            prepend_branch_name(
                config.branch,
                pipeline_class.__name__,
            )
        ),
        existing_resources_class=config.existing_resources_class,
        config=config,
        env=config.account_and_region,
    )
    add_tags_to_stack(pipeline, config)


def build(app: App) -> None:
    args = get_args(app)
    config = get_config(args)
    add_deploy_pipeline_stack_to_app(app, config)
