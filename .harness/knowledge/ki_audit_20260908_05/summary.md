## OpenRouter KiloCode Header Coupling

### Discovery
services/openrouter_gateway.py embeds KiloCode IDE-specific HTTP headers:
X-KiloCode-OrganizationId, X-KiloCode-TaskId, X-KiloCode-Parent-TaskId,
X-KiloCode-ProjectId, X-KiloCode-Tester, X-KiloCode-EditorName,
X-KiloCode-MachineId, X-KiloCode-Feature

### Risk
Couples harness gateway to a specific IDE. In headless environments these
headers are unnecessary noise and may expose operational metadata.

### Mitigation
Headers are partially guarded by env-vars (KILOCODE_EDITOR_NAME, KILOCODE_VERSION,
KILOCODE_FEATURE). Recommend a `GatewayHeaderProvider` protocol abstraction so
IDE-specific concerns remain encapsulated behind a swappable interface.
