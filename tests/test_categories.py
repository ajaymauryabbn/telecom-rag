
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_loader import TelecomDataLoader
from src.vector_store import TelecomVectorStore

class TestDataCategories(unittest.TestCase):
    def test_category_normalization(self):
        loader = TelecomDataLoader()
        
        # Test standard mappings
        self.assertEqual(loader.normalize_category("3gpp_standards"), "standards")
        self.assertEqual(loader.normalize_category("5g_protocols"), "standards")
        self.assertEqual(loader.normalize_category("troubleshooting"), "network_operations")
        self.assertEqual(loader.normalize_category("5g_radio"), "network_operations")
        self.assertEqual(loader.normalize_category("performance"), "performance")
        self.assertEqual(loader.normalize_category("KPIs"), "performance")
        self.assertEqual(loader.normalize_category("network_architecture"), "architecture")
        self.assertEqual(loader.normalize_category("5g_fundamentals"), "architecture")
        self.assertEqual(loader.normalize_category("unknown_stuff"), "general")
        
    def test_builtin_kb_categories(self):
        loader = TelecomDataLoader()
        docs = loader.load_builtin_knowledge_base()
        
        valid_cats = {"standards", "network_operations", "performance", "architecture", "general"}
        
        for doc in docs:
            self.assertIn(doc.metadata["category"], valid_cats, 
                          f"Invalid category '{doc.metadata['category']}' in {doc.metadata['source']}")

if __name__ == '__main__':
    unittest.main()
