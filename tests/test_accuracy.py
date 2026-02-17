
import unittest
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.retriever import TelecomRetriever
from src.llm import TelecomLLM

class TestGoldenDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("🚀 Initializing RAG for Golden Dataset Test...")
        cls.retriever = TelecomRetriever(auto_init=True)
        # We'll use the LLM to grade itself (LLM-as-a-judge)
        cls.judge_llm = TelecomLLM() 
        
        with open("tests/golden_dataset.json", "r") as f:
            cls.dataset = json.load(f)

    def test_accuracy(self):
        """Run golden dataset and calculate pass rate."""
        passed = 0
        total = len(self.dataset)
        
        print("\n📊 Starting Golden Dataset Evaluation:")
        
        for item in self.dataset:
            question = item["question"]
            ground_truth = item["ground_truth"]
            category = item["category"]
            
            print(f"\nQ: {question} ({category})")
            
            # Get RAG answer
            response = self.retriever.query(question)
            answer = response.answer
            
            # Grade it using LLM
            grade_prompt = f"""
            Compare the generated answer to the ground truth.
            
            Question: {question}
            Ground Truth: {ground_truth}
            Generated Answer: {answer}
            
            Is the Generated Answer factually consistent with the Ground Truth? 
            It doesn't need to be identical, but must contain the key information.
            Reply strictly with 'YES' or 'NO'.
            """
            
            grade = self.judge_llm.simple_generate(grade_prompt).strip().upper()
            
            if "YES" in grade:
                print("✅ PASSED")
                passed += 1
            else:
                print(f"❌ FAILED. Got: {answer[:100]}...")
        
        accuracy = passed / total
        print(f"\n🏆 Accuracy: {accuracy:.0%}")
        
        # We expect at least 80% accuracy for a pass
        self.assertGreaterEqual(accuracy, 0.80, f"Accuracy {accuracy:.0%} is below 80% threshold")

if __name__ == '__main__':
    unittest.main()
