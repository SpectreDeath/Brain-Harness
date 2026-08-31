# KI-3: Embedded In-Process Graph Database Drivers with Kùzu

## Overview & The Zero-Dependency Seam
External graph databases (such as Neo4j or Memgraph) require Docker containers, JVM runtimes, open network ports, and persistent authentication credentials. Graphiti solves this by implementing `KuzuDriver` as a first-class backend option.

## Architecture & Implementation

From `graphiti_core/driver/kuzu_driver.py`:
```python
import kuzu
from graphiti_core.driver.driver import GraphDriver, QueryExecutor

class KuzuDriver(GraphDriver):
    """In-process columnar graph database driver using Kùzu."""
    def __init__(self, database_path: str = ":memory:"):
        self.db = kuzu.Database(database_path)
        self.conn = kuzu.Connection(self.db)
        self._init_operations()

    async def execute_query(self, cypher_query: str, **kwargs: Any):
        # Translates and executes Cypher against local C++ engine
        return self.conn.execute(cypher_query, kwargs)
```

## Key Engineering Takeaways for Brain Harness
1. **Zero-Infra Testing**: Test suites run in parallel using in-memory `:memory:` Kùzu instances without needing mock databases or container spinning.
2. **Local Agent Embeddability**: Desktop agents, CLI tools, and local memory plugins can run persistent disk-backed knowledge graphs locally with zero setup steps for end users.
