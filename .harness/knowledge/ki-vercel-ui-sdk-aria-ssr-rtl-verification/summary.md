# Vercel UI SDK: Tri-Modal UI Verification — WAI-ARIA APG Key Checks, Clock/DOM-Isolated SSR & Mirrored RTL Parity

**Upstream Repository**: https://github.com/vercel-labs/ui @ `220c1a0d`

## Key Invariants
- **Aggregated WAI-ARIA Pattern Checking (`packages/core/src/testing/check-pattern.ts#L28-L117`)**: Covers 15 APG patterns (`listbox`, `menu`, `menubar`, `tabs`, `radio-group`, `toolbar`, `tree`, `dialog`, `alertdialog`, `disclosure`, `accordion`, `combobox`, `slider`, `switch`, `checkbox`), collecting all missing roles, ARIA references, and focus-drop defects in a single error.
- **Deterministic SSR Isolation (`packages/core/src/testing/check-server.ts#L63-L129`)**: Hides browser globals (`document`, `window`, `navigator`, `location`, `localStorage`, `sessionStorage`, `matchMedia`) and fails immediately on clock or entropy reads (`Date.now`, `new Date()`, `performance.now`, `Math.random`, `crypto.randomUUID`, `crypto.getRandomValues`).
- **Sequential Mirrored RTL Parity (`packages/core/src/testing/check-direction.ts#L10-L124`)**: Mounts components under `dir="ltr"` and `dir="rtl"` sequentially, requiring `ArrowLeft` in RTL to match `ArrowRight` in LTR on focus target and normalized `direction`/`side` state.
