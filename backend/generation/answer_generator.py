from langchain_openai import ChatOpenAI
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

from backend.config.settings import get_openrouter_api_key, LLM_REASONING_MODEL
from backend.prompts.legal_prompts import get_legal_assistant_prompt
from backend.retrieval.retriever import get_retriever

def load_rag_chain():
    """Builds and returns the RAG retrieval chain for legal Q&A."""
    api_key = get_openrouter_api_key()

    llm = ChatOpenAI(
        model=LLM_REASONING_MODEL,
        temperature=0.0,
        api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        max_retries=2
    )
    
    prompt = get_legal_assistant_prompt()
    combine_docs_chain = create_stuff_documents_chain(llm, prompt)
    retriever = get_retriever(k=3)
    
    rag_chain = create_retrieval_chain(retriever, combine_docs_chain)
    return rag_chain

def answer_query(query: str):
    """Executes RAG Q&A query and returns (answer, context_docs)."""
    chain = load_rag_chain()
    try:
        response = chain.invoke({"input": query})
        return response["answer"], response["context"]
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
            return "⚠️ **Rate Limit Exceeded:** The OpenRouter API quota has been reached. Please wait a few seconds and try again.", []
        return f"⚠️ **Error:** {str(e)}", []
