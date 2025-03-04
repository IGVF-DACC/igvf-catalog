from typing import Union
import lmdb


class Container:
    def __init__(self) -> None:
        pass

    def contains(self, key: Union[str, int]) -> bool:
        pass

    def add(self, key: Union[str, int]) -> None:
        pass


class LMDBContainer(Container):
    def __init__(self) -> None:
        super().__init__()
        self.container = lmdb.open(self.path, map_size=1099511627776)


class InMemoryContainer(Container):
    def __init__(self) -> None:
        super().__init__()
        self.container = set()

    def contains(self, key: Union[str, int]) -> bool:
        return key in self.container

    def add(self, key: Union[str, int]) -> None:
        self.container.add(key)


def get_container(in_memory: bool = True) -> Container:
    if in_memory:
        return InMemoryContainer()
    else:
        return LMDBContainer()
