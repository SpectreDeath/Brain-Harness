# Google Research `imp`: Locked Dataclass Config Governance & Registrar Pattern

## 1. Context & Provenance

- **Upstream Repository**: `https://github.com/google-research/google-research` (`imp/`)
- **Snapshot Reference**: `google-research-master` (archive snapshot, non-git)
- **Publication**: *Alternating Gradient Descent and Mixture-of-Experts for Integrated Multimodal Perception* (NeurIPS 2023, `https://arxiv.org/abs/2305.06324`)
- **Primary Verified Sources**:
  - `imp/README.md` (`L1-L95`)
  - `imp/max/config/validators.py` (`L23-L110`, sha256 `65d238cfc78ee0ac742dd2b089098b4546e396bc0b5e8ef38025184529001650`)
  - `imp/max/config/registry.py` (`L27-L110`, sha256 `71f7aa3e796ddab065e5c9fb920cd200cec6b476e30bf47f56f4880ef9d1ef44`)
  - `imp/max/config/base.py` (`L77-L232`, sha256 `f9b828b008e1cbbeb95075f0a7b92cfe2c3aa8a63736970cfede4f6815f55665`)

## 2. Core Architectural Invariants

1. **Schema-Locked Dataclass Subclassing (`validators.py`, `L31-L110`)**: `@validators.lock` pins a base dataclass (`cls.lock_attributes()`), and `@validators.validate` verifies subclass configs declare zero unknown fields (`set(config_types) - set(base_types)`) and match base type hints (allowing narrowed `Optional`/`Union` members when `unwrap_types=True`). This eliminates silent attribute-typo drift when defining experiment preset subclasses.
2. **Paired Config-Class Registry (`registry.py`, `L27-L110`)**: `Registrar.register()` / `register_with_class()` binds config classes and target classes under a unique `config.name`, failing fast on duplicate registration when `overwrite=False`.
3. **Immutable Copy-and-Override (`base.py`, `L186-L223`)**: `Config.copy_and_override()` deep-copies nested dataclasses/lists before applying dict or YAML overrides, preserving base presets.

## 3. Applicability to Brain Harness

- Directly reinforces Brain Harness `Rule 12` (Slotted & Frozen Dataclass Architecture) and `config.default.yaml` zero-fork plugin preset governance (`Rule 44`).
