import tempfile
import pickle

import lmdb

FIFTY_GB_IN_BYTES = 50 * 1024 * 1024 * 1024


class Container:
    def __init__(self) -> None:
        pass

    def contains(self, key: bytes) -> bool:
        pass

    def add(self, key: bytes) -> None:
        pass


class LMDBContainer(Container):
    def __init__(self) -> None:
        super().__init__()
        self.__tempdir = tempfile.TemporaryDirectory()
        self.path = self.__tempdir.name
        self.lmdb = lmdb.open(self.path, map_size=FIFTY_GB_IN_BYTES)

    def contains(self, key: bytes) -> bool:
        with self.lmdb.begin(write=False) as txn:
            return txn.get(key) is not None

    def set(self, key: bytes, rsids) -> None:
        with self.lmdb.begin(write=True) as txn:
            txn.put(key, pickle.dumps(rsids))

    def get(self, key: bytes) -> bytes:
        with self.lmdb.begin(write=False) as txn:
            if txn.get(key):
                return pickle.loads(txn.get(key))
            return None


class InMemoryContainer(Container):
    def __init__(self) -> None:
        super().__init__()
        self.container = {}

    def contains(self, key: bytes) -> bool:
        return key in self.container

    def set(self, key: bytes, rsid) -> None:
        self.container[key] = rsid

    def get(self, key: bytes) -> bytes:
        return self.container.get(key)


def get_container(in_memory: bool = True) -> Container:
    if in_memory:
        return InMemoryContainer()
    else:
        return LMDBContainer()
