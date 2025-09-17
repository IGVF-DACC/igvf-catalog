from aws_cdk import Stack

from constructs import Construct

from infrastructure.config import Config

from infrastructure.constructs.frontend import Frontend
from infrastructure.constructs.frontend import FrontendProps

from infrastructure.constructs.existing.types import ExistingResourcesClass

from typing import Any


class FrontendStack(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            *,
            config: Config,
            existing_resources_class: ExistingResourcesClass,
            **kwargs: Any
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.existing_resources = existing_resources_class(
            self,
            'ExistingResources',
        )
        self.frontend = Frontend(
            self,
            'Frontend',
            props=FrontendProps(
                **config.frontend,
                config=config,
                existing_resources=self.existing_resources,
            )
        )
