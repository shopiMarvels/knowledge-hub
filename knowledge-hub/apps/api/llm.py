# apps/api/llm.py
import os
import httpx
from typing import List, Tuple

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

SYSTEM_PROMPT = (
    "You are a careful assistant that answers ONLY using the provided context. "
    "Cite sources as (Doc <id> #<chunk_index>). If insufficient context, say you don't know. "
    "Be concise and accurate. Do not make up information not present in the context."
)

def build_prompt(question: str, contexts: List[Tuple[str, str]]) -> str:
    """
    Build a grounded prompt with context and citations
    contexts: list[(tag, text)] where tag is like "Doc 4 #0"
    """
    if not contexts:
        return f"<system>\n{SYSTEM_PROMPT}\n</system>\n\n<user>\nQuestion: {question}\n\nNo context provided. Please say you don't have enough information.\n</user>"
    
    ctx_section = "\n\n".join([f"[{tag}]\n{text}" for tag, text in contexts])
    
    prompt = f"""<system>
{SYSTEM_PROMPT}
</system>

<user>
Question: {question}

Context:
{ctx_section}

Requirements:
- Use ONLY the provided context above
- Show citations like (Doc X #Y) for each fact you reference
- Be concise but comprehensive
- If the context doesn't contain enough information, say so clearly
</user>"""
    
    return prompt

async def generate_answer(question: str, contexts: List[Tuple[str, str]], max_tokens: int = 384) -> str:
    """
    Generate an answer using Ollama LLM with the provided context
    """
    try:
        prompt = build_prompt(question, contexts)
        
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": 4096,  # Context window
                "num_predict": max_tokens,  # Max tokens to generate
                "temperature": 0.1,  # Low temperature for more focused answers
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        }
        
        print(f"Generating answer for: '{question[:50]}...' using {len(contexts)} contexts")
        
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{OLLAMA_URL}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            
            answer = data.get("response", "").strip()
            
            if not answer:
                return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
            
            print(f"Generated answer length: {len(answer)} characters")
            return answer
            
    except httpx.TimeoutException:
        return "I'm taking too long to respond. Please try a simpler question or try again later."
    except httpx.HTTPStatusError as e:
        print(f"HTTP error calling Ollama: {e}")
        return "I'm having trouble connecting to the language model. Please try again later."
    except Exception as e:
        print(f"Error generating answer: {e}")
        return "I encountered an error while generating the answer. Please try again."

async def test_ollama_connection() -> bool:
    """
    Test if Ollama is accessible and the model is available
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Test basic connection
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            response.raise_for_status()
            
            models = response.json().get("models", [])
            model_names = [model.get("name", "") for model in models]
            
            if OLLAMA_MODEL not in model_names:
                print(f"Warning: Model '{OLLAMA_MODEL}' not found. Available models: {model_names}")
                return False
                
            print(f"Ollama connection successful. Model '{OLLAMA_MODEL}' is available.")
            return True
            
    except Exception as e:
        print(f"Ollama connection test failed: {e}")
        return False
