# REA Managed Runtime & Bytecode Forensics Plugin (`plugin.rea_managed_runtime`)

Autonomous bridge and domain-partitioned reverse engineering plugin synthesized from [morluto/rea](https://github.com/morluto/rea) (v6.7.0).

## Capabilities

- **Service Key:** `service.rea_managed_runtime` (`REA_MANAGED_RUNTIME_KEY`)
- **Plugin Module Singleton:** `plugin = ReaManagedRuntimePlugin()`
- **Isolation Mode:** `IsolationMode.SUBPROCESS` (Rule 5)

### Exported Tools

1. `rea_inspect_managed_artifact(target_path, extract_members=True)`
   - Inspects Windows PE/CLI binaries or .NET assemblies without execution.
   - Extracts CLR 2.0 runtime headers, metadata streams (`#~`, `#Strings`, `#US`, `#GUID`, `#Blob`), and declared types.
2. `rea_inspect_managed_native_boundaries(target_path)`
   - Extracts PE/CLI ModuleRef, ImplMap, and P/Invoke declarations.
   - Maps unmanaged DLL dependencies and calling convention flags.
3. `rea_inspect_il2cpp_metadata(metadata_path, max_records=100)`
   - Parses Unity IL2CPP `global-metadata.dat` (versions 24, 27, 29, 31, 39; magic `0xfab11baf`).
   - Extracts string literals, method definitions, type definitions, and assembly images.
4. `rea_inspect_model_artifact(model_path, preview_tensors=50)`
   - Direct $O(1)$ byte-offset seek inspection of GGUF v2/v3 and safetensors files (Rule 48).
   - Extracts tensor shapes, types, parameter counts, and metadata dictionaries without loading weights into RAM.
5. `rea_inspect_python_pyc(pyc_path, disassemble=True)`
   - Validates 16-byte magic headers across Python 3.7–3.13.
   - Disassembles marshal code objects into structured instruction representations.
