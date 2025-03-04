import pytest
from adapters.deduplication import get_container, InMemoryContainer


def test_container_creation():
    container = get_container(in_memory=True)
    assert isinstance(container, InMemoryContainer)


def test_add_and_contains():
    container = InMemoryContainer()

    container.add('test_key')
    assert container.contains('test_key')

    container.add(42)
    assert container.contains(42)


def test_add_idempotent():
    container = InMemoryContainer()

    container.add('test_key')
    container.add('test_key')
    container.add('test_key')

    assert container.contains('test_key')

    container.add(42)
    container.add(42)
    assert container.contains(42)
