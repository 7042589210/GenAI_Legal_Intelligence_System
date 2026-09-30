import re

def normalize_legal_text(raw_text: str) -> str:
    """
    Normalizes raw text extracted from legal PDFs or OCR:
    - Cleans irregular whitespace, broken line breaks, and page header/footer noise.
    - Standardizes formatting without changing words, legal terms, clause numbers, dates, values, or definitions.
    - Preserves logical paragraph structures and numbered clause boundaries.
    """
    if not raw_text:
        return ""

    # 1. Remove PDF/OCR page header and footer noise (e.g. '--- Page 1 (Native) ---', 'Page X of Y')
    text = re.sub(r'---\s*Page\s*\d+\s*\([^)]+\)\s*---', '', raw_text)
    text = re.sub(r'(?i)Page\s+\d+\s+of\s+\d+', '', text)

    # 2. Normalize horizontal spaces per line
    lines = [re.sub(r'[ \t]+', ' ', line.strip()) for line in text.splitlines()]

    # 3. Rejoin broken line breaks within paragraphs while keeping clause boundaries
    normalized_paragraphs = []
    buffer = ""

    clause_start_pattern = re.compile(
        r'^(?:Clause|Section|\d+(\.\d+)*|\([a-z0-9]+\))\b', re.IGNORECASE
    )

    for line in lines:
        if not line:
            if buffer:
                normalized_paragraphs.append(buffer)
                buffer = ""
            continue

        if clause_start_pattern.match(line) and buffer:
            normalized_paragraphs.append(buffer)
            buffer = line
        elif not buffer:
            buffer = line
        else:
            # Rejoin hyphenated words split across line breaks
            if buffer.endswith('-') and len(buffer) > 1 and buffer[-2].isalpha():
                buffer = buffer[:-1] + line
            else:
                buffer += " " + line

    if buffer:
        normalized_paragraphs.append(buffer)

    return "\n\n".join(normalized_paragraphs).strip()
