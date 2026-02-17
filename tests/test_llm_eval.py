
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation import RAGEvaluator

class TestLLMEvaluation(unittest.TestCase):
    def setUp(self):
        self.evaluator = RAGEvaluator()
        # Mock LLM to avoid actual API calls during test
        self.evaluator.llm = MagicMock()
        
    def test_llm_faithfulness(self):
        # Mock LLM response
        self.evaluator.llm.simple_generate.return_value = "0.9"
        
        score = self.evaluator.calculate_llm_faithfulness("Answer", "Context")
        self.assertEqual(score, 0.9)
        
        # Verify prompt structure
        args, _ = self.evaluator.llm.simple_generate.call_args
        self.assertIn("Rate the faithfulness", args[0])

    def test_llm_relevancy(self):
        # Mock LLM response
        self.evaluator.llm.simple_generate.return_value = "0.8"
        
        score = self.evaluator.calculate_llm_relevancy("Question", "Answer")
        self.assertEqual(score, 0.8)
        
        # Verify prompt structure
        args, _ = self.evaluator.llm.simple_generate.call_args
        self.assertIn("Rate the relevancy", args[0])

    def test_evaluate_with_llm(self):
        # Mock LLM responses
        self.evaluator.calculate_llm_faithfulness = MagicMock(return_value=0.9)
        self.evaluator.calculate_llm_relevancy = MagicMock(return_value=0.8)
        
        result = self.evaluator.evaluate(
            question="Q", 
            answer="A", 
            context="C", 
            similarity_scores=[0.8, 0.7], 
            use_llm=True
        )
        
        self.assertEqual(result.faithfulness_score, 0.9)
        self.assertEqual(result.relevancy_score, 0.8)
        self.assertTrue(self.evaluator.calculate_llm_faithfulness.called)
        self.assertTrue(self.evaluator.calculate_llm_relevancy.called)

    def test_evaluate_without_llm(self):
        # Result should rely on heuristics (mocking those for isolation if needed, but integration test is fine)
        # Here we just check that LLM methods are NOT called
        self.evaluator.calculate_llm_faithfulness = MagicMock()
        self.evaluator.calculate_llm_relevancy = MagicMock()
        
        self.evaluator.evaluate(
            question="Q", 
            answer="A", 
            context="C", 
            similarity_scores=[0.8, 0.7], 
            use_llm=False
        )
        
        self.assertFalse(self.evaluator.calculate_llm_faithfulness.called)
        self.assertFalse(self.evaluator.calculate_llm_relevancy.called)

if __name__ == '__main__':
    unittest.main()
