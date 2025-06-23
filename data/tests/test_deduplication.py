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
        container.set(b'test_key', 'rs123')
        assert container.contains(b'test_key')

        container.set(b'42', 'rs123')
        assert container.contains(b'42')


def test_add_idempotent():
    for container in [InMemoryContainer(), LMDBContainer()]:
        container.set(b'test_key', 'rs1235')
        container.set(b'test_key', 'rs1235')
        container.set(b'test_key', 'rs1235')
        assert container.contains(b'test_key')

        container.set(b'42', 'rs123')
        container.set(b'42', 'rs123')
        assert container.contains(b'42')


def test_lmdb_persistence():
    container = LMDBContainer()

    # Add some data
    container.set(b'key1', 'rs123')
    container.set(b'key2', 'rs456')

    # Verify data exists
    assert container.contains(b'key1')
    assert container.contains(b'key2')
    assert not container.contains(b'nonexistent')
