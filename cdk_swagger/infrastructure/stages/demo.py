from aws_cdk import Stage

from constructs import Construct

from infrastructure.constructs.existing import catalog_dev

from infrastructure.config import Config

from infrastructure.stacks.frontend import FrontendStack

from infrastructure.tags import add_tags_to_stack

from typing import Any


class DemoDeployStage(Stage):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            *,
            config: Config,
            **kwargs: Any
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.frontend_stack = FrontendStack(
            self,
            'FrontendStack',
            config=config,
            existing_resources_class=catalog_dev.Resources,
            env=catalog_dev.US_WEST_2,
        )
        add_tags_to_stack(self.frontend_stack, config)
