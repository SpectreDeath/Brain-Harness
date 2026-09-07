"""
Test suite for neural-network-from-scratch skill.
Verifies activation functions, calculus derivatives, numerical stability floors,
matrix dimension alignment, and XOR convergence diagnostics.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

# Add scripts directory to sys.path for direct module import
SKILL_DIR = Path(__file__).resolve().parent.parent / ".agents" / "skills" / "neural-network-from-scratch"
SCRIPTS_DIR = SKILL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scratch_nn import (  # noqa: E402
    XOR_X,
    XOR_Y,
    TwoLayerNet,
    binary_cross_entropy,
    sigmoid,
    sigmoid_derivative,
    tanh_derivative,
)


@pytest.mark.unit
def test_sigmoid_activation_properties() -> None:
    """Verifies standard sigmoid limits and values."""
    assert np.isclose(sigmoid(np.array([0.0]))[0], 0.5)
    # Extremely large positive and negative values should be bounded in [0, 1] without overflow
    large_vals = np.array([-1000.0, 1000.0])
    res = sigmoid(large_vals)
    assert np.isclose(res[0], 0.0)
    assert np.isclose(res[1], 1.0)


@pytest.mark.unit
def test_derivative_identities() -> None:
    """Verifies mathematical identities for activation derivatives."""
    # Sigmoid derivative: a * (1 - a)
    a_sig = np.array([0.5, 0.2, 0.8])
    expected_sig_deriv = a_sig * (1.0 - a_sig)
    assert np.allclose(sigmoid_derivative(a_sig), expected_sig_deriv)

    # Tanh derivative: 1 - a^2
    a_tanh = np.array([0.0, 0.5, -0.5])
    expected_tanh_deriv = 1.0 - (a_tanh**2)
    assert np.allclose(tanh_derivative(a_tanh), expected_tanh_deriv)


@pytest.mark.unit
def test_bce_numerical_stability_floor() -> None:
    """Verifies that epsilon prevents NaN/inf on extreme prediction boundaries."""
    y_true = np.array([[1.0], [0.0]])
    # Completely opposing predictions (would cause ln(0) without epsilon)
    y_pred_bad = np.array([[0.0], [1.0]])

    loss = binary_cross_entropy(y_true, y_pred_bad, epsilon=1e-8)
    assert not np.isnan(loss)
    assert not np.isinf(loss)
    assert loss > 10.0  # Safe high loss, but finite numeric scalar


@pytest.mark.unit
def test_forward_backward_matrix_dimensions() -> None:
    """Verifies tensor shape alignment across forward and backward passes."""
    net = TwoLayerNet(input_dim=2, hidden_dim=4, output_dim=1, seed=42)
    x, y = XOR_X, XOR_Y
    n = len(x)

    # Forward
    z1, a1, z2, a2 = net.forward(x)
    assert z1.shape == (n, 4)
    assert a1.shape == (n, 4)
    assert z2.shape == (n, 1)
    assert a2.shape == (n, 1)

    # Backward
    dw1, db1, dw2, db2 = net.backward(x, y, a1, a2)
    assert dw1.shape == (2, 4)
    assert db1.shape == (1, 4)
    assert dw2.shape == (4, 1)
    assert db2.shape == (1, 1)


@pytest.mark.unit
def test_xor_training_convergence() -> None:
    """Verifies that 2-layer network successfully solves the non-linear XOR problem."""
    net = TwoLayerNet(learning_rate=0.1, seed=42)
    metrics = net.train_xor(epochs=10000, verbose_interval=0)

    # Invariant: final loss must be significantly lower than initial loss
    assert metrics.final_loss < metrics.initial_loss
    assert metrics.final_loss < 0.05, f"Expected final loss < 0.05, got {metrics.final_loss}"

    # Invariant: 100% accuracy on XOR truth table after 10k epochs
    assert metrics.accuracy == 1.0
    assert metrics.converged is True

    # Check rounded predictions match XOR target {0, 1, 1, 0}
    predictions = (np.array(metrics.predictions) > 0.5).astype(int).tolist()
    expected = [0, 1, 1, 0]
    assert predictions == expected


@pytest.mark.unit
def test_cli_verify_json() -> None:
    """Verifies CLI execution of verify diagnostic command."""
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "scratch_nn.py"),
        "verify",
        "--json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    report = json.loads(proc.stdout)
    assert report["name"] == "neural-network-from-scratch-xor-verification"
    assert report["passed"] is True
    assert report["accuracy"] == 1.0
    assert report["loss_decreased"] is True
