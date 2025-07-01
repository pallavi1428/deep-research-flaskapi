from openai import OpenAI
import tiktoken
from config import (
    OPENAI_KEY,
    OPENAI_ENDPOINT,
    CUSTOM_MODEL,
    CONTEXT_SIZE,
)

class LanguageModel:
    def __init__(self, model_name: str = "gpt-4-turbo", base_url: str = OPENAI_ENDPOINT):
        if not OPENAI_KEY:
            raise ValueError("OpenAI API key is missing in configuration")
            
        self.client = OpenAI(
            api_key=OPENAI_KEY,
            base_url=base_url.rstrip('/'),
            timeout=30.0
        )
        self.model_name = model_name
        # Removed validation to prevent errors - we'll validate during first generation instead

    def generate(self, messages: list, max_tokens: int = 2048) -> str:
        """Generate completion with simple error handling"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise ValueError(f"Failed to generate response: {str(e)}")

# Simple singleton pattern
_model = None

def get_model() -> LanguageModel:
    global _model
    if _model is None:
        # Use actual model name from config or default
        model_id = CUSTOM_MODEL if CUSTOM_MODEL and CUSTOM_MODEL != "CUSTOM_MODEL=gpt-4-turbo" else "gpt-4-turbo"
        _model = LanguageModel(model_name=model_id)
    return _model

# Tokenizer setup
try:
    ENCODER = tiktoken.encoding_for_model("gpt-4")
except:
    ENCODER = tiktoken.get_encoding("cl100k_base")

def trim_prompt(prompt: str, context_size: int = CONTEXT_SIZE) -> str:
    """Simple prompt trimming without complex error handling"""
    if not prompt:
        return ""
    
    encoded = ENCODER.encode(prompt)
    max_tokens = context_size - 1000  # Leave buffer
    
    if len(encoded) <= max_tokens:
        return prompt
    
    trimmed = ENCODER.decode(encoded[:max_tokens])
    return trimmed.rsplit('\n', 1)[0] if '\n' in trimmed else trimmed[:max_tokens*3]