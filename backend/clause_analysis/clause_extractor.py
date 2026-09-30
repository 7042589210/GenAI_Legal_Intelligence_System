import re
from typing import List, Dict, Any
from backend.preprocessing.text_normalizer import normalize_legal_text

def parse_clauses_and_metadata(pages_data: List[Dict[str, Any]], filename: str) -> List[Dict[str, Any]]:
    """
    Parses normalized contract text into structured clause chunks with metadata.
    Captures Clause/Section headings and attaches page number and source filename.
    """
    structured_chunks = []
    pattern = re.compile(r'(?:Clause|Section|\d+\.\d+|\d+\.)\s*[^.\n]+', re.IGNORECASE)

    for page_item in pages_data:
        raw_text = page_item["text"]
        text = normalize_legal_text(raw_text)

        matches = list(pattern.finditer(text))
        if matches:
            for i in range(len(matches)):
                start = matches[i].start()
                end = matches[i+1].start() if i + 1 < len(matches) else len(text)
                structured_chunks.append({
                    "text": text[start:end].strip(),
                    "metadata": {
                        "source": filename,
                        "page": page_item["page"],
                        "clause": matches[i].group(0).strip()
                    }
                })
        else:
            structured_chunks.append({
                "text": text,
                "metadata": {"source": filename, "page": page_item["page"], "clause": "General Provision"}
            })
    return structured_chunks
