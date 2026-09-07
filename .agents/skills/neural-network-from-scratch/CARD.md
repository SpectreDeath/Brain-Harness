# Skill Summary Card: `neural-network-from-scratch`

```
┌────────────────────────────────────────────────────────┐
│               SKILL SUMMARY CARD                       │
├────────────────────────────────────────────────────────┤
│ SKILL:       neural-network-from-scratch               │
│ Name:        neural-network-from-scratch               │
│ Category:    data_engineering / deep_learning          │
│ Invocation:  /neural-network-from-scratch              │
│ Triggers:    "build neural network from scratch",      │
│              "backpropagation calculus in Python",     │
│              "NumPy neural network XOR",               │
│              "migrate scratch NN to PyTorch"           │
│ Version:     1.0.0                                     │
│ Isolation:   in-process                                │
│ Provides:    "service.neural_network_from_scratch"     │
├────────────────────────────────────────────────────────┤
│ Target:      Construct, train, diagnose, and translate │
│              mathematical feedforward neural networks  │
│              from NumPy calculus to PyTorch modules.   │
└────────────────────────────────────────────────────────┘
```

---

## The 5-Stage Neural Network Lifecycle Loop

| Stage | Objective | Primary Artifact / Output | Completion Gate |
|---|---|---|---|
| **1. Dimension & Topology Framing** | Dimension matrix shapes, initialize random weights and zero bias | Topology Spec & Tensor Shapes | `Weight and bias matrix shapes verified` |
| **2. Forward Propagation Calculus** | Compute linear combinations and non-linear activations ($\tanh$, $\sigma$) | Forward Propagation Tensors | `Forward activation tensor values calculated` |
| **3. Loss Formulation & Stability Floor** | Compute Binary Cross-Entropy with $\epsilon = 10^{-8}$ stability floor | Scalar Loss & Metric Output | `BCE loss evaluated with stability epsilon` |
| **4. Chain-Rule Backpropagation** | Derive analytical gradients ($dz_2, dW_2, da_1, dz_1, dW_1$) and update | Gradient Matrices & Updates | `Analytical gradients derived and applied` |
| **5. PyTorch Migration & Diagnostics** | Translate NumPy math to `nn.Module` and verify XOR convergence | Modular PyTorch Model | `XOR convergence verified with 100% accuracy` |

---

## Authoritative Tooling Seams

```bash
# 1. Train XOR network with custom parameters
python scripts/scratch_nn.py train --epochs 10000 --lr 0.1 [--verbose 1000] [--json]

# 2. Run deterministic convergence diagnostics
python scripts/scratch_nn.py verify [--json]
```

---

## Deep Reference Blueprints

- [`backpropagation-calculus-guide.md`](references/backpropagation-calculus-guide.md) — Step-by-step chain-rule derivation of analytical gradients and $\tanh'$ identity.
- [`numpy-to-pytorch-translation-table.md`](references/numpy-to-pytorch-translation-table.md) — Side-by-side equivalence table mapping scratch NumPy operations to `torch.nn.Module`.

---

## Tri-Pillar Architecture Cheat Sheet

### 1. Dimension Consistency Invariant
Always verify tensor inner dimensions before multiplication: $X(N \times 2) \times W_1(2 \times 4) \to z_1(N \times 4)$, and $a_1^T(4 \times N) \times dz_2(N \times 1) \to dW_2(4 \times 1)$.

### 2. Numerical Stability Floor
Never evaluate $\ln(a_2)$ directly. Always clip probabilities with $\epsilon = 10^{-8}$ to prevent catastrophic $\text{NaN}$ loss collapse during early training.

### 3. Non-Monotonic Loss Trajectory
XOR binary cross-entropy loss oscillates slightly during gradient descent exploration before collapsing toward zero; evaluate convergence by comparing final loss to initial loss and verifying $100\%$ classification accuracy.

---

## Mandatory Invariants Checklist

- [ ] **Matrix Dimension Consistency**: Assert tensor inner dimensions match before matrix dot products ($X \cdot W_1$, $a_1 \cdot W_2$).
- [ ] **Numerical Stability Floor**: Always add $\epsilon = 10^{-8}$ inside logarithm arguments for binary cross-entropy loss.
- [ ] **Analytical Gradients**: Compute analytical partial derivatives via chain rule without reliance on black-box autodiff.
- [ ] **Batch Gradient Scaling**: Always divide parameter gradients $dW_1, dW_2$ by dataset batch size $N$.
- [ ] **Symmetry Breaking**: Initialize weight matrices randomly ($W \sim \mathcal{N}(0, 1)$) rather than all zeros.
- [ ] **XOR Convergence Verification**: Assert final loss $< 0.05$ and classification accuracy $= 100\%$ across all 4 XOR pairs.
