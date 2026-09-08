## Coverage Threshold Gap

### Discovery
pyproject.toml configures pytest-cov with `source = ["src/harness"]` but defines
no `[tool.coverage.report]` fail_under threshold. Coverage could degrade silently
without any CI or test run notification.

### Fix
Add to pyproject.toml:
```toml
[tool.coverage.report]
fail_under = 80
show_missing = true
```

And to pytest options:
```toml
addopts = "--cov=src/harness --cov-report=term-missing --cov-fail-under=80"
```
