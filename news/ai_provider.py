"""
AI Provider Wrapper for News Knowledge Graph

Provides a unified interface for OpenAI and Anthropic APIs for embeddings,
text generation, and other AI operations.
"""

import os
import json
from typing import List, Dict, Any, Optional, Union
from abc import ABC, abstractmethod
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings for text"""
        pass
    
    @abstractmethod
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        pass
    
    @abstractmethod
    def chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        """Generate chat completion"""
        pass

class OpenAIProvider(AIProvider):
    """OpenAI API provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.base_url = base_url
        self.default_embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
        self.default_chat_model = os.getenv('CHAT_MODEL', 'gpt-4o-mini')
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text using OpenAI"""
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.default_embedding_model,
            "input": text
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result['data'][0]['embedding']
        except Exception as e:
            raise ValueError(f"OpenAI embedding generation failed: {str(e)}")
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using OpenAI"""
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.default_embedding_model,
            "input": texts
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return [item['embedding'] for item in result['data']]
        except Exception as e:
            raise ValueError(f"OpenAI batch embedding generation failed: {str(e)}")
    
    def chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        """Generate chat completion using OpenAI"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model or self.default_chat_model,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            raise ValueError(f"OpenAI chat completion failed: {str(e)}")

class AnthropicProvider(AIProvider):
    """Anthropic API provider implementation"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.anthropic.com/v1"):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable.")
        
        self.base_url = base_url
        self.default_embedding_model = "claude-3-sonnet-20240229"
        self.default_chat_model = os.getenv('CHAT_MODEL', 'claude-3-sonnet-20240229')
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text using Anthropic"""
        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self.default_embedding_model,
            "max_tokens": 1,
            "messages": [{"role": "user", "content": text}]
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            # Note: Anthropic doesn't have a direct embeddings API like OpenAI
            # This is a placeholder - you might need to use a different approach
            raise NotImplementedError("Anthropic doesn't provide direct embeddings API. Use OpenAI for embeddings.")
        except Exception as e:
            raise ValueError(f"Anthropic embedding generation failed: {str(e)}")
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using Anthropic"""
        # Anthropic doesn't support batch embeddings
        embeddings = []
        for text in texts:
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        """Generate chat completion using Anthropic"""
        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Convert OpenAI format messages to Anthropic format
        anthropic_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                # Anthropic uses system prompt differently
                continue
            anthropic_messages.append(msg)
        
        payload = {
            "model": model or self.default_chat_model,
            "max_tokens": 1000,
            "messages": anthropic_messages
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result['content'][0]['text']
        except Exception as e:
            raise ValueError(f"Anthropic chat completion failed: {str(e)}")

class OllamaProvider(AIProvider):
    """Ollama local provider implementation"""
    
    def __init__(self, host: str = "localhost", port: int = 11434, model: str = "nomic-embed-text"):
        self.host = host
        self.port = port
        self.model = model
        self.base_url = f"http://{host}:{port}"
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using local Ollama"""
        url = f"{self.base_url}/api/embeddings"
        
        payload = {
            "model": self.model,
            "prompt": text
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result['embedding']
        except Exception as e:
            raise ValueError(f"Ollama embedding generation failed: {str(e)}")
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using Ollama"""
        embeddings = []
        for text in texts:
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        """Generate chat completion using Ollama"""
        url = f"{self.base_url}/api/generate"
        
        # Convert messages to Ollama format
        prompt = ""
        for msg in messages:
            if msg['role'] == 'system':
                prompt += f"System: {msg['content']}\n"
            elif msg['role'] == 'user':
                prompt += f"User: {msg['content']}\n"
            elif msg['role'] == 'assistant':
                prompt += f"Assistant: {msg['content']}\n"
        
        payload = {
            "model": model or "llama3.2",
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result['response']
        except Exception as e:
            raise ValueError(f"Ollama chat completion failed: {str(e)}")

def get_ai_provider(provider: str = "auto") -> AIProvider:
    """
    Factory function to get the appropriate AI provider
    
    Args:
        provider: Provider type ("openai", "anthropic", "ollama", or "auto")
    
    Returns:
        AIProvider instance
    """
    if provider == "openai":
        return OpenAIProvider()
    elif provider == "anthropic":
        return AnthropicProvider()
    elif provider == "ollama":
        host = os.getenv('OLLAMA_HOST', 'localhost')
        port = int(os.getenv('OLLAMA_PORT', '11434'))
        model = os.getenv('OLLAMA_MODEL', 'nomic-embed-text')
        return OllamaProvider(host, port, model)
    elif provider == "auto":
        # Auto-detect based on available API keys
        if os.getenv('OPENAI_API_KEY'):
            return OpenAIProvider()
        elif os.getenv('ANTHROPIC_API_KEY'):
            return AnthropicProvider()
        else:
            # Fall back to Ollama if no cloud API keys
            host = os.getenv('OLLAMA_HOST', 'localhost')
            port = int(os.getenv('OLLAMA_PORT', '11434'))
            model = os.getenv('OLLAMA_MODEL', 'nomic-embed-text')
            return OllamaProvider(host, port, model)
    else:
        raise ValueError(f"Unknown provider: {provider}")

# Convenience functions
def get_embeddings(text: str, provider: str = "auto") -> List[float]:
    """Get embeddings for text using the specified provider"""
    ai_provider = get_ai_provider(provider)
    return ai_provider.generate_embedding(text)

def get_embeddings_batch(texts: List[str], provider: str = "auto") -> List[List[float]]:
    """Get embeddings for multiple texts using the specified provider"""
    ai_provider = get_ai_provider(provider)
    return ai_provider.generate_embeddings_batch(texts)

def chat_completion(messages: List[Dict[str, str]], provider: str = "auto", model: Optional[str] = None) -> str:
    """Get chat completion using the specified provider"""
    ai_provider = get_ai_provider(provider)
    return ai_provider.chat_completion(messages, model)

if __name__ == "__main__":
    # Test the provider
    try:
        provider = get_ai_provider()
        print(f"✅ Using provider: {provider.__class__.__name__}")
        
        # Test embedding generation
        test_text = "This is a test text for embedding generation."
        embedding = provider.generate_embedding(test_text)
        print(f"✅ Generated embedding with {len(embedding)} dimensions")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please check your configuration and API keys.")
