def fixed_size_chunking(text, chunk_size=500, overlap=50):
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        # If this isn't the first chunk, apply overlap
        if start > 0:
            start = start - overlap
        chunk = text[start:end]
        chunks.append(chunk)
        start = end
    
    return chunks

# Example usage
sample_text = "Your long document text goes here. " * 50
chunks = fixed_size_chunking(sample_text, chunk_size=200, overlap=20)
print(f"Generated {len(chunks)} chunks")
print(f"First chunk: {chunks[0][:100]}...")

