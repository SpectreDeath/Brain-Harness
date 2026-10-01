# Harness Ingestion & Bridge Pipeline (`harness.ingestion`)

The `harness.ingestion` package provides multi-source codebase discovery, Git repository fetching, AST inspection, OpenAPI/PyPI schema translation, and autonomous plugin conversion for Brain Harness.

---

## Central Function & Capabilities

The ingestion pipeline transforms external code repositories and API specifications into sandboxed Harness plugins:
1. **Multi-Source Resolution**: Dispatches source strings (`github:owner/repo`, `pypi:package-name`, `openapi:spec.json`, or local filesystem paths) to dedicated resolvers via `UniversalSourceRegistry`.
2. **Repository Fetching & Shallow Cloning**: Clones remote Git repositories with bounded depth and shallow submodules into isolated staging directories (`RepoFetcher`).
3. **AST Inspection & Archetype Detection**: Scans codebase file structures, dependencies (`pyproject.toml`, `requirements.txt`), and CLI entrypoints to detect candidate plugin archetypes (`RepoInspector`).
4. **Autonomous Plugin Conversion**: Generates complete plugin manifests (`plugin.json`), typed entrypoints (`main.py`), and test contracts wrapping the foreign codebase into a sandboxed Harness plugin (`RepoConverter`).

---

## Architectural Invariants

- **Binary Byte-Offset Seeking (Rule 48)**: When processing large multi-megabyte documentation dumps or sequential corpora, retrieval routines index byte-offsets once in binary mode and retrieve slices via $O(1)$ seeks (`f.seek()`), never reading full files into memory.
- **External Protection Boundary Fallback (Rule 46)**: When introspecting external repositories or protected paths, the ingestion pipeline falls back to non-modifying shell reads or isolated runner scripts rather than failing on IDE security boundaries.
- **Domain-Partitioned Plugin Synthesis (Rule 18)**: Disparate tools extracted from monorepos or multi-capability libraries are partitioned into single-responsibility plugins rather than monolithic bundles.

---

## Key Modules & Symbols

| Module | Core Classes / Symbols | Description |
|---|---|---|
| [`resolvers.py`](resolvers.py) | `UniversalSourceRegistry`, `GitHubSourceResolver`, `PyPISourceResolver`, `OpenAPISourceResolver` | Resolves URIs and package identifiers into structured `ResolvedSource` handles. |
| [`fetcher.py`](fetcher.py) | `RepoFetcher`, `FetchError`, `DEFAULT_PLUGIN_DIR` | Clones and stages external repositories safely with branch and commit pinning. |
| [`inspector.py`](inspector.py) | `RepoInspector`, `InspectionError` | Inspects target repository ASTs, manifests, and file layouts to detect architectures. |
| [`converter.py`](converter.py) | `RepoConverter`, `ConvertedPlugin`, `ConversionError` | Synthesizes sandboxed plugin scaffolding and configuration wrappers around code. |
| [`pipeline.py`](pipeline.py) | `PluginIngestionPipeline`, `PluginIngestionEngine` | End-to-end orchestration pipeline executing resolve $\rightarrow$ fetch $\rightarrow$ inspect $\rightarrow$ convert. |
| [`openapi_converter.py`](openapi_converter.py)| `OpenApiConverter` | Translates OpenAPI/Swagger REST schemas into declarative agent tools. |
| [`pypi_converter.py`](pypi_converter.py) | `PyPiConverter` | Generates plugin wrappers directly from PyPI package distributions. |

---

## Programmatic Usage Example

```python
import asyncio
from pathlib import Path
from harness.ingestion.pipeline import PluginIngestionPipeline

async def ingest_github_repository(repo_url: str):
    pipeline = PluginIngestionPipeline()
    
    # Run end-to-end ingestion pipeline
    result = await pipeline.ingest(
        source=repo_url,
        category="data_engineering",
        output_dir=Path("plugins/data_engineering"),
    )
    
    print(f"Ingested plugin ID: {result.plugin_id}")
    print(f"Manifest location: {result.plugin_path / 'plugin.json'}")

if __name__ == "__main__":
    asyncio.run(ingest_github_repository("https://github.com/example/tool"))
```

---

## Related Documentation

- [External Repo Bridge Forge Skill](../../../.agents/skills/external-repo-bridge-forge/SKILL.md)
- [How-To: Ingest External Repositories](../../../docs/HOWTO.md#ingesting-external-repositories-into-sandboxed-plugins)
- [Ingestion Reference](../../../docs/reference/ingestion.md)
- [Plugin Sandboxing & Lifecycle](../plugins/README.md)
