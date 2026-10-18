# Differential Facet Availability JSON Schema Reference

This reference defines the canonical wire format for multi-provider evidence records and facet availability declarations.

## 1. Supported Comparison Dimensions

The 8 canonical dimensions supported by the differential engine are:

| Dimension | Description | Typical Providers |
|---|---|---|
| `identity` | Procedure address, symbol name, binary hash, signature | All providers |
| `pseudocode` | High-level decompiler C/C++ representation | Ghidra, IDA Pro, Binary Ninja |
| `assembly` | Machine code instructions, mnemonic sequence, operands | Ghidra, Rizin, Capstone |
| `comments` | User and auto-generated annotations, type descriptions | Disassemblers |
| `calls` | Outgoing call targets and imported symbol invocations | Callgraph analyzers |
| `references` | Cross-references to data, strings, and global variables | Symbol extractors |
| `strings_names` | Referenced ASCII/UTF-8 strings and imported names | String extractors |
| `cfg` | Control Flow Graph blocks, branch edges, cyclomatic topology | Control-flow analyzers |

---

## 2. Facet Availability Object Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "FacetAvailability",
  "type": "object",
  "required": ["available"],
  "properties": {
    "available": {
      "type": "boolean",
      "description": "Whether the provider attempted observation and supports this facet"
    },
    "reason": {
      "type": "string",
      "description": "Mandatory explanation if available is false (must be non-empty)"
    }
  }
}
```

---

## 3. Coverage Declaration Object Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CoverageDeclaration",
  "type": "object",
  "required": ["scope", "status"],
  "properties": {
    "scope": {
      "type": "string",
      "enum": ["root", "container-entries", "dossier"]
    },
    "status": {
      "type": "string",
      "enum": ["complete", "unknown", "partial"]
    },
    "truncated": {
      "type": "boolean",
      "default": false
    },
    "omitted_count": {
      "type": "integer",
      "minimum": 0,
      "default": 0
    }
  }
}
```

---

## 4. Multi-Provider Dossier Example

```json
{
  "id": "ev:9a3f2b1c4e6d8a7f0e2b4c6d8a0f2e4b6c8d0a2f4e6b8c0d2a4f6e8b0c2d4a6",
  "provider": "ghidra",
  "subject_format": "elf",
  "coverage": {
    "scope": "dossier",
    "status": "complete",
    "truncated": false,
    "omitted_count": 0
  },
  "facet_availability": {
    "identity": { "available": true },
    "assembly": { "available": true },
    "pseudocode": { "available": true },
    "cfg": { "available": false, "reason": "CFG generation skipped during headless batch export" }
  },
  "identity": { "name": "main", "address": "0x401000" },
  "assembly": [
    "push rbp",
    "mov rbp, rsp",
    "sub rsp, 0x10"
  ],
  "pseudocode": "int main(void) { return 0; }"
}
```
