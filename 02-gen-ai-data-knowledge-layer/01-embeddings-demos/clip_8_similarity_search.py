import numpy as np
from typing import List, Dict
from sklearn.preprocessing import normalize

class SemanticSearchEngine:
    def __init__(self, embedding_model, vector_store):
        self.model = embedding_model
        self.store = vector_store  # Assume {doc_id: {"text": str, "embedding": list, "metadata": dict}}
        
    def formulate_query(self, user_query: str, query_expansion: bool = False) -> List[float]:
        """
        Transform natural language query into an embedding.
        Optional: Expand the query for better retrieval.
        """
        # Basic query embedding
        base_embedding = self.model.embed_query(user_query)
        
        if query_expansion:
            # Simple synonym expansion for demonstration
            # In production, you might use an LLM to generate multiple query perspectives
            expanded_queries = [
                user_query,
                f"details about {user_query}",
                f"explanation of {user_query}"
            ]
            embeddings = [self.model.embed_query(q) for q in expanded_queries]
            # Average the embeddings for a more robust query representation
            base_embedding = np.mean(embeddings, axis=0)
        
        return base_embedding
    
    def calculate_similarity(self, query_embedding: List[float], 
                           doc_embedding: List[float], 
                           method: str = "cosine") -> float:
        """
        Calculate similarity between query and document.
        """
        query_vec = np.array(query_embedding)
        doc_vec = np.array(doc_embedding)
        
        if method == "cosine":
            # Cosine similarity = dot product of normalized vectors
            query_norm = normalize(query_vec.reshape(1, -1))[0]
            doc_norm = normalize(doc_vec.reshape(1, -1))[0]
            return np.dot(query_norm, doc_norm)
        elif method == "dot":
            # Dot product (for normalized embeddings, this equals cosine similarity)
            return np.dot(query_vec, doc_vec)
        else:
            raise ValueError(f"Unknown similarity method: {method}")
    
    def search(self, user_query: str, 
               top_k: int = 5, 
               score_threshold: float = 0.7,
               use_metadata_filter: Dict = None) -> List[Dict]:
        """
        Main search pipeline: query -> embedding -> similarity calculation -> ranking.
        """
        # Step 1: Query Formulation
        query_embedding = self.formulate_query(user_query, query_expansion=True)
        
        # Step 2: Similarity Calculation with all candidates
        results = []
        for doc_id, doc_data in self.store.items():
            # Apply metadata filter if provided
            if use_metadata_filter:
                if not all(doc_data["metadata"].get(k) == v 
                          for k, v in use_metadata_filter.items()):
                    continue
            
            # Calculate similarity score
            similarity = self.calculate_similarity(
                query_embedding, 
                doc_data["embedding"]
            )
            
            # Only include results above threshold
            if similarity >= score_threshold:
                results.append({
                    "doc_id": doc_id,
                    "text": doc_data["text"],
                    "score": similarity,
                    "metadata": doc_data["metadata"]
                })
        
        # Step 3: Ranking by similarity score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Step 4: Return top_k results (with optional re-ranking)
        return self._rerank_results(results[:top_k], user_query)
    
    def _rerank_results(self, initial_results: List[Dict], query: str) -> List[Dict]:
        """
        Optional second-stage re-ranking for improved relevance.
        This could use a cross-encoder model or LLM judgment.
        For now, we'll implement a simple heuristic: boost chunks with query terms.
        """
        for result in initial_results:
            # Simple keyword overlap boost (hybrid approach)
            query_terms = set(query.lower().split())
            chunk_terms = set(result["text"].lower().split())
            overlap = len(query_terms.intersection(chunk_terms)) / len(query_terms)
            
            # Adjust score: 70% semantic similarity, 30% keyword overlap
            result["adjusted_score"] = (0.7 * result["score"]) + (0.3 * overlap)
        
        # Re-sort by adjusted score
        initial_results.sort(key=lambda x: x["adjusted_score"], reverse=True)
        return initial_results
    
    def tune_relevance(self, query: str, expected_results: List[str], 
                      tuning_param: str = "score_threshold") -> Dict:
        """
        Interactive relevance tuning based on feedback.
        In production, this would use collected user feedback data.
        """
        best_params = {"score_threshold": 0.7, "top_k": 5}
        
        # Simulate parameter search
        if tuning_param == "score_threshold":
            for threshold in [0.6, 0.7, 0.8, 0.85]:
                results = self.search(query, score_threshold=threshold)
                retrieved_ids = [r["doc_id"] for r in results]
                
                # Calculate precision at K
                relevant_retrieved = len(set(retrieved_ids) & set(expected_results))
                precision = relevant_retrieved / len(retrieved_ids) if retrieved_ids else 0
                
                print(f"Threshold {threshold}: Precision = {precision:.2f}")
                
                if precision > 0.8:  # Our target
                    best_params["score_threshold"] = threshold
                    break
        
        return best_params

# Demonstration with mock data
if __name__ == "__main__":
    # Mock embedding model (in reality, use OpenAIEmbeddings or similar)
    class MockEmbedder:
        def embed_query(self, text):
            # Return random embedding for demo
            return list(np.random.randn(256))
    
    # Mock vector store with sample documents
    mock_store = {
        "doc1": {
            "text": "Machine learning models require large datasets for training.",
            "embedding": list(np.random.randn(256)),
            "metadata": {"category": "AI", "year": 2023}
        },
        "doc2": {
            "text": "Deep learning uses neural networks with multiple layers.",
            "embedding": list(np.random.randn(256)),
            "metadata": {"category": "AI", "year": 2024}
        },
        "doc3": {
            "text": "Climate change is causing global temperature increases.",
            "embedding": list(np.random.randn(256)),
            "metadata": {"category": "Environment", "year": 2023}
        }
    }
    
    # Initialize search engine
    engine = SemanticSearchEngine(MockEmbedder(), mock_store)
    
    # Perform a search
    query = "What are the requirements for training AI models?"
    print(f"Query: '{query}'")
    print("\nSearch Results:")
    print("-" * 50)
    
    results = engine.search(
        query, 
        top_k=3, 
        use_metadata_filter={"category": "AI"}
    )
    
    for i, result in enumerate(results, 1):
        print(f"{i}. [Score: {result['score']:.3f}]")
        print(f"   Text: {result['text'][:80]}...")
        print(f"   Metadata: {result['metadata']}")
        print()
    
    # Demonstrate relevance tuning
    print("Relevance Tuning Simulation:")
    print("-" * 50)
    best_params = engine.tune_relevance(
        query, 
        expected_results=["doc1", "doc2"],  # What we expect to be relevant
        tuning_param="score_threshold"
    )
    print(f"\nOptimal parameters: {best_params}")