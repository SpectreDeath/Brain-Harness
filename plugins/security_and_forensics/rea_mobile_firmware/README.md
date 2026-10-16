# REA Mobile & Firmware Forensics Plugin (`plugin.rea_mobile_firmware`)

## Overview

Part of the REA multi-capability reverse engineering bridge into Brain Harness.
Provides Android APK static inspection, headless JADX decompilation, class reference tracing,
discrete typed ADB device bridging, and Linux-isolated Binwalk/Unblob firmware carving.

- **Category:** `security_and_forensics`
- **Service Key:** `service.rea_mobile_firmware`
- **Isolation Mode:** `IsolationMode.SUBPROCESS` (Rule 5)
- **Source Repository:** `https://github.com/morluto/rea` (Commit: `ffaf2c12`)

## Exported Tools

1. `rea_mobile_apk_inspect(apk_path, decode_resources=True)`
2. `rea_mobile_jadx_decompile(apk_path, class_filter=None, output_dir=None)`
3. `rea_mobile_android_search_classes(apk_path, query)`
4. `rea_mobile_android_trace_references(apk_path, class_name, method_name=None)`
5. `rea_mobile_adb_inspect_client()`
6. `rea_mobile_adb_list_devices()`
7. `rea_mobile_adb_list_packages(device_serial=None)`
8. `rea_mobile_adb_pull_package(package_name, device_serial=None, destination=".")`
9. `rea_mobile_adb_read_logcat(device_serial=None, buffer="main", filter_tag=None, max_lines=500)`
10. `rea_firmware_regions_inspect(firmware_path)` — *Linux-only (returns platform_unsupported on Windows)*
11. `rea_firmware_extract(firmware_path, destination_dir)` — *Linux-only (returns platform_unsupported on Windows)*

## Operational Budgets (`config.default.yaml`)

- `subprocess_timeout_s`: 120
- `firmware_max_input_bytes`: 134,217,728 (128 MiB)
- `adb_command_timeout_s`: 30
- `jadx_worker_count`: 1


---

## Tools & Entrypoints

| Entrypoint | Parameters | Description |
|---|---|---|
| `rea_mobile_apk_inspect` | `(apk_path, decode_resources)` | Inspect APK manifest, package identity, permissions, SDK levels, and component counts. |
| `rea_mobile_jadx_decompile` | `(apk_path, class_filter, output_dir)` | Decompile Dalvik bytecode into Java/Smali source trees via headless JADX. |
| `rea_mobile_android_search_classes` | `(apk_path, query)` | Search decompiler class names by case-sensitive substring. |
| `rea_mobile_android_trace_references` | `(apk_path, class_name, method_name)` | Trace static incoming references to a class or unique method across the decompiled APK. |
| `rea_mobile_adb_inspect_client` | `()` | Report resolved adb binary path, version, and install source without contacting devices. |
| `rea_mobile_adb_list_devices` | `()` | Enumerate attached devices and emulators with state, model, and serial metadata. |
| `rea_mobile_adb_list_packages` | `(device_serial)` | List installed packages on one device with base APK paths. |
| `rea_mobile_adb_pull_package` | `(package_name, device_serial, destination)` | Pull a device-installed APK to a local path. |
| `rea_mobile_adb_read_logcat` | `(device_serial, buffer, filter_tag, max_lines)` | Bounded adb logcat dump for a given buffer and optional tag filter. |
| `rea_firmware_regions_inspect` | `(firmware_path)` | Scan binary with Binwalk 3.1.0 for signature candidates (Linux-only). |
| `rea_firmware_extract` | `(firmware_path, destination_dir)` | Unpack embedded partitions via Unblob 26.6.4 into structured file trees (Linux-only). |
