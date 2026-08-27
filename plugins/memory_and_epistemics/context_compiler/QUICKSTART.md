# Context Compiler Plugin — Quickstart Guide

The `domain.context_compiler` plugin reduces LLM token overhead on multi-file code editing tasks by compiling a 3-tier context:
- **Tier 1 (Full Source)**: The target file actively being edited.
- **Tier 2 (Skeletonized Interface)**: Files reachable within $N$ hops (imports and bare-name calls), with all function bodies stripped to `...` while preserving type annotations, signatures, and docstrings.
- **Tier 3 (Excluded)**: All unreachable files in the codebase.

## 🚀 Quick Usage

### Python Service API
```python
from plugins.memory_and_epistemics.context_compiler.main import compile_context, skeletonize_code

# 1. Compile context for a target file in a repository
result = compile_context(
    repo_root="/path/to/repo",
    target_file="src/my_module/target.py",
    max_hops=2
)
print(f"Token reduction: {result['reduction_pct']}%")
print(result["prompt_text"])

# 2. Skeletonize standalone code
skel = skeletonize_code("def complex_calc(x: int) -> int:\n    '''Calculates value.'''\n    step1 = x * 2\n    return step1 + 42")
print(skel["skeleton_code"])
# Output:
# def complex_calc(x: int) -> int:
#     '''Calculates value.'''
#     ...
```
