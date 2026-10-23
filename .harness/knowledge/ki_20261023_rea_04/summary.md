# Static Native Boundary Mapping for Managed CLI/PE Runtimes

## Core Architectural Principle

In managed runtimes (.NET Framework, .NET Core, Unity Mono), applications frequently interoperate with native C/C++ libraries via Platform Invocation Services (`P/Invoke`). Static reverse engineering can uncover external dependencies, entrypoints, and signature mismatches without executing hostile binaries.

## Operational Pattern

1. **PE/CLI Header Extraction:**
   - Verify PE DOS magic `0x5A4D` (`MZ`) and PE signature.
   - Inspect Data Directory #14 (index 14) for the `IMAGE_COR20_HEADER` RVA and size.
   - Parse `STORAGESIGNATURE` (`BSJB`) to identify metadata streams: `#~`, `#Strings`, `#US`, `#GUID`, `#Blob`.

2. **ModuleRef and P/Invoke Mapping:**
   - Scan PE import tables (Data Directory #1) for unmanaged DLL dependencies (`kernel32.dll`, `user32.dll`, native driver DLLs).
   - Extract `ImplMap` table rows to identify method names, target DLL modules, and calling conventions (`cdecl`, `stdcall`, `thiscall`).
   - Flag unmanaged entrypoints that bypass managed memory safety invariants.

## Provenance
- **Source Repository:** `morluto/rea`
- **Source Module:** `src/contracts/managed/managedToolContracts.ts` (L1-L80)
- **Commit:** `701695139`
