# Phase 8 — Rule Classifier vs Ground Truth Summary

Evaluated **14** repositories: **2/14** correct (**accuracy = 0.1429**).

## 3x3 Confusion Matrix (rows = Ground Truth, cols = Predicted)

| Ground Truth \ Predicted | `plugin` | `ki_only` | `skip` |
|---|---:|---:|---:|
| `plugin` | 2 | 7 | 1 |
| `ki_only` | 2 | 0 | 2 |
| `skip` | 0 | 0 | 0 |

## Per-Repo Predictions

| Repo | Truth | Predicted | Match | Dominant Unit | Lang / Pkg / Tests / README / arXiv |
|---|---|---|---|---|---|
| `adk-docs` | `plugin` | `ki_only` | MISS | `adk-docs` (snapshot:google_portfolio_root) | docs_or_config / requirements / tests=False / readme=True / arxiv=False |
| `adk-python` | `plugin` | `plugin` | OK | `adk-python` (snapshot:google_portfolio_root) | python / pyproject / tests=True / readme=True / arxiv=False |
| `adk-web` | `plugin` | `ki_only` | MISS | `adk-web` (snapshot:google_portfolio_root) | typescript / npm / tests=True / readme=True / arxiv=False |
| `earthengine-api` | `plugin` | `ki_only` | MISS | `earthengine-api` (snapshot:google_portfolio_root) | typescript / npm / tests=False / readme=True / arxiv=False |
| `google-research-master` | `ki_only` | `plugin` | MISS | `imp` (snapshot:grm) | python / requirements / tests=True / readme=True / arxiv=True |
| `gvisor` | `ki_only` | `skip` | MISS | `runsc` (snapshot:gvisor) | go / none / tests=True / readme=False / arxiv=False |
| `harness2` | `plugin` | `ki_only` | MISS | `harness2` (snapshot:google_portfolio_root) | python / pyproject / tests=False / readme=True / arxiv=True |
| `magika` | `plugin` | `ki_only` | MISS | `magika` (snapshot:google_portfolio_root) | docs_or_config / go_mod / tests=False / readme=True / arxiv=False |
| `mantis` | `plugin` | `plugin` | OK | `mantis` (snapshot:google_portfolio_root) | python / requirements / tests=True / readme=True / arxiv=False |
| `perfetto` | `plugin` | `skip` | MISS | `perfetto` (snapshot:google_portfolio_root) | python / none / tests=False / readme=True / arxiv=False |
| `styleguide` | `plugin` | `ki_only` | MISS | `styleguide` (snapshot:google_portfolio_root) | typescript / none / tests=False / readme=True / arxiv=False |
| `tunix-main` | `plugin` | `ki_only` | MISS | `tunix-main` (snapshot:google_portfolio_root) | python / pyproject / tests=False / readme=True / arxiv=True |
| `airllm` | `ki_only` | `plugin` | MISS | `air_llm` (snapshot:airllm) | python / setup_py / tests=True / readme=False / arxiv=False |
| `airllm-plus` | `ki_only` | `skip` | MISS | `pack` (snapshot:airllm_plus) | python / none / tests=False / readme=False / arxiv=False |
