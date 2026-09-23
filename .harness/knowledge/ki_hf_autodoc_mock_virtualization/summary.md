# Zero-Dependency Meta-Path Mock Virtualization for AST Introspection

## Context
Extracted during automated repository triad ingestion of Hugging Face `doc-builder` (`D:\GitHub\cloned\doc-builder`). In deep learning libraries (Transformers, Diffusers, PyTorch, TensorFlow, JAX), importing packages for documentation inspection typically requires gigabytes of compiled CUDA binaries, custom C extensions, and accelerator hardware.

## Distilled Mental Model & Engineering Breakthrough
Instead of installing all target framework dependencies, Hugging Face `doc-builder` deploys an in-process meta-path importer hook (`MockFinder` implementing PEP 302 / PEP 451):
1. **Dynamic Module Virtualization**: When an uninstalled dependency is requested (e.g. `import torch`), `MockFinder.find_spec` intercepts the import and synthesizes a `_MockModule`.
2. **Metaclass Inheritance Compatibility**: When documented classes inherit from missing third-party classes (`class MyModel(nn.Module):`), `_MockBaseMeta` generates synthetic base classes on the fly so class declarations don't raise `TypeError`.
3. **Distribution & Version Spoofing**: `importlib.metadata.version` calls are intercepted via `_MockDistribution` to return valid SemVer strings, satisfying library initialization checks.

## Triggers & Seam Choices
- **Trigger**: When performing automated AST or runtime introspection of heavy Python libraries without heavyweight local environments.
- **Seam Choice**: Integrate through `HfDocBuilderService.inspect_autodoc()` with `mock_heavy_deps=True` before delegating to `inspect` and `ast` parsers.
