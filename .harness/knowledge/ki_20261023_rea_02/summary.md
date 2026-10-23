# Multi-Version Magic Header Parsing & Section Map Validation for Unity IL2CPP

## Core Architectural Principle

Unity compiled games utilizing the IL2CPP AOT backend strip .NET metadata from executable assemblies and serialize type, method, string literal, and field tables into a monolithic `global-metadata.dat` binary file.

## Operational Pattern

1. **Header Assertion & Magic:**
   - Assert the 4-byte unsigned little-endian integer at offset 0 equals `0xFAB11BAF`.
   - Read the 4-byte signed integer at offset 4 to extract the metadata version (v24, v27, v29, v31, v39).
   - If magic does not match, fail closed with `status: "invalid_magic"` rather than misinterpreting subsequent offsets.

2. **Section Map Layout Differences:**
   - In versions 29, 31, and 39, section descriptors are laid out as pairs of `(offset: int32, size: int32)` starting with `stringLiterals`, `stringLiteralData`, `strings`, `events`, `properties`, and `methods`.
   - In version 27, custom attribute information replaces standard v29 layout at index 24.
   - String literal indices must be resolved against the string offset table rather than assumed sequential byte runs.

## Provenance
- **Source Repository:** `morluto/rea`
- **Source Module:** `src/domain/il2cpp/il2cppMetadata.ts` (L1-L60)
- **Commit:** `34563fcc9`
