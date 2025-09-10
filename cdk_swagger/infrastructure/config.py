from aws_cdk import Environment

from dataclasses import dataclass
from dataclasses import field

from infrastructure.constructs.existing import catalog_dev
from infrastructure.constructs.existing import catalog_prod

from infrastructure.constructs.existing.types import ExistingResourcesClass


from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple


config: Dict[str, Any] = {
    'pipeline': {
        'demo': {
            'pipeline': 'DemoDeploymentPipelineStack',
            'existing_resources_class': catalog_dev.Resources,
            'account_and_region': catalog_dev.US_WEST_2,
            'tags': [
                ('time-to-live-hours', '72'),
                ('turn-off-on-friday-night', 'yes'),
            ],
        },
        'dev': {
            'pipeline': 'DevDeploymentPipelineStack',
            'existing_resources_class': catalog_dev.Resources,
            'account_and_region': catalog_dev.US_WEST_2,
            'tags': [
            ],
        },
        'production': {
            'pipeline': 'ProductionDeploymentPipelineStack',
            'existing_resources_class': catalog_prod.Resources,
            'account_and_region': catalog_prod.US_WEST_2,
            'tags': [
            ],
        },
    },
    'environment': {
        'demo': {
            'frontend': {
                'cpu': 1024,
                'memory_limit_mib': 2048,
                'desired_count': 1,
                'max_capacity': 4,
            },
            'backend_url': 'https://db-dev.catalog.igvf.org/',
            'catalog_llm_query_service_url': 'https://catalog-llm-dev.demo.igvf.org/query',
            'tags': [
                ('time-to-live-hours', '72'),
                ('turn-off-on-friday-night', 'yes'),
            ],
            'open_api_config_type': 'development',
        },
        'dev': {
            'frontend': {
                'cpu': 1024,
                'memory_limit_mib': 2048,
                'desired_count': 1,
                'max_capacity': 4,
            },
            'backend_url': 'https://db-dev.catalog.igvf.org/',
            'catalog_llm_query_service_url': 'https://catalog-llm-dev.demo.igvf.org/query',
            'tags': [
            ],
            'open_api_config_type': 'development',
        },
        'production': {
            'frontend': {
                'cpu': 1024,
                'memory_limit_mib': 2048,
                'desired_count': 1,
                'max_capacity': 4,
            },
            'backend_url': 'https://db.catalog.igvf.org/',
            'catalog_llm_query_service_url': 'https://llm.catalogkg.igvf.org/query',
            'tags': [
            ],
            'url_prefix': 'api',
            'open_api_config_type': 'production',
        },
    }
}


@dataclass
class Common:
    organization_name: str = 'igvf-dacc'
    project_name: str = 'igvf-catalog-api'
    default_region: str = 'us-west-2'
    aws_cdk_version: str = '2.1022.0'


@dataclass
class Config:
    name: str
    branch: str
    backend_url: str
    catalog_llm_query_service_url: str
    open_api_config_type: str
    frontend: Dict[str, Any]
    tags: List[Tuple[str, str]]
    url_prefix: Optional[str] = None
    use_subdomain: bool = True
    common: Common = field(
        default_factory=Common
    )


@dataclass
class PipelineConfig:
    name: str
    branch: str
    pipeline: str
    existing_resources_class: ExistingResourcesClass
    account_and_region: Environment
    tags: List[Tuple[str, str]]
    common: Common = field(
        default_factory=Common
    )


def build_config_from_name(name: str, **kwargs: Any) -> Config:
    return Config(
        **{
            **config['environment'][name],
            **kwargs,
            **{'name': name},
        }
    )


def build_pipeline_config_from_name(name: str, **kwargs: Any) -> PipelineConfig:
    return PipelineConfig(
        **{
            **config['pipeline'][name],
            **kwargs,
            **{'name': name},
        }
    )


def get_config_name_from_branch(branch: str) -> str:
    if branch == 'dev':
        return 'dev'
    return 'demo'


def get_pipeline_config_name_from_branch(branch: str) -> str:
    if branch == 'dev':
        return 'dev'
    if branch == 'main':
        return 'production'
    return 'demo'
