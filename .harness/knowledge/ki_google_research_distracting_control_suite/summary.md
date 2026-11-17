# Google Research `distracting_control`: Composable Robustness & Perturbation Wrappers

## 1. Context & Provenance

- **Upstream Repository**: `https://github.com/google-research/google-research` (`distracting_control/`)
- **Snapshot Reference**: `google-research-master` (archive snapshot, non-git)
- **Publication**: *The Distracting Control Suite — A Challenging Benchmark for Reinforcement Learning from Pixels* (`https://arxiv.org/pdf/2101.02722.pdf`)
- **Primary Verified Sources**:
  - `distracting_control/README.md` (`L1-L48`)
  - `distracting_control/suite.py` (`L30-L110`, sha256 `49bc7c4496414d8343fe565fc832bc2195e63b07718d732bae5949fe9ff62730`)

## 2. Core Architectural Invariants

- **Composable Orthogonally-Controlled Perturbations (`suite.py`)**: Background video substitution (`DAVIS 2017`), camera pose jitter, and color shifts are isolated wrapper modules that can be composed individually or preset across `difficulty` tiers (`easy`, `medium`, `hard`) with `dynamic=True|False` toggling, while preserving standard `dm_control` environment interfaces (`suite.load()`).

## 3. Applicability to Brain Harness

- Useful design template for **chaos/noise fault injection** and harness evaluation suites: parameterize orthogonal distractors independently across difficulty levels behind a drop-in adapter interface.
