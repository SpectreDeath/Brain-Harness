# Latent Programmer: Discrete VQ-VAE Program Plans & Bypass-Preventing Pretraining

## Provenance
- **Upstream Repository**: `https://github.com/google-research/google-research` (`latent_programmer/`)
- **Paper**: `https://arxiv.org/abs/2012.00377` (ICML 2021)
- **Surfaced By**: `query recommend nlp_and_llm_project [has_tests=true, has_arxiv=true, harness_learned=false, size_tier=large]`

## Key Mechanisms
1. **Bypass-Preventing Bottleneck (`latent_programmer/models/latent_models.py#L43-L218`)**:
   - `Autoencoder` downsamples target program embeddings by factor $2^c$ via strided 1D convolutions before discrete quantization.
   - During `pretrain=True`, `encoded_padding_mask` is multiplied by `0` so the decoder relies solely on quantized discrete latent tokens rather than shortcutting straight to I/O encodings.
2. **EMA Codebook Discretization (`latent_programmer/models/vqvae.py#L31-L149`)**:
   - Computes $L_2$ distances to codebook `vq_emb`, applies optional `emb_mask` for control tokens, and updates `ema_emb`/`cluster_sizes` with straight-through gradient estimation.

## Harness Relevance
- Separates coarse discrete plan generation from low-level code emission cleanly — applicable to structured multi-step planning and domain DSL synthesis.
