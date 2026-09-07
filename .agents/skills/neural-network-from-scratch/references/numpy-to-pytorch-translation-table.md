# NumPy to PyTorch Translation & Architecture Equivalence Table

This reference guide provides an authoritative mapping between scratch NumPy mathematical matrix operations and modular PyTorch (`torch.nn`) production abstractions.

---

## Direct Equivalence Mapping

| Pipeline Phase | NumPy Scratch Implementation | PyTorch (`torch.nn`) Equivalent |
|---|---|---|
| **Data Representation** | `X = np.array([...], dtype=float)` | `X = torch.tensor([...], dtype=torch.float32)` |
| **Layer Parameters** | `W1 = np.random.randn(2, 4); b1 = np.zeros((1, 4))` | `layer1 = nn.Linear(in_features=2, out_features=4)` |
| **Forward Linear Pass** | `z1 = X @ W1 + b1` | `z1 = layer1(X)` |
| **Activation ($\tanh$)** | `a1 = np.tanh(z1)` | `a1 = torch.tanh(z1)` or `nn.Tanh()(z1)` |
| **Activation ($\sigma$)** | `a2 = 1 / (1 + np.exp(-z2))` | `a2 = torch.sigmoid(z2)` or `nn.Sigmoid()(z2)` |
| **Binary Cross-Entropy** | `-np.mean(y * np.log(a2 + eps) + (1-y) * np.log(1-a2 + eps))` | `criterion = nn.BCELoss(); loss = criterion(a2, y)` |
| **Gradient Calculation** | Explicit chain rule: `dz2 = a2 - y; dW2 = (a1.T @ dz2) / N` | Automatic differentiation: `loss.backward()` |
| **Gradient Buffer Reset** | Automatic (transient local gradient variables) | Explicit: `optimizer.zero_grad()` |
| **Parameter Update** | Manual step: `W2 -= lr * dW2; b2 -= lr * db2` | Optimizer step: `optimizer.step()` via `optim.SGD` |
| **Inference Mode** | Function call `predict(X)` without gradient steps | `with torch.no_grad(): output = model(X)` |

---

## Canonical PyTorch Equivalence Implementation

```python
import torch
import torch.nn as nn
import torch.optim as optim

class XORNet(nn.Module):
    """Modular PyTorch equivalent of the canonical 2-layer NumPy XOR network."""
    def __init__(self, input_dim: int = 2, hidden_dim: int = 4, output_dim: int = 1):
        super().__init__()
        self.layer1 = nn.Linear(input_dim, hidden_dim)
        self.tanh = nn.Tanh()
        self.layer2 = nn.Linear(hidden_dim, output_dim)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        h = self.tanh(self.layer1(x))
        out = self.sigmoid(self.layer2(h))
        return out

# Training Loop Pattern
def train_pytorch_xor(epochs: int = 10000, lr: float = 0.1) -> XORNet:
    X = torch.tensor([[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]])
    y = torch.tensor([[0.0], [1.0], [1.0], [0.0]])

    model = XORNet()
    criterion = nn.BCELoss()
    optimizer = optim.SGD(model.parameters(), lr=lr)

    for epoch in range(epochs):
        optimizer.zero_grad()
        predictions = model(X)
        loss = criterion(predictions, y)
        loss.backward()
        optimizer.step()

    return model
```

---

## Architecture Selection Heuristics

```
                         [Architecture Decision]
                                    │
           Is your goal pedagogical transparency, pure math verification,
           or deployment on zero-dependency lightweight environments?
                        ├── YES ──► Use NumPy Scratch Implementation
                        │           - No C++/CUDA binary dependencies
                        │           - Full line-by-line derivative visibility
                        │           - Instant cold-start execution
                        └── NO  ──► Use PyTorch (torch.nn) Architecture
                                    - Reverse-mode autograd for arbitrary DAGs
                                    - Hardware acceleration (CUDA, ROCm, MPS)
                                    - Rich ecosystem (TorchScript, ONNX, TensorRT)
```
