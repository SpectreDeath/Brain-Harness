# Protobuf Struct Serialization & Wire Normalization

**ID:** `ki_antigravity_001`  
**Category:** `data_engineering`  
**Origin:** `google-antigravity-sdk`  
**Provenance Lineage:** `google/antigravity/connections/local/struct_converter.py`, `google/antigravity/proto/conversation.proto`

## Executive Summary
Google Antigravity establishes strict binary wire types for conversation steps, multimodal content (images/video/audio), tool calls, and error states across 25 Protocol Buffer specifications. StructConverter recursively converts Python dicts, GenAI enum types, and dataclasses into Protobuf Structs while stripping invalid JSONSchema combiners (anyOf, allOf) to prevent API schema validation rejections.

## Architectural Invariants & Rules
1. All client-server IPC step messages must be serialized to Protobuf wire format.
2. Dynamic dictionary schemas must pass through StructConverter to normalize GenAI enum representations.
3. Multimodal content blocks must preserve mime_type, byte length, and raw bytes without UTF-8 re-encoding.
