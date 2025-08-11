from aws_cdk import Stack

from constructs import Construct

from infrastructure.config import PipelineConfig

from infrastructure.constructs.pipeline import DemoDeploymentPipeline
from infrastructure.constructs.pipeline import DemoDeploymentPipelineProps
from infrastructure.constructs.pipeline import DevDeploymentPipeline
from infrastructure.constructs.pipeline import DevDeploymentPipelineProps
from infrastructure.constructs.pipeline import ProductionDeploymentPipeline
from infrastructure.constructs.pipeline import ProductionDeploymentPipelineProps

from infrastructure.constructs.existing.types import ExistingResourcesClass

from typing import Any
from typing import Dict
from typing import Union
from typing import List
from typing import Type

GITHUB_REPO = 'IGVF-DACC/igvf-catalog'


class DemoDeploymentPipelineStack(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            *,
            existing_resources_class: ExistingResourcesClass,
            config: PipelineConfig,
            **kwargs: Any
    ) -> None:
        super().__init__(scope, construct_id,  **kwargs)
        self.existing_resources = existing_resources_class(
            self,
            'ExistingResources',
        )
        self.pipeline = DemoDeploymentPipeline(
            self,
            'DemoDeploymentPipeline',
            props=DemoDeploymentPipelineProps(
                github_repo=GITHUB_REPO,
                existing_resources=self.existing_resources,
                config=config,
            )
        )


class DevDeploymentPipelineStack(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            *,
            existing_resources_class: ExistingResourcesClass,
            config: PipelineConfig,
            **kwargs: Any
    ) -> None:
        super().__init__(scope, construct_id,  **kwargs)
        self.existing_resources = existing_resources_class(
            self,
            'ExistingResources',
        )
        self.pipeline = DevDeploymentPipeline(
            self,
            'DevDeploymentPipeline',
            props=DevDeploymentPipelineProps(
                github_repo=GITHUB_REPO,
                existing_resources=self.existing_resources,
                config=config,
            )
        )


class ProductionDeploymentPipelineStack(Stack):

    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            *,
            existing_resources_class: ExistingResourcesClass,
            config: PipelineConfig,
            **kwargs: Any
    ) -> None:
        super().__init__(scope, construct_id,  **kwargs)
        self.existing_resources = existing_resources_class(
            self,
            'ExistingResources',
        )
        self.pipeline = ProductionDeploymentPipeline(
            self,
            'ProductionDeploymentPipeline',
            props=ProductionDeploymentPipelineProps(
                github_repo=GITHUB_REPO,
                existing_resources=self.existing_resources,
                config=config,
            )
        )


PipelineStackClass = Union[
    Type[DemoDeploymentPipelineStack],
    Type[DevDeploymentPipelineStack],
    Type[ProductionDeploymentPipelineStack],
]


pipeline_stacks: List[PipelineStackClass] = [
    DemoDeploymentPipelineStack,
    DevDeploymentPipelineStack,
    ProductionDeploymentPipelineStack,
]


name_to_pipeline_stack_map: Dict[str, PipelineStackClass] = {
    pipeline_stack.__name__: pipeline_stack
    for pipeline_stack in pipeline_stacks
}


def pipeline_stack_factory(name: str) -> PipelineStackClass:
    return name_to_pipeline_stack_map[name]
