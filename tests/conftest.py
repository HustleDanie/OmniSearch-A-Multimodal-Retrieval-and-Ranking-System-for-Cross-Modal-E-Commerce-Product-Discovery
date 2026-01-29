"""
Pytest configuration file for mocking external dependencies.
"""
import sys
from unittest.mock import MagicMock

# Mock external dependencies before anything else imports them
sys.modules['pymongo'] = MagicMock()
sys.modules['pymongo.errors'] = MagicMock()
sys.modules['pymongo.collection'] = MagicMock()
sys.modules['pymongo.database'] = MagicMock()
sys.modules['pymongo.results'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['clip'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['weaviate'] = MagicMock()
sys.modules['weaviate.classes'] = MagicMock()
sys.modules['weaviate.classes.config'] = MagicMock()
sys.modules['weaviate.classes.query'] = MagicMock()
