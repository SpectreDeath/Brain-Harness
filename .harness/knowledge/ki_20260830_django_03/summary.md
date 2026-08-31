# Declarative Metaclass Field Descriptors & Deferred QuerySet Compilation

## Architectural Summary
`ModelBase` and `QuerySet` combine metaclass introspection and immutable AST expressions to defer SQL generation and execution until terminal evaluation.

## Operational Guidelines
1. **Descriptor Fields:** Wrap entity attributes in Python descriptors that validate and manage state transitions.
2. **Immutable Chaining:** QuerySet builder methods (`filter`, `exclude`, `order_by`) clone and return new QuerySet AST instances without modifying the original object.
3. **Deferred Execution:** Never perform network or disk I/O in query construction methods; trigger execution only when evaluated.
