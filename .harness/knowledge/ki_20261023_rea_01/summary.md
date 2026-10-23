# Zero-Allocation Binary Offset Seeking for High-Scale Model Artifact Inspection

## Core Architectural Principle

When ingesting or inspecting multi-gigabyte neural network model weights (GGUF v2/v3, safetensors), agents and inspection engines must never serialize the entire file or allocate tensor weight buffers into host RAM or GPU VRAM.

## Operational Pattern

1. **Safetensors Inspection:**
   - Read only the first 8 bytes (little-endian unsigned 64-bit integer $N$) to determine the exact length of the JSON header.
   - Read exactly $N$ bytes containing `__metadata__` and tensor declarations (`shape`, `dtype`, `data_offsets`).
   - Terminate reading immediately at byte $8 + N$, leaving the multi-gigabyte weight buffer untouched on disk.

2. **GGUF Inspection:**
   - Validate magic `0x46554747` (`b"GGUF"`) and format version (v2 or v3).
   - Read header metadata KV count and tensor count.
   - Stream metadata strings and scalars; for array types, skip elements via offset addition rather than loading array elements into RAM.
   - Construct an $O(1)$ byte-offset lookup table (`dict[tensor_name, (data_offset, byte_length)]`) to allow selective slicing.

## Provenance
- **Source Repository:** `morluto/rea`
- **Source Module:** `src/domain/model/modelArtifact.ts` (L1-L75)
- **Commit:** `635f673a8`
