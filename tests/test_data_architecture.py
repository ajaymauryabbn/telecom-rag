
import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_loader import TelecomDataLoader

class TestDataIngestion(unittest.TestCase):
    def test_dynamic_chunking(self):
        loader = TelecomDataLoader()
        
        # Test performance chunking (500 tokens)
        text = "word " * 1000
        chunks = loader.chunk_text(text, "test_perf", "performance")
        # 500 tokens - overlap
        self.assertLessEqual(chunks[0].metadata["token_count"], 501)
        
        # Test maintenance chunking (300 tokens)
        chunks = loader.chunk_text(text, "test_maint", "maintenance")
        self.assertLessEqual(chunks[0].metadata["token_count"], 301)
        
    def test_pdf_loading(self):
        loader = TelecomDataLoader()
        # Just check if we can call the method without crashing
        # We expect 0 docs if directory is empty or path doesn't match, but valid execution
        try:
            docs = loader.load_all_raw_documents()
            print(f"Loaded {len(docs)} PDF chunks")
            # If we downloaded data, we should have > 0
            if any(Path("data/raw").glob("*/*.pdf")):
                 self.assertGreater(len(docs), 0, "Should load PDF documents if files exist")
        except Exception as e:
            self.fail(f"PDF loading failed: {e}")

if __name__ == '__main__':
    unittest.main()
