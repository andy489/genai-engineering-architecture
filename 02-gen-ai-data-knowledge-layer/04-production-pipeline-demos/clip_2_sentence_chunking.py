import nltk
nltk.download('punkt_tab')

from nltk.tokenize import sent_tokenize

def sentence_based_chunking(text, max_sentences=3):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []
    
    for sentence in sentences:
        current_chunk.append(sentence)
        if len(current_chunk) >= max_sentences:
            chunk_text = " ".join(current_chunk)
            chunks.append(chunk_text)
            current_chunk = []
    
    # Add the last chunk if it has any sentences
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

# Example usage
sample_paragraph = "This is the first sentence. This is the second. This is the third. Here is a fourth sentence. And a fifth one."
sentence_chunks = sentence_based_chunking(sample_paragraph, max_sentences=2)
for i, chunk in enumerate(sentence_chunks):
    print(f"Chunk {i+1}: {chunk}")