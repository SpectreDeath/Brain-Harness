# Google Research `dp_sgd_clipping`: In-Place Fast Gradient Norm, Ghost Norm & FFT Dispatch

## 1. Context & Provenance

- **Upstream Repository**: `https://github.com/google-research/google-research` (`dp_sgd_clipping/` subproject, 5 files)
- **Snapshot Reference**: `google-research-master` (archive snapshot, non-git)
- **Publication / Reference**: *Efficient Gradient Clipping Methods in DP-SGD for Convolution Models* (W. Kong, M. Ribero, G. Velegkas; `https://arxiv.org/abs/2205.10683`)
- **Primary Verified Sources**:
  - `dp_sgd_clipping/README.md` (`L1-L38`)
  - `dp_sgd_clipping/fast_cnn_grad_norm.py` (`L31-L536`, sha256 `2abe8df40e02e49bf04b75c4e9b1b817995d37bf325f462825f7bdc7178cab4c`)
  - `dp_sgd_clipping/fast_cnn_grad_norm_test.py` (`L1-L316`)

---

## 2. Core Problem & Architectural Thesis

Per-sample gradient clipping in Differentially Private SGD (`DP-SGD`) requires computing exact per-example gradient norms $\|\nabla_\theta \ell_i\|_2$ before clipping and noise injection. For 1D convolutional layers, naively unfolding all input sliding windows allocates a large intermediate tensor per example. Because each candidate algorithm dominates in a different regime of input dimension, kernel size, stride, and channel counts, `dp_sgd_clipping` provides three memory-bounded implementations plus an automatic asymptotic cost selector.

---

## 3. Verified Implementation Invariants

### A. Validation & Three Incomparable Norm Kernels (`fast_cnn_grad_norm.py` `L31-L291`)
- `_check_value_and_shape_of_arguments(input_matrix, partial_gradient, kernel_size, stride)` (`L31-L58`) validates 2D shapes, non-empty dimensions, positive integer parameters, and exact CNN output width equality $\lfloor (D_{\text{in}} - K) / S + 1 \rfloor = D_{\text{out}}$.
- `in_place_fast_grad_norm` (`L61-L110`) iterates per input channel using `np.lib.stride_tricks.sliding_window_view(..., window_shape=(kernel_size,))[::stride]` paired with `np.tensordot` over partial gradients without materializing unfolded tensors.
- `in_place_ghost_norm` (`L157-L218`) evaluates the ghost-norm Gramian Frobenius product $\langle \sum_i U(x[i])U(x[i])^T, \sum_k g[k]g[k]^T \rangle$ across output coordinate pairs $(j_1, j_2)$.
- `in_place_norm_fft` (`L221-L291`) embeds strided partial gradients into `np.zeros(input_dimension)` and computes circulant convolutions using `np.fft.fft` / `np.fft.ifft`, summing squared real amplitudes over `[0:kernel_size]`.

### B. Regime-Aware Dispatch (`fast_cnn_grad_norm.py` `L113-L154`, `L430-L536`)
- `grad_norm_computation_selector` (`L430-L536`) computes asymptotic cost estimates weighted by empirical constants (`constant_fft = 20`, `constant_in_place_ghost = 6`, `constant_in_place_fast_grad = 4`, `constant_naive_ghost = 3`, `constant_naive_fast_grad = 2`) and passes boolean predicates into `_select_method` (`L113-L154`), falling back between memory-efficient vs naive implementations when `memory_efficient_implementation_required` is toggled.

---

## 4. Applicability to Brain Harness & Anti-Patterns

- **Harness Seam Targets**: Any batch analytics or ML training plugin computing per-example gradient/sensitivity norms should separate exact shape invariants (`_check_value_and_shape_of_arguments`) from execution-strategy dispatch so memory-bounded vs speed-first kernels remain swappable without changing callers.
- **Anti-Patterns**:
  - **Do not hardcode a single per-sample Jacobian strategy** across all tensor regimes; asymptotic crossovers depend strongly on `output_dimension^2` vs `input_dimension * log(input_dimension)`.
  - **Do not silence shape mismatches** — assert exact stride/kernel output-dimension identities before inner loops execute.
