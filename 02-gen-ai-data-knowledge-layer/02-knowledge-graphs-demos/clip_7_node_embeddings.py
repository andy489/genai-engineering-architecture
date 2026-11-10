import networkx as nx
from node2vec import Node2Vec
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Create a simple graph
G = nx.karate_club_graph()  # Zachary's karate club, a classic social network

# Generate walks and train Node2Vec
node2vec = Node2Vec(G, dimensions=64, walk_length=30, num_walks=200, workers=4)
model = node2vec.fit(window=10, min_count=1, batch_words=4)

# Get embedding for node 0
embedding_0 = model.wv['0']  # gensim word2vec format

# Get embeddings for all nodes
embeddings = np.array([model.wv[str(node)] for node in G.nodes()])

# Compute cosine similarity between node 0 and node 33
sim = cosine_similarity([embeddings[0]], [embeddings[33]])[0][0]
print(f"Similarity between node 0 and node 33: {sim:.3f}")

# Find top 5 nodes most similar to node 0
similar_nodes = model.wv.most_similar('0', topn=5)
print("Nodes most similar to node 0:")
for node, score in similar_nodes:
    print(f"  - node {node}: similarity {score:.3f}")