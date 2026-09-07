# Backpropagation Calculus & Analytical Gradients Guide

This reference guide establishes the formal mathematical derivations, matrix dimension alignments, and gradient chain-rule calculus for a 2-layer feedforward neural network trained with Binary Cross-Entropy loss.

---

## 1. Network Topology & Forward Propagation

Let $N$ denote batch size (for XOR, $N = 4$), $D_{in} = 2$ (input features), $D_h = 4$ (hidden neurons), and $D_{out} = 1$ (output targets).

### Forward Equations
1. **Hidden Layer Linear Combination**:
   $$z_1 = X W_1 + b_1 \quad \in \mathbb{R}^{N \times D_h} \quad (4 \times 4)$$
   where $X \in \mathbb{R}^{N \times D_{in}} (4 \times 2)$, $W_1 \in \mathbb{R}^{D_{in} \times D_h} (2 \times 4)$, $b_1 \in \mathbb{R}^{1 \times D_h} (1 \times 4)$ (broadcast across rows).

2. **Hidden Non-Linear Activation ($\tanh$)**:
   $$a_1 = \tanh(z_1) = \frac{e^{z_1} - e^{-z_1}}{e^{z_1} + e^{-z_1}} \quad \in \mathbb{R}^{N \times D_h} \quad (4 \times 4)$$

3. **Output Layer Linear Combination**:
   $$z_2 = a_1 W_2 + b_2 \quad \in \mathbb{R}^{N \times D_{out}} \quad (4 \times 1)$$
   where $W_2 \in \mathbb{R}^{D_h \times D_{out}} (4 \times 1)$, $b_2 \in \mathbb{R}^{1 \times D_{out}} (1 \times 1)$.

4. **Output Sigmoid Activation ($\sigma$)**:
   $$a_2 = \sigma(z_2) = \frac{1}{1 + e^{-z_2}} \quad \in \mathbb{R}^{N \times D_{out}} \quad (4 \times 1)$$

---

## 2. Loss Function & Numerical Stability Floor

For binary classification targets $y \in \{0, 1\}^{N \times 1}$, we use Binary Cross-Entropy (BCE):

$$L = -\frac{1}{N} \sum_{i=1}^N \Big[ y^{(i)} \ln(a_2^{(i)} + \epsilon) + (1 - y^{(i)}) \ln(1 - a_2^{(i)} + \epsilon) \Big]$$

### The $\epsilon = 10^{-8}$ Numerical Stability Invariant
If $a_2 \to 0$ when $y = 1$, or $a_2 \to 1$ when $y = 0$, evaluating $\ln(0)$ yields $-\infty$. When multiplied or subtracted, Python floating point arithmetic produces `NaN`. Adding $\epsilon = 10^{-8}$ bounds the logarithm input safely away from zero: $\ln(10^{-8}) \approx -18.4207$, preventing numeric explosion without distorting analytical gradients.

---

## 3. Analytical Derivation of Chain-Rule Gradients

### Step A: Output Layer Gradient ($dz_2$)
Combining the derivative of BCE loss with respect to sigmoid output $a_2$, and the derivative of sigmoid with respect to $z_2$:

$$\frac{\partial L}{\partial a_2} = -\frac{1}{N} \left( \frac{y}{a_2} - \frac{1 - y}{1 - a_2} \right) = \frac{1}{N} \frac{a_2 - y}{a_2 (1 - a_2)}$$

$$\frac{\partial a_2}{\partial z_2} = \sigma(z_2)(1 - \sigma(z_2)) = a_2(1 - a_2)$$

Applying the chain rule:
$$dz_2 = \frac{\partial L}{\partial z_2} = \frac{\partial L}{\partial a_2} \cdot \frac{\partial a_2}{\partial z_2} = a_2 - y \quad \in \mathbb{R}^{N \times 1}$$

### Step B: Layer 2 Parameter Gradients ($dW_2, db_2$)
Using $z_2 = a_1 W_2 + b_2$:

$$dW_2 = \frac{\partial L}{\partial W_2} = \frac{1}{N} a_1^T dz_2 \quad \in \mathbb{R}^{D_h \times D_{out}} \quad (4 \times 1)$$

$$db_2 = \frac{\partial L}{\partial b_2} = \frac{1}{N} \sum_{i=1}^N dz_2^{(i)} = \text{mean}(dz_2, \text{axis}=0, \text{keepdims}=\text{True}) \quad \in \mathbb{R}^{1 \times 1}$$

### Step C: Hidden Activation Gradient ($da_1$)
Backpropagating error upstream through weight matrix $W_2$:

$$da_1 = \frac{\partial L}{\partial a_1} = dz_2 W_2^T \quad \in \mathbb{R}^{N \times D_h} \quad (4 \times 4)$$

### Step D: Hidden Pre-Activation Gradient ($dz_1$)
The derivative of hyperbolic tangent $\tanh$ has the identity:
$$\frac{d}{dx} \tanh(x) = 1 - \tanh^2(x)$$

Because $a_1 = \tanh(z_1)$, the local derivative is simply $(1 - a_1^2)$. Applying element-wise Hadamard multiplication ($\odot$):

$$dz_1 = \frac{\partial L}{\partial z_1} = da_1 \odot (1 - a_1^2) \quad \in \mathbb{R}^{N \times D_h} \quad (4 \times 4)$$

### Step E: Layer 1 Parameter Gradients ($dW_1, db_1$)
Using $z_1 = X W_1 + b_1$:

$$dW_1 = \frac{\partial L}{\partial W_1} = \frac{1}{N} X^T dz_1 \quad \in \mathbb{R}^{D_{in} \times D_h} \quad (2 \times 4)$$

$$db_1 = \frac{\partial L}{\partial b_1} = \frac{1}{N} \sum_{i=1}^N dz_1^{(i)} = \text{mean}(dz_1, \text{axis}=0, \text{keepdims}=\text{True}) \quad \in \mathbb{R}^{1 \times 4}$$

---

## 4. Parameter Update Formulation

Parameters are updated along the negative gradient scaled by learning rate $\eta$:

$$W_2 \leftarrow W_2 - \eta \, dW_2, \quad b_2 \leftarrow b_2 - \eta \, db_2$$
$$W_1 \leftarrow W_1 - \eta \, dW_1, \quad b_1 \leftarrow b_1 - \eta \, db_1$$

For XOR with $\eta = 0.1$ and seed $42$, initial BCE loss starts at $\approx 0.70$ and descends to $< 0.05$ after 10,000 epochs, achieving 100% classification accuracy.
