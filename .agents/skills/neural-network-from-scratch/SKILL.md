---
name: neural-network-from-scratch
description: "Construct, train, diagnose, and translate mathematical feedforward neural networks from NumPy matrix calculus to modular PyTorch architectures. Use when building neural networks from scratch, deriving analytical backpropagation gradients, implementing XOR classification, preventing numerical instability in cross-entropy loss, or migrating mathematical prototypes to torch.nn modules."
---

# Neural Network from Scratch

`neural-network-from-scratch` is a deep-module agent skill for engineering, training, diagnosing, and migrating mathematical neural networks. Distilled from Eva J Patel's foundational curriculum, it operationalizes matrix calculus, forward propagation, analytical backpropagation derivatives, numerical stability safeguards, and modular translation to PyTorch.

See [CARD.md](CARD.md) for companion quick reference cards, CLI commands, and lifecycle matrices.

---

## Core Operational Pillars

Every scratch neural network engagement enforces three architectural pillars:

1. **The Visual Brief** — Interactive HTML briefs generated in `%TEMP%/neural-network-from-scratch-<timestamp>.html` with live Mermaid.js mathematical DAG diagrams, tensor dimension contracts, and convergence diagnostic scorecards.
2. **The Mandatory Checkpoint** — Human-in-the-loop validation via `implementation_plan.md` with `RequestFeedback: true`. The agent must halt and await user confirmation before modifying network topologies, updating hyperparameters, or executing extended training loops.
3. **Behavioral Boundaries & Anti-Patterns** — Rigid negative guardrails that reject unclamped logarithms, misaligned inner matrix multiplications, zero-variance initializations, and black-box autograd shortcuts.

---

## Authoritative Tooling & Execution Seams

The skill provides deterministic, non-interactive execution engines in `scripts/`:

- `python scripts/scratch_nn.py train [--epochs 10000] [--lr 0.1] [--seed 42] [--json]`: Trains the 2-layer network on the XOR dataset and outputs convergence metrics.
- `python scripts/scratch_nn.py verify [--json]`: Executes deterministic convergence diagnostics asserting loss reduction and 100% classification accuracy.

Consult co-located architectural reference guides in `references/`:
- When deriving chain-rule partial derivatives or verifying analytical equations, consult [`backpropagation-calculus-guide.md`](references/backpropagation-calculus-guide.md) for full step-by-step calculus proofs, matrix dimensions, and the $\tanh'$ derivative identity.
- When migrating verified mathematical algorithms to production deep learning pipelines, consult [`numpy-to-pytorch-translation-table.md`](references/numpy-to-pytorch-translation-table.md) for direct side-by-side mapping to `torch.nn.Module`, autograd, and optimizer abstractions.

---

## Execution Stages

### Stage 1: Dimension & Parameter Topology Framing

Establish network topology, define layer dimension boundaries, and initialize parameter matrices with reproducible pseudorandom seeds.

#### Procedure
1. Define input dimensionality $D_{in} = 2$, hidden neuron count $D_h = 4$, and output dimensionality $D_{out} = 1$.
2. Seed the pseudorandom generator (`np.random.seed(42)`) to ensure deterministic training runs.
3. Initialize weight matrices using Gaussian distributions (`np.random.randn`):
   - First layer weights $W_1$ with shape $(D_{in}, D_h) = (2, 4)$.
   - Second layer weights $W_2$ with shape $(D_h, D_{out}) = (4, 1)$.
4. Initialize bias vectors to zeros (`np.zeros`):
   - Hidden bias $b_1$ with shape $(1, D_h) = (1, 4)$.
   - Output bias $b_2$ with shape $(1, D_{out}) = (1, 1)$.
5. Verify inner matrix dimension alignment: ensure inner dimensions match for dot products $X \cdot W_1$ and $a_1 \cdot W_2$.

> **Completion Gate**: `Weight and bias matrix shapes verified with inner dimension alignment`

---

### Stage 2: Forward Propagation & Activation Calculus

Compute intermediate linear combinations and non-linear activations across both layers.

#### Procedure
1. Compute the hidden layer linear combination: $z_1 = X W_1 + b_1$ with shape $(N, 4)$.
2. Apply the non-linear hyperbolic tangent activation function: $a_1 = \tanh(z_1)$ mapping values into $(-1, 1)$.
3. Compute the output layer linear combination: $z_2 = a_1 W_2 + b_2$ with shape $(N, 1)$.
4. Apply the Sigmoid activation function: $a_2 = \sigma(z_2) = \frac{1}{1 + e^{-z_2}}$ mapping values into $(0, 1)$ probability space.
5. Clip extreme exponent values inside Sigmoid if necessary to prevent numerical floating point overflow.

> **Completion Gate**: `Forward linear combinations and non-linear activations computed`

---

### Stage 3: Loss Function Formulation & Error Measurement

Quantify network prediction errors using Binary Cross-Entropy (BCE) fortified with numerical stability floors.

#### Procedure
1. Formulate Binary Cross-Entropy across $N$ training examples:
   $$L = -\frac{1}{N} \sum \left[ y \ln(a_2) + (1 - y) \ln(1 - a_2) \right]$$
2. Protect against $\ln(0)$ infinity errors by applying an epsilon floor $\epsilon = 10^{-8}$:
   $$L = -\frac{1}{N} \sum \left[ y \ln(a_2 + 10^{-8}) + (1 - y) \ln(1 - a_2 + 10^{-8}) \right]$$
3. Measure the initial loss at epoch 0 (for XOR with seed 42, initial loss is $\approx 0.70$).
4. Establish convergence criteria: require final loss $< 0.05$ and 100% classification accuracy on XOR targets.

> **Completion Gate**: `Binary cross-entropy loss computed with numerical stability epsilon floor`

---

### Stage 4: Chain-Rule Backpropagation & Parameter Updates

Derive and compute analytical gradients across all parameters, updating weights via gradient descent.

#### Procedure
1. Compute the output pre-activation error gradient: $dz_2 = a_2 - y$ with shape $(N, 1)$ per `backpropagation-calculus-guide.md`.
2. Compute output parameter gradients:
   - $dW_2 = \frac{1}{N} a_1^T dz_2$ with shape $(4, 1)$.
   - $db_2 = \frac{1}{N} \sum dz_2$ with shape $(1, 1)$.
3. Backpropagate error gradient to hidden layer activations: $da_1 = dz_2 W_2^T$ with shape $(N, 4)$.
4. Compute hidden pre-activation gradient using the $\tanh'$ derivative identity $(1 - a_1^2)$:
   $$dz_1 = da_1 \odot (1 - a_1^2) \quad \text{with shape } (N, 4)$$
5. Compute hidden parameter gradients:
   - $dW_1 = \frac{1}{N} X^T dz_1$ with shape $(2, 4)$.
   - $db_1 = \frac{1}{N} \sum dz_1$ with shape $(1, 4)$.
6. Apply gradient descent update scaled by learning rate $\eta = 0.1$:
   $$W_2 \leftarrow W_2 - \eta dW_2, \quad b_2 \leftarrow b_2 - \eta db_2$$
   $$W_1 \leftarrow W_1 - \eta dW_1, \quad b_1 \leftarrow b_1 - \eta db_1$$

> **Completion Gate**: `Analytical chain-rule gradients computed and parameter update applied`

---

### Stage 5: Modular PyTorch Translation & Convergence Diagnostics

Verify end-to-end training convergence on XOR and translate verified NumPy logic into modular PyTorch architecture per `numpy-to-pytorch-translation-table.md`.

#### Procedure
1. Execute full training loop for 10,000 epochs via `python scripts/scratch_nn.py train --epochs 10000`.
2. Verify convergence: assert final loss is strictly less than initial loss, and assert predicted XOR truth table matches $\{0, 1, 1, 0\}$ with $100\%$ accuracy.
3. Translate NumPy arrays and manual gradients into idiomatic `torch.nn.Module` subclasses implementing `nn.Linear`, `nn.Tanh`, `nn.Sigmoid`, and `torch.optim.SGD`.
4. Run automated diagnostic verification via `python scripts/scratch_nn.py verify`.

> **Completion Gate**: `XOR training convergence verified with 100% accuracy and PyTorch equivalent translated`

---

## Anti-Patterns

- **Unclamped Logarithm Loss Evaluation** — Computing `np.log(a2)` directly without adding $\epsilon = 10^{-8}$, causing catastrophic `NaN` or `-inf` crashes when model predictions approach boundary states.
- **Transposed Dimension Mismatch** — Multiplying tensors with misaligned inner dimensions (e.g. attempting `X @ dz1` instead of `X.T @ dz1`), causing execution crashes or silent incorrect broadcasts.
- **Monotonic Loss Assertion Assumption** — Expecting XOR binary cross-entropy loss to decrease strictly monotonically on every epoch, causing false-positive test failures during normal optimization oscillation.
- **Missing Gradient Batch Normalization** — Omitting the division by batch size $N$ in $dW_1 = (X^T dz_1) / N$, causing effective gradient scale to explode when changing dataset sizes.
- **Symmetric Weight Initialization** — Initializing weight matrices with all zeros instead of random Gaussian numbers, preventing hidden neurons from breaking symmetry during gradient descent.
- **Untethered PyTorch Autodiff Dependency** — Depending prematurely on complex autograd libraries for simple algorithmic problems where pure NumPy matrix calculus provides superior transparency and zero dependencies.
