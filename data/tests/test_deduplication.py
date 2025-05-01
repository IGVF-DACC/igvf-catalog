import pytest
from adapters.deduplication import get_container, InMemoryContainer, LMDBContainer


def test_container_creation():
    # Test in-memory container
    container = get_container(in_memory=True)
    assert isinstance(container, InMemoryContainer)

    # Test LMDB container
    container = get_container(in_memory=False)
    assert isinstance(container, LMDBContainer)


def test_add_and_contains():
    for container in [InMemoryContainer(), LMDBContainer()]:
        container.add(b'test_key')
        assert container.contains(b'test_key')

        container.add(b'42')
        assert container.contains(b'42')


def test_add_idempotent():
    for container in [InMemoryContainer(), LMDBContainer()]:
        container.add(b'test_key')
        container.add(b'test_key')
        container.add(b'test_key')
        assert container.contains(b'test_key')

        container.add(b'42')
        container.add(b'42')
        assert container.contains(b'42')


def test_lmdb_persistence():
    container = LMDBContainer()

    # Add some data
    container.add(b'key1')
    container.add(b'key2')

    # Verify data exists
    assert container.contains(b'key1')
    assert container.contains(b'key2')
    assert not container.contains(b'nonexistent')
