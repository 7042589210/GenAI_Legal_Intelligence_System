from langchain_groq import ChatGroq
from backend.config.settings import get_groq_api_key, LLM_SCAN_MODEL
from backend.schemas.legal_schemas import ContractAnalysisResponse

def analyze_structured_risks(chunks: list) -> ContractAnalysisResponse:
    """Extracts structured Pydantic Risk Flags, Clauses, and Summary using Groq structured output. Now uses chunk metadata for citations."""
    api_key = get_groq_api_key()

    llm = ChatGroq(
        model=LLM_SCAN_MODEL,
        temperature=0.1,
        api_key=api_key,
        max_retries=2
    )
    structured_llm = llm.with_structured_output(ContractAnalysisResponse)
    
    context_text = ""
    used_chunks = []
    current_char_count = 0
    max_chars = 24000  # approx 6000 tokens limit

    for idx, chunk in enumerate(chunks):
        chunk_text = chunk.get('text', '')
        if current_char_count + len(chunk_text) > max_chars and idx > 0:
            break
            
        meta = chunk.get("metadata", {})
        source = meta.get("source", "Unknown Document")
        page = meta.get("page", 1)
        clause = meta.get("clause", "Unknown Clause")
        
        formatted_chunk = f"\n--- CHUNK {idx} | Source: {source} | Page: {page} | Clause: {clause} ---\n{chunk_text}\n"
        context_text += formatted_chunk
        current_char_count += len(formatted_chunk)
        used_chunks.append(chunk)

    prompt = (
        "Analyze the following legal contract text segments. Extract document summary, "
        "key extracted clauses, and risk flags with severity, rationale, and recommendation. "
        "Ensure every risk flag includes the precise clause name, number, potential impact, "
        "and a direct exact-match evidence quote. Also include Citations mapping to the Source/Page/Clause metadata provided.\n"
        "Do not invent facts or clauses. If information is unavailable, state: 'Not specified in the document.' Do not hallucinate missing legal information.\n"
        "You MUST output valid JSON matching the exact schema requested.\n\n"
        f"Context:\n{context_text}"
    )
    try:
        response = structured_llm.invoke(prompt)
        
        # Evidence Verification Layer
        for rf in response.risk_flags:
            verified_citations = []
            for citation in rf.citations:
                # Check if citation text exists in ANY of the original chunks
                is_verified = False
                for chunk in used_chunks:
                    if citation.evidence_text.lower() in chunk.get('text', '').lower():
                        is_verified = True
                        break
                if is_verified:
                    verified_citations.append(citation)
            
            # Replace with only verified citations
            rf.citations = verified_citations
            if not rf.citations:
                rf.evidence = "Evidence could not be verified or was hallucinated."
                
        return response
    except Exception as e:
        if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
            raise Exception("Rate Limit Exceeded: The Groq API quota has been reached. Please wait a few seconds and try again.")
        raise
