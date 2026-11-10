import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from typing import List

# 1. SETUP & CONFIGURATION
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize our embedding model
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    dimensions=256  # Using smaller dimension for efficiency
)

# 2. CHUNKING STRATEGY
def chunk_document(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """Split document into semantically coherent chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    return text_splitter.split_text(text)

# 3. BATCH PROCESSING
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def embed_batch_with_retry(texts: List[str]) -> List[List[float]]:
    """Embed a batch of texts with automatic retry logic."""
    try:
        return embeddings.embed_documents(texts)
    except Exception as e:
        logger.error(f"Embedding batch failed: {str(e)}")
        raise

# 4. MAIN PIPELINE
def generate_document_embeddings(documents: List[str], batch_size: int = 100) -> List[tuple]:
    """
    End-to-end pipeline: chunk → batch → embed → store.
    Returns list of (chunk_text, embedding_vector) tuples.
    """
    all_chunks = []
    metadata = []
    
    # Step 1: Preprocess and chunk all documents
    logger.info(f"Processing {len(documents)} documents...")
    for i, doc in enumerate(documents):
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)
        # Track which document each chunk came from
        metadata.extend([{"doc_id": i, "chunk_index": j} for j in range(len(chunks))])
    
    logger.info(f"Created {len(all_chunks)} total chunks.")
    
    # Step 2: Process in batches
    results = []
    for batch_start in range(0, len(all_chunks), batch_size):
        batch_end = batch_start + batch_size
        batch_texts = all_chunks[batch_start:batch_end]
        batch_meta = metadata[batch_start:batch_end]
        
        logger.info(f"Embedding batch {batch_start//batch_size + 1}/{(len(all_chunks)-1)//batch_size + 1}")
        
        try:
            # This is where the actual embedding happens
            batch_embeddings = embed_batch_with_retry(batch_texts)
            
            # Combine text, embedding, and metadata
            for text, embedding, meta in zip(batch_texts, batch_embeddings, batch_meta):
                results.append((text, embedding, meta))
                
        except Exception as e:
            logger.error(f"Failed to process batch starting at index {batch_start}: {str(e)}")
            # In production, you might implement a dead-letter queue here
    
    logger.info(f"Successfully embedded {len(results)} chunks.")
    return results

# 5. EXAMPLE EXECUTION
if __name__ == "__main__":
    # Simulate loading documents (in reality, this would be from files, a database, etc.)
    sample_documents = [
        "The theory of relativity transformed our understanding of space and time. Einstein's insights showed that these are not absolute but relative to the observer.",
        "Machine learning models learn patterns from data. Deep learning, a subset of ML, uses neural networks with multiple layers to model complex relationships.",
        "Climate change represents one of the greatest challenges of our century. Rising temperatures, sea levels, and extreme weather events demand urgent action."
    ]
    
    # Run the pipeline
    embedded_chunks = generate_document_embeddings(sample_documents, batch_size=2)
    
    # Show a sample result
    if embedded_chunks:
        sample_text, sample_embedding, sample_meta = embedded_chunks[0]
        print(f"\nSample chunk text: {sample_text[:100]}...")
        print(f"Embedding dimension: {len(sample_embedding)}")
        print(f"First 5 values: {sample_embedding[:5]}")
        print(f"Metadata: {sample_meta}")