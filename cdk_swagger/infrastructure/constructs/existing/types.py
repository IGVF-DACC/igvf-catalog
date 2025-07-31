from infrastructure.constructs.existing.catalog_dev import Resources as CatalogDevResources
from infrastructure.constructs.existing.catalog_prod import Resources as CatalogProdResources

from typing import Union

from typing import Type


ExistingResources = Union[
    CatalogDevResources,
    CatalogProdResources,
]

ExistingResourcesClass = Union[
    Type[CatalogDevResources],
    Type[CatalogProdResources],
]
