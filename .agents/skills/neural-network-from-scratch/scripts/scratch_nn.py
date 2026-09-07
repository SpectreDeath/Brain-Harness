# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "numpy",
#     "pyyaml",
# ]
# ///
"""
Slotted, type-safe NumPy 2-layer Neural Network and XOR solver.
Adheres to PEP 723, ScriptHygieneRule (zero input() calls), and RelocatableScriptsRule.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml

# Canonical XOR Dataset
XOR_X = np.array(
    [
        [0.0, 0.0],
        [0.0, 1.0],
        [1.0, 0.0],
        [1.0, 1.0],
    ],
    dtype=np.float64,
)

XOR_Y = np.array(
    [
        [0.0],
        [1.0],
        [1.0],
        [0.0],
    ],
    dtype=np.float64,
)


def sigmoid(x: np.ndarray) -> np.ndarray:
    """Numerically safe sigmoid activation."""
    return 1.0 / (1.0 + np.exp(-np.clip(x, -500.0, 500.0)))


def sigmoid_derivative(a: np.ndarray) -> np.ndarray:
    """Derivative of sigmoid given output activation a = sigmoid(z)."""
    return a * (1.0 - a)


def tanh_derivative(a: np.ndarray) -> np.ndarray:
    """Derivative of tanh given output activation a = tanh(z)."""
    return 1.0 - (a**2)


def binary_cross_entropy(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    epsilon: float = 1e-8,
) -> float:
    """Binary cross-entropy loss with numerical stability epsilon floor."""
    clipped_pred = np.clip(y_pred, epsilon, 1.0 - epsilon)
    loss = -np.mean(
        y_true * np.log(clipped_pred) + (1.0 - y_true) * np.log(1.0 - clipped_pred)
    )
    return float(loss)


@dataclass(slots=True)
class TrainingMetrics:
    initial_loss: float
    final_loss: float
    epochs: int
    converged: bool
    predictions: list[float]
    ground_truth: list[float]
    accuracy: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TwoLayerNet:
    """Canonical 2-layer neural network implemented in pure NumPy."""

    __slots__ = ("w1", "b1", "w2", "b2", "lr", "eps")

    def __init__(
        self,
        input_dim: int = 2,
        hidden_dim: int = 4,
        output_dim: int = 1,
        learning_rate: float = 0.1,
        epsilon: float = 1e-8,
        seed: int | None = 42,
    ) -> None:
        if seed is not None:
            np.random.seed(seed)
        self.w1 = np.random.randn(input_dim, hidden_dim)
        self.b1 = np.zeros((1, hidden_dim))
        self.w2 = np.random.randn(hidden_dim, output_dim)
        self.b2 = np.zeros((1, output_dim))
        self.lr = learning_rate
        self.eps = epsilon

    def forward(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Executes forward propagation returning intermediate linear combinations and activations."""
        z1 = x @ self.w1 + self.b1
        a1 = np.tanh(z1)
        z2 = a1 @ self.w2 + self.b2
        a2 = sigmoid(z2)
        return z1, a1, z2, a2

    def backward(
        self,
        x: np.ndarray,
        y: np.ndarray,
        a1: np.ndarray,
        a2: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Calculates analytical chain-rule gradients."""
        n = len(x)
        dz2 = a2 - y
        dw2 = (a1.T @ dz2) / n
        db2 = np.mean(dz2, axis=0, keepdims=True)

        da1 = dz2 @ self.w2.T
        dz1 = da1 * (1.0 - a1**2)
        dw1 = (x.T @ dz1) / n
        db1 = np.mean(dz1, axis=0, keepdims=True)

        return dw1, db1, dw2, db2

    def update(
        self,
        dw1: np.ndarray,
        db1: np.ndarray,
        dw2: np.ndarray,
        db2: np.ndarray,
    ) -> None:
        """Applies gradient descent step."""
        self.w2 -= self.lr * dw2
        self.b2 -= self.lr * db2
        self.w1 -= self.lr * dw1
        self.b1 -= self.lr * db1

    def train_xor(
        self,
        epochs: int = 10000,
        verbose_interval: int = 0,
    ) -> TrainingMetrics:
        """Trains network on the XOR dataset and captures convergence metrics."""
        x, y = XOR_X, XOR_Y
        _, _, _, a2_init = self.forward(x)
        initial_loss = binary_cross_entropy(y, a2_init, self.eps)

        for epoch in range(epochs):
            _, a1, _, a2 = self.forward(x)
            dw1, db1, dw2, db2 = self.backward(x, y, a1, a2)
            self.update(dw1, db1, dw2, db2)

            if verbose_interval > 0 and epoch % verbose_interval == 0:
                current_loss = binary_cross_entropy(y, a2, self.eps)
                print(f"Epoch {epoch:5d} | Loss: {current_loss:.4f}")

        _, _, _, a2_final = self.forward(x)
        final_loss = binary_cross_entropy(y, a2_final, self.eps)
        preds = a2_final.flatten().tolist()
        ground_truth = y.flatten().tolist()
        binary_preds = (a2_final > 0.5).astype(float)
        accuracy = float(np.mean(binary_preds == y))
        converged = bool(final_loss < initial_loss and accuracy == 1.0)

        return TrainingMetrics(
            initial_loss=initial_loss,
            final_loss=final_loss,
            epochs=epochs,
            converged=converged,
            predictions=[round(p, 4) for p in preds],
            ground_truth=ground_truth,
            accuracy=accuracy,
        )

    def predict(self, x: np.ndarray) -> np.ndarray:
        """Returns raw probabilities for input tensor."""
        _, _, _, a2 = self.forward(x)
        return a2


def load_config() -> dict[str, Any]:
    """Loads default configuration relative to script location."""
    script_dir = Path(__file__).resolve().parent
    cfg_path = script_dir.parent / "config.default.yaml"
    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {
        "random_seed": 42,
        "default_learning_rate": 0.1,
        "default_epochs": 10000,
        "epsilon": 1e-8,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic CLI for neural-network-from-scratch operations."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: train
    p_train = subparsers.add_parser("train", help="Train XOR network with custom parameters.")
    p_train.add_argument("--epochs", type=int, default=10000, help="Training iterations.")
    p_train.add_argument("--lr", type=float, default=0.1, help="Learning rate.")
    p_train.add_argument("--seed", type=int, default=42, help="Random seed.")
    p_train.add_argument("--verbose", type=int, default=0, help="Epoch print interval.")
    p_train.add_argument("--json", action="store_true", help="Output metrics as JSON.")

    # Subcommand: verify
    p_verify = subparsers.add_parser("verify", help="Run deterministic convergence diagnostics.")
    p_verify.add_argument("--json", action="store_true", help="Output verification report as JSON.")

    args = parser.parse_args()
    config = load_config()

    if args.command == "train":
        net = TwoLayerNet(
            learning_rate=args.lr or config.get("default_learning_rate", 0.1),
            seed=args.seed or config.get("random_seed", 42),
            epsilon=config.get("epsilon", 1e-8),
        )
        metrics = net.train_xor(epochs=args.epochs, verbose_interval=args.verbose)
        if getattr(args, "json", False):
            print(json.dumps(metrics.to_dict(), indent=2))
        else:
            print(f"XOR Training Complete ({metrics.epochs} epochs):")
            print(f"  Initial Loss: {metrics.initial_loss:.4f}")
            print(f"  Final Loss:   {metrics.final_loss:.4f}")
            print(f"  Accuracy:     {metrics.accuracy * 100:.1f}%")
            print(f"  Predictions:  {metrics.predictions}")
            print(f"  Ground Truth: {metrics.ground_truth}")
            print(f"  Status:       {'CONVERGED' if metrics.converged else 'FAILED'}")
        return 0 if metrics.converged else 1

    elif args.command == "verify":
        net = TwoLayerNet(
            learning_rate=config.get("default_learning_rate", 0.1),
            seed=config.get("random_seed", 42),
            epsilon=config.get("epsilon", 1e-8),
        )
        metrics = net.train_xor(epochs=config.get("default_epochs", 10000), verbose_interval=0)
        report = {
            "name": "neural-network-from-scratch-xor-verification",
            "passed": metrics.converged,
            "initial_loss": round(metrics.initial_loss, 4),
            "final_loss": round(metrics.final_loss, 4),
            "loss_decreased": bool(metrics.final_loss < metrics.initial_loss),
            "accuracy": metrics.accuracy,
            "predictions": metrics.predictions,
        }
        if getattr(args, "json", False):
            print(json.dumps(report, indent=2))
        else:
            status = "PASS" if report["passed"] else "FAIL"
            print(f"[{status}] XOR Convergence Diagnostic:")
            print(f"  Loss: {report['initial_loss']} -> {report['final_loss']} (Decreased: {report['loss_decreased']})")
            print(f"  Accuracy: {report['accuracy'] * 100:.1f}%")
        return 0 if metrics.converged else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
