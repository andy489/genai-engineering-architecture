import hashlib
import time
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter
from langchain_openai import OpenAIEmbeddings
import redis  # For caching
import tiktoken  # For token counting

class RobustEmbeddingPipeline:
    def __init__(self, model_name="text-embedding-3-small", dimensions=256):
        self.embeddings = OpenAIEmbeddings(
            model=model_name,
            dimensions=dimensions
        )
        self.cache = redis.Redis(host='localhost', port=6379, decode_responses=False)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
    def _cost_estimator(self, tokens: int) -> float:
        """Estimate cost in USD for embedding operations."""
        # text-embedding-3-small: $0.02 per 1M tokens
        cost_per_million = 0.02
        return (tokens / 1_000_000) * cost_per_million
    
    def smart_chunker(self, text: str, document_type: str = "general") -> List[str]:
        """
        Adaptive chunking based on content type.
        Returns chunks with preserved metadata headers.
        """
        if document_type == "academic":
            # Preserve sections for academic papers
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=100,
                separators=["\n## ", "\n# ", "\n\n", "\n", ". ", " "]
            )
        elif document_type == "code":
            # Keep functions/methods together
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=600,
                chunk_overlap=50,
                separators=["\ndef ", "\nclass ", "\n\n", "\n", " "]
            )
        else:
            # Token-based splitting for general text (more accurate for LLM context)
            splitter = SentenceTransformersTokenTextSplitter(
                chunk_size=512,
                chunk_overlap=50
            )
        
        chunks = splitter.split_text(text)
        
        # Enrich each chunk with context about its position
        enriched_chunks = []
        for i, chunk in enumerate(chunks):
            header = f"[Chunk {i+1} of {len(chunks)}] "
            enriched_chunks.append(header + chunk)
            
        return enriched_chunks
    
    def _rate_limiter(self, batch_size: int):
        """Respect API rate limits with adaptive waiting."""
        tokens_in_batch = batch_size * 512  # Conservative estimate
        if tokens_in_batch > 800000:  # OpenAI's RPM limit check
            time.sleep(60)  # Wait a minute if approaching limit
        elif tokens_in_batch > 400000:
            time.sleep(10)  # Shorter wait for moderate batches
        # Else proceed immediately
    
    def get_cached_embedding(self, text: str) -> List[float] | None:
        """Check cache for existing embedding to avoid redundant API calls."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        cached = self.cache.get(f"embedding:{text_hash}")
        if cached:
            return eval(cached)  # In production, use proper serialization
        return None
    
    def set_cached_embedding(self, text: str, embedding: List[float]):
        """Store embedding in cache with 30-day expiry."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        self.cache.setex(f"embedding:{text_hash}", 2592000, str(embedding))
    
    def process_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Process documents with enhanced robustness.
        Each document dict must have: 'text', 'id', 'type'
        """
        results = []
        total_cost = 0
        total_tokens = 0
        
        for doc in documents:
            # Step 1: Adaptive Chunking
            chunks = self.smart_chunker(doc['text'], doc.get('type', 'general'))
            
            for chunk_num, chunk in enumerate(chunks):
                # Step 2: Check Cache First
                cached_embedding = self.get_cached_embedding(chunk)
                if cached_embedding:
                    results.append({
                        'doc_id': doc['id'],
                        'chunk': chunk_num,
                        'embedding': cached_embedding,
                        'source': 'cache'
                    })
                    continue
                
                # Step 3: Rate Limit Management
                self._rate_limiter(len(chunks) - chunk_num)
                
                # Step 4: Generate Embedding with Cost Tracking
                chunk_tokens = len(self.tokenizer.encode(chunk))
                chunk_cost = self._cost_estimator(chunk_tokens)
                total_tokens += chunk_tokens
                total_cost += chunk_cost
                
                try:
                    embedding = self.embeddings.embed_query(chunk)
                    
                    # Step 5: Cache the Result
                    self.set_cached_embedding(chunk, embedding)
                    
                    results.append({
                        'doc_id': doc['id'],
                        'chunk': chunk_num,
                        'embedding': embedding,
                        'source': 'api',
                        'tokens': chunk_tokens
                    })
                    
                except Exception as e:
                    print(f"Failed on document {doc['id']}, chunk {chunk_num}: {str(e)}")
                    # Implement dead-letter queue in production
        
        print(f"Total tokens processed: {total_tokens:,}")
        print(f"Estimated cost: ${total_cost:.4f}")
        print(f"Cache hits: {len([r for r in results if r['source']=='cache'])}")
        
        return results

# Usage Example
if __name__ == "__main__":
    pipeline = RobustEmbeddingPipeline(dimensions=256)  # Reduced dimensions for cost
    
    sample_docs = [
        {
            'id': 'doc_1',
            'text': "Climate change impacts include rising sea levels and increased frequency of extreme weather events. These changes affect ecosystems and human societies globally.",
            'type': 'general'
        },
        {
            'id': 'doc_2',
            'text': "def calculate_embedding(text):\n    vector = model.encode(text)\n    return vector.tolist()\n\nclass DocumentProcessor:\n    def __init__(self):\n        self.cache = {}",
            'type': 'code'
        }
    ]
    
    results = pipeline.process_documents(sample_docs)
    
    for result in results[:2]:
        print(f"\nDocument: {result['doc_id']}, Source: {result['source']}")
        print(f"Embedding length: {len(result['embedding'])}")