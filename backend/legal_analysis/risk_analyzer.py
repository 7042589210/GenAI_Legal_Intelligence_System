import asyncio
import random
import logging
from langchain_openai import ChatOpenAI
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

from backend.config.settings import get_openrouter_api_key, LLM_REASONING_MODEL, LLM_SCAN_MODEL
from backend.prompts.legal_prompts import get_risk_analysis_prompt
from backend.retrieval.retriever import get_retriever

logger = logging.getLogger(__name__)

# SEMAPHORES: Cap simultaneous in-flight requests to OpenRouter
REASONING_SEMAPHORE = asyncio.Semaphore(1)  # Strict limit for heavy 120b model
SCAN_SEMAPHORE = asyncio.Semaphore(3)       # Broader limit for lightweight 27b model

def load_risk_chain(model_name: str = LLM_REASONING_MODEL):
    """Builds and returns the RAG retrieval chain for legal risk analysis."""
    api_key = get_openrouter_api_key()

    llm = ChatOpenAI(
        model=model_name,
        temperature=0.1,
        api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        max_retries=0 # Retries handled manually via exponential backoff below
    )
    
    prompt = get_risk_analysis_prompt()
    combine_docs_chain = create_stuff_documents_chain(llm, prompt)
    retriever = get_retriever(k=5)
    
    risk_chain = create_retrieval_chain(retriever, combine_docs_chain)
    return risk_chain

def analyze_contract_risks(
    query: str = "Perform a comprehensive risk assessment covering liability, termination, indemnity, payment terms, and governing law."
):
    """Performs RAG-based legal risk analysis on the indexed contract in ChromaDB."""
    chain = load_risk_chain(LLM_REASONING_MODEL)
    try:
        response = chain.invoke({"input": query})
        return response["answer"], response["context"]
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
            return "⚠️ **Rate Limit Exceeded:** The free tier Google Gemini API quota has been reached. Please wait a few seconds and try again.", []
        return f"⚠️ **Error:** {str(e)}", []

async def analyze_contract_risks_async(
    query: str = "Perform a comprehensive risk assessment covering liability, termination, indemnity, payment terms, and governing law.",
    use_reasoning_model: bool = True
):
    model_name = LLM_REASONING_MODEL if use_reasoning_model else LLM_SCAN_MODEL
    semaphore = REASONING_SEMAPHORE if use_reasoning_model else SCAN_SEMAPHORE
    chain = load_risk_chain(model_name=model_name)
    
    max_retries = 5
    base_delay = 2.0

    async with semaphore:
        for attempt in range(max_retries):
            try:
                # Use ainvoke for non-blocking network calls
                response = await chain.ainvoke({"input": query})
                return response["answer"], response["context"]
            
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "RateLimitError" in error_msg:
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        delay = (base_delay ** attempt) + random.uniform(0, 1)
                        logger.warning(f"OpenRouter Rate Limit Exceeded (429). Retrying in {delay:.2f}s...")
                        await asyncio.sleep(delay)
                    else:
                        return "⚠️ **Rate Limit Exceeded:** OpenRouter API quota reached. Please try again later.", []
                else:
                    return f"⚠️ **Error:** {str(e)}", []
