"""Telecom RAG - LLM Integration Module

Supports:
- OpenAI GPT-4o-mini
- Google Gemini Flash
"""

from typing import Optional, List, Dict, Any

from .config import (
    LLM_PROVIDER,
    OPENAI_API_KEY,
    GOOGLE_API_KEY,
    OPENAI_MODEL,
    GEMINI_MODEL,
    TELECOM_PROMPT_TEMPLATE
)


class TelecomLLM:
    """Unified LLM interface for telecom RAG."""
    
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or LLM_PROVIDER
        self._initialize()
    
    def _initialize(self):
        """Initialize the LLM client with graceful fallback."""
        if self.provider == "gemini":
            try:
                self._init_gemini()
                return
            except (ImportError, Exception) as e:
                print(f"⚠️ Gemini init failed: {e}")
                print("   Falling back to OpenAI...")
                self.provider = "openai"

        # Default to OpenAI
        self._init_openai()
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            
            if not OPENAI_API_KEY or OPENAI_API_KEY in ("your_openai_api_key_here", ""):
                raise ValueError(
                    "OPENAI_API_KEY not configured. "
                    "Set it via environment variable or in the .env file."
                )
            
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            self.model = OPENAI_MODEL
            print(f"✅ Initialized OpenAI LLM: {self.model}")
            
        except ImportError:
            raise ImportError("openai not installed. Run: pip install openai")
    
    def _init_gemini(self):
        """Initialize Google Gemini client."""
        try:
            import google.generativeai as genai
            
            if not GOOGLE_API_KEY or GOOGLE_API_KEY == "your_google_api_key_here":
                raise ValueError("GOOGLE_API_KEY not configured. Please update .env file.")
            
            genai.configure(api_key=GOOGLE_API_KEY)
            self.client = genai.GenerativeModel(GEMINI_MODEL)
            self.model = GEMINI_MODEL
            print(f"✅ Initialized Gemini LLM: {self.model}")
            
        except ImportError:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
    
    def generate(
        self, 
        question: str, 
        context: str, 
        glossary_terms: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Generate a response using the RAG prompt template.
        
        Args:
            question: User's question
            context: Retrieved context from vector store
            glossary_terms: Expanded glossary terms
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (lower = more focused)
            
        Returns:
            Dict with 'answer' and 'usage' info
        """
        # Build the prompt using Telco-RAG format
        prompt = TELECOM_PROMPT_TEMPLATE.format(
            question=question,
            context=context,
            glossary_terms=glossary_terms if glossary_terms else "No specific terms identified."
        )
        
        if self.provider == "gemini":
            return self._generate_gemini(prompt, max_tokens, temperature)
        else:
            return self._generate_openai(prompt, max_tokens, temperature)
    
    def _generate_openai(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float
    ) -> Dict[str, Any]:
        """Generate using OpenAI."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a telecom operations expert assistant. Provide accurate, grounded answers based on the provided context. Always cite your sources."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return {
            "answer": response.choices[0].message.content,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "model": self.model
        }
    
    def _generate_gemini(
        self, 
        prompt: str, 
        max_tokens: int, 
        temperature: float
    ) -> Dict[str, Any]:
        """Generate using Gemini."""
        import google.generativeai as genai
        
        generation_config = genai.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=temperature
        )
        
        response = self.client.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        return {
            "answer": response.text,
            "usage": {
                "prompt_tokens": 0,  # Gemini doesn't provide this easily
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "model": self.model
        }
    
    def simple_generate(self, prompt: str) -> str:
        """Simple generation without RAG formatting."""
        if self.provider == "gemini":
            response = self.client.generate_content(prompt)
            return response.text
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.3
            )
            return response.choices[0].message.content


if __name__ == "__main__":
    # Test LLM
    try:
        llm = TelecomLLM()
        
        # Test with sample context
        result = llm.generate(
            question="What is HARQ?",
            context="HARQ (Hybrid Automatic Repeat Request) is a combination of high-rate forward error correction and ARQ error-control. It is used in 5G NR for reliable data transmission.",
            glossary_terms="- HARQ: Hybrid Automatic Repeat Request\n- NR: New Radio"
        )
        
        print("\n📝 Generated response:")
        print(result["answer"])
        print(f"\n📊 Usage: {result['usage']}")
        
    except ValueError as e:
        print(f"⚠️ {e}")
        print("Please configure your API key in the .env file")
