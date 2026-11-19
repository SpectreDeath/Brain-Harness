# Google Research `perturbations`: Differentiable Perturbed Optimizers & Fenchel-Young Losses

## 1. Context & Provenance

- **Upstream Repository**: `https://github.com/google-research/google-research` (`perturbations/` subproject, 13 files)
- **Snapshot Reference**: `google-research-master` (archive snapshot, non-git)
- **Publication**: *Learning with Differentiable Perturbed Optimizers* (NeurIPS 2020; Berthet et al., `https://arxiv.org/abs/2002.08676`)
- **Primary Verified Sources**:
  - `perturbations/README.md` (`L1-L284`)
  - `perturbations/perturbations.py` (`L47-L184`, sha256 `221616350abc45322871e066c6419bf0aff300a6f82fdb159705134f263b4e46`)
  - `perturbations/fenchel_young.py` (`L27-L99`, sha256 `30dc3e3ce0d6191649a3192ba81de408bb52ef4b86d038f61c4f1554b492909d`)

---

## 2. Core Problem & Architectural Thesis

Discrete combinatorial solvers (e.g., `argmax`, sorting/ranking, shortest paths) yield zero or undefined gradients almost everywhere. `perturbations` transforms any linear-program-style solver `func(theta)` into a smooth differentiable operator via stochastic Monte-Carlo perturbations (`theta + sigma * noise`) paired with an exact integration-by-parts `@tf.custom_gradient` backward pass—requiring zero solver rewrite.

---

## 3. Verified Implementation Invariants

### A. Noise Distributions & `@perturbed` Custom-Gradient Wrapper (`perturbations.py` `L47-L184`)
- `sample_noise_with_gradients(noise, shape)` (`L47-L78`) supports `'normal'` (returns `(Z, Z)`) and `'gumbel'` (returns `(G, 1 - exp(-G))`) aligned with $\nabla_z \log \mu(z)$ for integration by parts; unsupported noise strings raise `ValueError`.
- `@perturbed(func=None, num_samples=1000, sigma=0.05, noise='normal', batched=True)` (`L81-L184`) works both as a decorator (`functools.partial`) and direct function wrapper:
  1. Validates rank `>= 2` when `batched=True`, or inserts/strips dummy batch axis when `batched=False`.
  2. Tiles `[N, B, ...]` perturbed inputs, flattens `(N*B, ...)` so arbitrary user `func` runs perturbation-agnostically, and averages outputs over sample axis `0`.
  3. Implements `grad(dy)` cleanly using two `tf.einsum` contractions divided by `sigma * num_samples`.

### B. Direct Fenchel-Young Surrogate Gradient (`fenchel_young.py` `L27-L99`)
- `FenchelYoungLoss` (`L27-L99`, `@gin.configurable`) evaluates `diff = self.perturbed(theta) - y_true` (sign-flipped when `maximize=False`) and defines a `@tf.custom_gradient` whose backward gradient directly returns `dy * diff`, avoiding Hessian/second-order noise estimates in supervised discrete optimization.

---

## 4. Applicability to Brain Harness & Anti-Patterns

- **Harness Seam Targets**: Optimization/routing plugins selecting discrete top-k tool subsets, DAG paths, or sparse pruning masks can borrow this decorator pattern (`@perturbed` decoupling black-box discrete solver execution from custom gradient estimation) and direct primal-dual residuals (`perturbed(theta) - y_true`).
- **Anti-Patterns**:
  - **Do not apply `@perturbed` to non-linear-program solvers** — the docstring explicitly warns that gradient guarantees only hold when `func` solves a linear program on a polytope.
  - **Do not differentiate through smoothed discrete outputs with generic MSE** when ground-truth primal targets exist — use the Fenchel-Young direct residual gradient instead.
