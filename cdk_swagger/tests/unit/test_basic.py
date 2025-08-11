import pytest
from aws_cdk import App
from infrastructure.build import build


def test_cdk_app_can_synth():
    """Test that the CDK app can be synthesized without errors."""
    app = App()
    app.node.set_context('branch', 'test-branch')
    app.node.set_context('config-name', 'demo')
    build(app)

    # If we get here without errors, the test passes
    assert app is not None


def test_basic_imports():
    """Test that basic modules can be imported."""
    try:
        from infrastructure.config import Config
        from infrastructure.constructs.frontend import Frontend
        assert True
    except ImportError as e:
        pytest.fail(f'Failed to import required modules: {e}')
