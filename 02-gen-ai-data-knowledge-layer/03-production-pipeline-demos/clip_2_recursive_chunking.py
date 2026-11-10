def recursive_chunking(text, separators=None, chunk_size=500):
    if separators is None:
        separators = ["\n\n", "\n", ". ", " ", ""]
    
    # If the text is already small enough, return it as a single chunk
    if len(text) <= chunk_size:
        return [text]
    
    # Try splitting with the current separator
    separator = separators[0]
    if separator == "":
        # If we've reached character-level splitting, just return as list of characters?
        # In practice, we'd force split at chunk_size
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    splits = text.split(separator)
    
    # If splitting didn't create multiple pieces, try the next separator
    if len(splits) == 1:
        return recursive_chunking(text, separators[1:], chunk_size)
    
    # Build chunks by combining splits
    chunks = []
    current_chunk = ""
    for split in splits:
        # Add back the separator (except for the last piece)
        piece = split + (separator if split != splits[-1] else "")
        if len(current_chunk) + len(piece) <= chunk_size:
            current_chunk += piece
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # If the piece itself is too large, recursively split it
            if len(piece) > chunk_size:
                sub_chunks = recursive_chunking(piece, separators[1:], chunk_size)
                chunks.extend(sub_chunks)
                current_chunk = ""
            else:
                current_chunk = piece
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

# Example usage
hierarchical_text = "Section 1\n\nThis is a paragraph with multiple sentences. It talks about topic A. Still topic A.\n\nSection 2\n\nThis paragraph covers topic B. It has details about B."
recursive_chunks = recursive_chunking(hierarchical_text, chunk_size=50)
for i, chunk in enumerate(recursive_chunks):
    print(f"Recursive Chunk {i+1}: {chunk}")