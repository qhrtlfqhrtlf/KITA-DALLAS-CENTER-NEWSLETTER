import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


@pytest.fixture(autouse=True)
def reset_client_singleton():
    """Reset the _client singleton before each test to allow proper mocking."""
    from lib import ai_processor
    ai_processor._client = None
    yield
    ai_processor._client = None
