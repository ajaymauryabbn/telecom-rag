"""Telecom RAG - Evaluation Module

Implements RAGAS-style evaluation metrics for hallucination detection:
- Faithfulness scoring (is answer grounded in context?)
- Answer relevancy (does answer address the question?)
- Abstention logic (refuse when confidence is low)
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .config import (
    LLM_PROVIDER,
    OPENAI_API_KEY,
    GOOGLE_API_KEY,
    OPENAI_MODEL,
    GEMINI_MODEL
)


@dataclass
class EvaluationResult:
    """Evaluation metrics for a RAG response."""
    faithfulness_score: float  # 0-1: How grounded is answer in context
    relevancy_score: float     # 0-1: How relevant is answer to question
    confidence_score: float    # 0-1: Combined confidence
    should_abstain: bool       # True if confidence too low
    abstention_reason: str     # Why abstaining (if applicable)
    claims: List[str]          # Extracted claims from answer
    supported_claims: int      # Number of claims supported by context
    total_claims: int          # Total claims in answer
    # Context quality metrics (per architecture doc Section 5.1)
    context_precision: float = 0.0  # Relevant chunks / total chunks (target: >0.70)
    context_recall: float = 0.0     # Covered claims / total claims (target: >0.85)
    
    # TLM Trust Metrics (Section 5.2)
    trust_score: float = 0.0        # Combined reliability metric
    consistency_score: float = 0.0  # Self-consistency agreement (0-1)


class RAGEvaluator:
    """
    Evaluates RAG responses for faithfulness and relevancy.
    Implements abstention logic for low-confidence answers.
    """
    
    # Thresholds tuned for telecom domain with quality built-in KB
    FAITHFULNESS_THRESHOLD = 0.8   # Flag for review if below
    ABSTENTION_THRESHOLD = 0.3     # Refuse only for very low confidence
    MIN_SIMILARITY_THRESHOLD = 0.2 # Allow lower similarity since domain-specific
    
    def __init__(self):
        self.llm_available = self._check_llm()
        self.llm = None
        if self.llm_available:
            try:
                from .llm import TelecomLLM
                self.llm = TelecomLLM()
            except Exception as e:
                print(f"⚠️ Failed to init LLM for eval: {e}")

    def _check_llm(self) -> bool:
        """Check if LLM is available for evaluation."""
        if LLM_PROVIDER == "openai" and OPENAI_API_KEY and OPENAI_API_KEY != "your_openai_api_key_here":
            return True
        if LLM_PROVIDER == "gemini" and GOOGLE_API_KEY and GOOGLE_API_KEY != "your_google_api_key_here":
            return True
        return False
    
    def extract_claims(self, answer: str) -> List[str]:
        """
        Extract factual claims from an answer.
        Simple heuristic: split by sentences and filter.
        """
        # Split into sentences
        sentences = re.split(r'[.!?]+', answer)
        
        claims = []
        for sent in sentences:
            sent = sent.strip()
            # Filter out very short or non-factual sentences
            if len(sent) > 20 and not sent.startswith(('I ', 'We ', 'You ')):
                # Check if it contains factual content (numbers, technical terms)
                if re.search(r'\d|[A-Z]{2,}|specifically|defined|means|refers to', sent):
                    claims.append(sent)
        
        return claims
    
    def check_claim_support(self, claim: str, context: str) -> bool:
        """
        Check if a claim is supported by the context.
        Uses simple keyword/phrase overlap heuristic.
        """
        claim_lower = claim.lower()
        context_lower = context.lower()
        
        # Extract key terms from claim
        terms = re.findall(r'\b[a-z]{3,}\b', claim_lower)
        technical_terms = re.findall(r'\b[A-Z]{2,6}\b', claim)
        
        # Count term overlap
        term_matches = sum(1 for t in terms if t in context_lower)
        tech_matches = sum(1 for t in technical_terms if t in context)
        
        # Calculate support ratio
        total_terms = len(terms) + len(technical_terms)
        if total_terms == 0:
            return True  # No specific claims to verify
        
        support_ratio = (term_matches + tech_matches * 2) / (total_terms + len(technical_terms))
        
        return support_ratio > 0.3
    
    def calculate_faithfulness(
        self, 
        answer: str, 
        context: str
    ) -> Tuple[float, List[str], int, int]:
        """
        Calculate faithfulness score (Heuristic).
        Measures how grounded the answer is in the provided context.
        """
        claims = self.extract_claims(answer)
        
        if not claims:
            return 1.0, [], 0, 0  # No claims = faithful by default
        
        supported = 0
        for claim in claims:
            if self.check_claim_support(claim, context):
                supported += 1
        
        score = supported / len(claims) if claims else 1.0
        return score, claims, supported, len(claims)

    def calculate_llm_faithfulness(self, answer: str, context: str) -> float:
        """
        Calculate faithfulness using LLM (More accurate).
        """
        if not self.llm:
            return 0.0
            
        prompt = f"""Rate the faithfulness of the answer to the context on a scale of 0.0 to 1.0.
Faithfulness measures if the answer is derived solely from the context given.
Return ONLY the float score.

Context:
{context[:2000]}...

Answer:
{answer}

Score:"""
        try:
            response = self.llm.simple_generate(prompt).strip()
            # extract float
            match = re.search(r"0\.\d+|1\.0|0|1", response)
            if match:
                return float(match.group())
            return 0.5 # Fallback
        except Exception as e:
            print(f"⚠️ LLM Faithfulness failed: {e}")
            return 0.5

    def calculate_relevancy(self, question: str, answer: str) -> float:
        """
        Calculate how relevant the answer is to the question.
        Uses keyword overlap heuristic.
        """
        question_terms = set(re.findall(r'\b[a-z]{3,}\b', question.lower()))
        question_tech = set(re.findall(r'\b[A-Z]{2,6}\b', question))
        
        answer_terms = set(re.findall(r'\b[a-z]{3,}\b', answer.lower()))
        answer_tech = set(re.findall(r'\b[A-Z]{2,6}\b', answer))
        
        # Remove common words
        common_words = {'what', 'how', 'why', 'when', 'where', 'which', 'the', 'and', 'for'}
        question_terms -= common_words
        
        if not question_terms and not question_tech:
            return 1.0
        
        # Calculate overlap
        term_overlap = len(question_terms & answer_terms)
        tech_overlap = len(question_tech & answer_tech)
        
        total_question = len(question_terms) + len(question_tech)
        overlap = term_overlap + tech_overlap * 2  # Weight technical terms higher
        
        return min(1.0, overlap / total_question) if total_question > 0 else 1.0

    def calculate_llm_relevancy(self, question: str, answer: str) -> float:
        """
        Calculate relevancy using LLM.
        """
        if not self.llm:
            return 0.0
            
        prompt = f"""Rate the relevancy of the answer to the question on a scale of 0.0 to 1.0.
Relevancy measures if the answer actually answers the question asked.
Return ONLY the float score.

Question:
{question}

Answer:
{answer}

Score:"""
        try:
            response = self.llm.simple_generate(prompt).strip()
            match = re.search(r"0\.\d+|1\.0|0|1", response)
            if match:
                return float(match.group())
            return 0.5
        except Exception as e:
            print(f"⚠️ LLM Relevancy failed: {e}")
            return 0.5
    
    def calculate_retrieval_confidence(
        self, 
        similarity_scores: List[float]
    ) -> float:
        """
        Calculate confidence based on retrieval quality.
        Uses average of top similarity scores.
        """
        if not similarity_scores:
            return 0.0
        
        # Use top 3 scores
        top_scores = sorted(similarity_scores, reverse=True)[:3]
        avg_score = sum(top_scores) / len(top_scores)
        
        # Check if best match is good enough
        best_score = max(similarity_scores)
        
        if best_score < self.MIN_SIMILARITY_THRESHOLD:
            return 0.3  # Very low confidence
        
        return avg_score
    
    def evaluate(
        self,
        question: str,
        answer: str,
        context: str,
        similarity_scores: List[float],
        use_llm: bool = False
    ) -> EvaluationResult:
        """
        Full evaluation of a RAG response.
        
        Args:
            question: User's question
            answer: Generated answer
            context: Retrieved context used for generation
            similarity_scores: Similarity scores from retrieval
            use_llm: Whether to use LLM for evaluation (slower, more accurate)
            
        Returns:
            EvaluationResult with all metrics
        """
        # Calculate faithfulness
        if use_llm and self.llm:
            faithfulness = self.calculate_llm_faithfulness(answer, context)
            claims = ["LLM Evaluated"] # Skip claim extraction for LLM mode to save time? Or keep it?
            # Let's keep heuristic claims for display, but override score
            _, heuristic_claims, supported, total = self.calculate_faithfulness(answer, context)
            claims = heuristic_claims
        else:
            faithfulness, claims, supported, total = self.calculate_faithfulness(answer, context)
        
        # Calculate relevancy
        if use_llm and self.llm:
            relevancy = self.calculate_llm_relevancy(question, answer)
        else:
            relevancy = self.calculate_relevancy(question, answer)
        
        # Calculate retrieval confidence
        retrieval_confidence = self.calculate_retrieval_confidence(similarity_scores)
        
        # Combined confidence score (weighted average)
        confidence = (
            faithfulness * 0.4 +
            relevancy * 0.3 +
            retrieval_confidence * 0.3
        )
        
        # Determine abstention
        should_abstain = False
        abstention_reason = ""
        
        if retrieval_confidence < self.MIN_SIMILARITY_THRESHOLD:
            should_abstain = True
            abstention_reason = "Retrieved documents have low relevance to the question"
        elif faithfulness < self.ABSTENTION_THRESHOLD:
            should_abstain = True
            abstention_reason = "Answer may not be fully grounded in available information"
        elif confidence < self.ABSTENTION_THRESHOLD:
            should_abstain = True
            abstention_reason = "Insufficient confidence to provide a reliable answer"
        
        # Calculate context precision (relevant chunks / total)
        # Using similarity scores as proxy for relevance
        high_relevance_count = sum(1 for s in similarity_scores if s > 0.5)
        context_precision = high_relevance_count / len(similarity_scores) if similarity_scores else 0.0
        
        # Calculate context recall (supported claims / total claims)
        # Using heuristic supported count even in LLM mode for now as proxy
        context_recall = supported / total if total > 0 else 1.0
        
        # Calculate Reliability/Trust Score (Section 5.2 TLM)
        # Weighted average of key metrics:
        # - Faithfulness (40%): Is it true?
        # - Relevancy (30%): Is it useful?
        # - Ctx Precision (20%): Was retrieval good?
        # - Confidence (10%): Does model feel sure?
        trust_score = (faithfulness * 0.4) + (relevancy * 0.3) + (context_precision * 0.2) + (confidence * 0.1)
        
        return EvaluationResult(
            faithfulness_score=faithfulness,
            relevancy_score=relevancy,
            confidence_score=confidence,
            should_abstain=should_abstain,
            abstention_reason=abstention_reason,
            claims=claims,
            supported_claims=supported,
            total_claims=total,
            context_precision=context_precision,
            context_recall=context_recall,
            trust_score=trust_score,
            consistency_score=1.0  # Placeholder: Requires multi-generation logic
        )
    
    def get_abstention_message(self, reason: str) -> str:
        """Generate a polite abstention message."""
        return f"""⚠️ **Unable to provide a confident answer**

{reason}

**What you can do:**
- Try rephrasing your question with more specific terms
- Check if the topic is covered in the knowledge base
- Consult official 3GPP documentation for authoritative information

*This response was withheld because the system could not verify the accuracy of the answer based on available sources.*"""


# Global instance
_evaluator = None


def get_evaluator() -> RAGEvaluator:
    """Get or create global evaluator instance."""
    global _evaluator
    if _evaluator is None:
        _evaluator = RAGEvaluator()
    return _evaluator


if __name__ == "__main__":
    # Test evaluation
    evaluator = RAGEvaluator()
    
    question = "What is HARQ in 5G NR?"
    answer = "HARQ (Hybrid Automatic Repeat Request) is a error correction mechanism in 5G NR that combines forward error correction with retransmission. It uses soft combining to improve reliability."
    context = "HARQ (Hybrid Automatic Repeat Request) is a combination of high-rate forward error correction (FEC) and ARQ error-control. In 5G NR, HARQ provides reliable data transmission by using incremental redundancy."
    
    result = evaluator.evaluate(question, answer, context, [0.85, 0.72, 0.65])
    
    print("\n📊 Evaluation Results:")
    print(f"  Faithfulness: {result.faithfulness_score:.2f}")
    print(f"  Relevancy: {result.relevancy_score:.2f}")
    print(f"  Confidence: {result.confidence_score:.2f}")
    print(f"  Should Abstain: {result.should_abstain}")
    print(f"  Claims: {result.total_claims} total, {result.supported_claims} supported")
