# Ingestion Pipeline Reference (`harness.ingestion`)

The `harness.ingestion` package provides multi-source discovery, shallow repository cloning, AST inspection, and automated plugin generation for Brain Harness.

---

## 1. `UniversalSourceRegistry` & `SourceResolver`

### `UniversalSourceRegistry`
Central registry matching URI schemes and strings to dedicated source resolvers.

#### Methods
- `register_resolver(prefix: str, resolver: SourceResolver) -> None`: Registers a custom resolver.
- `resolve_source(source_uri: str) -> ResolvedSource`: Inspects URI and returns a typed `ResolvedSource` handle.

### Built-in Resolvers
- `GitHubSourceResolver`: Resolves `https://github.com/owner/repo` and `github:owner/repo`.
- `PyPISourceResolver`: Resolves `pypi:package-name` against the PyPI JSON API.
- `OpenAPISourceResolver`: Resolves `openapi:spec.json` and remote Swagger URLs.
- `LocalDirectorySourceResolver`: Resolves local paths and directory trees.

---

## 2. `RepoFetcher`

Clones remote repositories and stages archives into isolated workspace paths.

### Methods
- `fetch(source: ResolvedSource, target_dir: Path) -> FetchResult`: Executes bounded shallow clone (`git clone --depth 1`) or archive extraction into `target_dir`.

---

## 3. `RepoInspector`

Inspects target codebase ASTs and manifests to infer optimal plugin archetypes.

### Methods
- `inspect_repository(repo_path: Path) -> InspectionReport`: Identifies programming languages, dependency manifests (`pyproject.toml`, `package.json`), entrypoints, and candidate tools.

---

## 4. `RepoConverter` & `PluginIngestionPipeline`

### `PluginIngestionPipeline`
End-to-end pipeline coordinating resolution, fetching, AST inspection, and code synthesis.

#### Methods
- `ingest(source: str, category: str, output_dir: Path) -> IngestionResult`: Executes the complete ingestion sequence, authoring `plugin.json` and sandboxed entrypoints.

### `RepoConverter`
Synthesizes Harness plugin scaffolding and IPC subprocess wrappers around foreign codebases.

#### Methods
- `convert_to_plugin(inspection: InspectionReport, output_dir: Path) -> ConvertedPlugin`: Scaffolds manifest, IPC communication wrappers, and default configurations.
