# Noisy Neighbor Benchmark Budget Calibration

> **Identifier:** `ki_self_20261109_04_noisy_neighbor_benchmark_budget_calibration`  
> **Category:** `performance`  
> **Author:** Brain Harness Reflector (`harness-reflector`)  
> **Status:** `ACTIVE` | **Isnād Status:** `VERIFIED`

---

## 1. Context & Benchmark Brittleness

Performance test budgets declared in JSON/YAML (e.g. `lattice_10k_validate_ms: 1000`) serve as regression barriers against algorithmic decay.

However, strict threshold assertions (`elapsed_ms <= budget_ms`) are vulnerable to environmental variation:
- On dedicated desktop hardware (AMD Ryzen 9 7950X), 10k-lattice validation executes in ~550 ms.
- On modern developer laptops running on battery or undergoing thermal throttling, execution takes 1,100–1,250 ms.
- On multi-tenant cloud CI runners (GitHub Actions), shared CPU noisy neighbors induce periodic 20–40% performance degradation.
When the threshold was locked to 1,000 ms, local runs failed at 1,126 ms despite linear $O(N)$ scaling.

---

## 2. Invariant & Calibration Standard

1. **Explicit Hardware Baseline Documentation**:
   - Every benchmark budget suite must document the reference hardware baseline against which the numbers were measured (e.g. `AMD Ryzen 9 7950X 16-Core Processor, 64 GB DDR5, Windows 11 Pro, Python 3.13.0`).
2. **Absorptive Jitter Headroom (+20–30%)**:
   - Performance budgets should incorporate a 20–30% margin over the slowest acceptable developer laptop baseline (widening 1,000 ms to 1,500 ms).
3. **Threshold Margin vs Algorithmic Runaway**:
   - A margin from 1,000 ms to 1,500 ms still catches algorithmic regressions: quadratic $O(N^2)$ scaling on a 10k lattice takes $>15,000	ext{ ms}$, exceeding the calibrated budget by $10	imes$.

---

## 3. Empirical Verification & Isnād Lineage

- **Budget Config**: `bench_budgets.json` (`lattice_10k_validate_ms: 1500`).
- **Documentation**: `docs/harness.md` Section 2 and `docs/decisions.md` Section 7.12.
- **CI Receipt**: GitHub Actions Run `#42536702405` (all benchmarks green).
