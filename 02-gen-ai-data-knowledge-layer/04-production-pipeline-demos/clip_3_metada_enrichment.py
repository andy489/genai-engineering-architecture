import re
from typing import List, Dict

def enrich_chunks_with_metadata(document_title: str, content: str) -> List[Dict]:
    """
    Split content by headers and create enriched chunks.
    Each chunk gets the document title and its section header.
    """
    # Simple regex to find markdown-style headers (e.g., ## Section)
    header_pattern = r'^(#{1,3})\s+(.+)$'
    lines = content.split('\n')
    
    chunks = []
    current_section = "Introduction"  # Default for content before first header
    current_text = []
    
    for line in lines:
        header_match = re.match(header_pattern, line)
        if header_match:
            # Save the previous chunk if it exists
            if current_text:
                chunk_text = " ".join(current_text)
                enriched = f"[Title: {document_title}] [Section: {current_section}] {chunk_text}"
                chunks.append({
                    "text": enriched,
                    "metadata": {
                        "title": document_title,
                        "section": current_section,
                        "original_text": chunk_text  # Keep original if needed
                    }
                })
                current_text = []
            
            # Update current section
            current_section = header_match.group(2).strip()
        else:
            if line.strip():  # Only add non-empty lines
                current_text.append(line.strip())
    
    # Don't forget the last chunk
    if current_text:
        chunk_text = " ".join(current_text)
        enriched = f"[Title: {document_title}] [Section: {current_section}] {chunk_text}"
        chunks.append({
            "text": enriched,
            "metadata": {
                "title": document_title,
                "section": current_section,
                "original_text": chunk_text
            }
        })
    
    return chunks

# Example usage
doc_title = "2023 Annual Report"
doc_content = """
## Executive Summary
The company achieved record revenue in 2023.
Growth was driven by international expansion.

## Financial Highlights
Net income increased by 25% compared to 2022.
Operating expenses were well controlled.
"""

enriched_chunks = enrich_chunks_with_metadata(doc_title, doc_content)
for chunk in enriched_chunks:
    print("Enriched Text:")
    print(chunk["text"])
    print("Metadata:")
    print(chunk["metadata"])
    print("-" * 50)