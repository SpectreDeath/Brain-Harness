# Quickstart: `plugin.okf_memory`

Git-native agent memory governor providing in-memory BM25 lexical ranking, pre-edit governance scoping, concept mutations, and trust ordering validation for Open Knowledge Framework (OKF v0.2) bundles.

---

## 1. Pre-Edit Governance Scoping

Before modifying any source code in the repository, evaluate path-scoped governance constraints:

```python
from plugins.memory_and_epistemics.okf_memory.main import okf_search

# Check governance constraints for an auth middleware file
scope = okf_search(for_path="src/api/auth/jwt.py")
print(f"Matched concepts: {scope['results_count']}")
for item in scope["results"]:
    print(f"[{item['id']}] {item['title']}")
    print(f"  Rules: {item.get('governance', [])}")
```

---

## 2. BM25 Lexical Search

Search the knowledge bundle with sub-millisecond lexical scoring and governance term boosting:

```python
from plugins.memory_and_epistemics.okf_memory.main import okf_search

# Search for caching strategies with limit=3 (progressive disclosure)
res = okf_search(query="redis token revocation blacklist", limit=3)
for item in res["results"]:
    print(f"({item['score']}) [{item['id']}] {item['title']}: {item['description']}")
```

---

## 3. Retrieve Concept Details

Load full Markdown body and YAML frontmatter metadata:

```python
from plugins.memory_and_epistemics.okf_memory.main import okf_show

concept = okf_show("auth-jwt-revocation")
if concept["status"] == "ok":
    data = concept["concept"]
    print("Body:\n", data["body"])
    print("Code references:", data["code_refs"])
```

---

## 4. Atomic Mutation & Bookkeeping

Create or update concept documents. Parent `index.md` tables and `log.md` audit ledgers are synced automatically:

```python
from plugins.memory_and_epistemics.okf_memory.main import okf_create, okf_update

# Create new architecture decision
created = okf_create(
    concept_id="db-connection-pool",
    title="Database Connection Pool Sizing",
    concept_type="architecture",
    description="Maintains bounded connection pool size of 20 with 5s timeout.",
    body="## Implementation Details\n\nConfigured via AsyncEngine pool_size=20.",
    governance=["Do not set pool_size > 50 in production", "Always set pool_pre_ping=True"],
    code_refs=["src/db/session.py"],
)

# Update existing concept
updated = okf_update(
    concept_id="db-connection-pool",
    description="Maintains bounded connection pool size of 25 with 5s timeout.",
)
```

---

## 5. Bidirectional Relationship Linking

Link related concepts in their frontmatter schemas:

```python
from plugins.memory_and_epistemics.okf_memory.main import okf_relate

res = okf_relate(
    source_id="db-connection-pool",
    target_id="db-read-replica",
    description="Read replicas use separate slave connection pools",
)
```

---

## 6. Normative Schema & Trust Validation

Validate that the knowledge bundle satisfies OKF v0.2 requirements and actor trust ordering invariants:

```python
from plugins.memory_and_epistemics.okf_memory.main import okf_validate

report = okf_validate(strict=True)
print("Valid:", report["valid"])
print("Errors:", report["errors"])
print("Warnings:", report["warnings"])
```

---

## 7. IoC Service Resolution

Resolve the service dynamically inside Brain Harness plugins or agent step loops:

```python
from harness.kernel.context import ServiceContext
from harness.services.okf_memory import OKF_MEMORY_SERVICE_KEY, OKFMemoryService

async def run(ctx: ServiceContext):
    service = ctx.require(OKF_MEMORY_SERVICE_KEY)
    results = await service.okf_search_async(for_path="src/harness/cli.py")
    print(results)
```

---

## 8. CLI Commands

The plugin is also exposed via the Brain Harness CLI:

```bash
# Scope governance constraints before modifying a file
harness okf scope src/harness/cli.py

# Search knowledge bundle
harness okf search "jwt authentication" --limit 3

# Show concept markdown and frontmatter
harness okf show auth-jwt-revocation

# Validate bundle against OKF v0.2 specifications
harness okf validate --strict
```
