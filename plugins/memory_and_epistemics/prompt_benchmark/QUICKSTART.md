# Quick Start Guide: `domain.prompt_benchmark` (v1.0.0)

> LLM output evaluation, BLEU/ROUGE ngram similarity scoring, and regression benchmark suite

## 🎯 When to Use
Use this plugin when you need capabilities related to `general`.

Common trigger intents:
- **`score_text_similarity_bleu_rouge`**: Compute token precision (BLEU-1, BLEU-2) and recall/F1 (ROUGE-1, ROUGE-L) between reference and candidate text
- **`evaluate_model_outputs`**: Run automated evaluation over a batch of prompt test cases against criteria (exact match, contains keywords, regex, length)
- **`generate_regression_matrix`**: Compare benchmark scores across multiple prompt versions or model runs

## 🛠️ How to Use (Agent & User)
### Python / Runtime Tool Call:
```python
result = await runtime.tools.invoke('domain.prompt_benchmark.score_text_similarity_bleu_rouge', {'reference': '<reference>', 'candidate': '<candidate>'})
```

### CLI Quick Action:
```powershell
harness tool list --provider domain.prompt_benchmark
harness plugin enable domain.prompt_benchmark
```

## ⚡ Available Entrypoints & Skills
- **`score_text_similarity_bleu_rouge(reference: string, candidate: string)`**
  Compute token precision (BLEU-1, BLEU-2) and recall/F1 (ROUGE-1, ROUGE-L) between reference and candidate text
- **`evaluate_model_outputs(test_cases: array)`**
  Run automated evaluation over a batch of prompt test cases against criteria (exact match, contains keywords, regex, length)
- **`generate_regression_matrix(runs: array)`**
  Compare benchmark scores across multiple prompt versions or model runs