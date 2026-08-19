# Quick Start Guide: `domain.embedding_cluster` (v1.0.0)

> Unsupervised text chunk clustering, topic keyword extraction, and cluster summary generator

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`cluster_text_chunks`**: Cluster a collection of text documents or chunks into K topic groups based on TF-IDF representation
- **`extract_cluster_topic_keywords`**: Extract top TF-IDF keywords characterizing a cluster group

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.embedding_cluster.cluster_text_chunks', {'texts': '<texts>', 'num_clusters': '<num_clusters>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.embedding_cluster
harness plugin enable domain.embedding_cluster
```

## ⚡ Available Entrypoints & Skills
- **`cluster_text_chunks(texts: array, num_clusters: integer)`**
  Cluster a collection of text documents or chunks into K topic groups based on TF-IDF representation
- **`extract_cluster_topic_keywords(cluster_texts: array, top_n: integer)`**
  Extract top TF-IDF keywords characterizing a cluster group