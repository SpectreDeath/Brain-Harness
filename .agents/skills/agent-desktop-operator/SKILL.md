---
name: agent-desktop-operator
description: Operate desktop applications across Windows, macOS, and Linux using accessibility tree snapshot maps, qualified ref allocation, and 2D delivery-retry recovery. Do not use for DOM-only web scraping or pixel-matching OCR.
---

# Agent Desktop Operator: OS Accessibility Computer Use Engine

`agent-desktop-operator` equips AI coding agents with direct desktop GUI operation across Windows, macOS, and Linux through native OS accessibility trees (UI Automation on Windows, AXUIElement on macOS, and AT-SPI on Linux) without screenshots or fragile pixel matching.

See [CARD.md](CARD.md) for the companion summary card, vocabulary definitions, and invariants checklist.
Consult [config.default.yaml](config.default.yaml) for baseline operational budgets and timeout thresholds.

---

## The 5-Stage Observe-Drill-Act-Verify Loop

```
[1. Preflight Status] ──► [2. Skeleton Mapping] ──► [3. Subtree Drill-Down]
                                                             │
                                                             ▼
[5. Verify & 2D Recovery] ◄── [4. Semantic Action Dispatch] ◄┘
```

---

## 1. Preflight Status & Surface Discovery

Before interacting with desktop windows, verify runtime permissions and surface capabilities:

1. **Query Platform Status**:
   - Run `agent-desktop status` (or `desktop_status` via IoC service).
   - Check that `permissions_granted` is true and note `supported_surfaces` (`window`, `menu`, `dialog`, `sheet`, `alert`).
2. **Handle Elevation & Sandboxing**:
   - On Windows, UI Automation interacts with standard and elevated windows under appropriate privilege levels.
   - On macOS, confirm Accessibility grant under System Settings > Privacy & Security > Accessibility.

> **Completion criterion**: Runtime reports `ok: true`, OS accessibility API active, and surface types enumerated.

---

## 2. Skeleton Mapping for Dense Applications

Large applications can contain thousands of accessible nodes. Never read the entire application tree at full depth in a single turn:

1. **Generate Shallow Skeleton**:
   - Run `agent-desktop snapshot --skeleton --app "AppName" -i --compact`.
   - `--skeleton` clamps branch depth while recording `children_count` on truncated branches.
   - `-i` filters to interactive actionable elements only.
   - `--compact` strips redundant geometry for token efficiency.
2. **Respect Web-Wrapper Bypass**:
   - In Chromium and Electron applications (window class `Chrome_WidgetWin_1`), anonymous transparent container wrappers consume zero logical depth budget, preventing web views from exhausting observation quotas.
3. **Never Skeleton Focused Surfaces**:
   - When inspecting popovers, dropdowns, or system sheets, pass `--surface menu` or `--surface sheet` directly without `--skeleton`.

> **Completion criterion**: Shallow skeleton snapshot generated with root-level navigation refs and candidate branch ref tokens.

---

## 3. Subtree Drill-Down

Once candidate containers are identified from the skeleton, drill down to reveal leaf actionable controls:

1. **Execute Root Drill**:
   - Run `agent-desktop snapshot --root '@s8f3k2p9:e3' -i --compact`.
   - Drilling expands the selected subtree and dynamically allocates fresh refs within the *same* `snapshot_id`.
   - Refs outside the drilled subtree remain valid; previous refs inside the expanded branch are superseded.
2. **PowerShell Quote Syntax**:
   - In PowerShell, always quote the ref: `'@s8f3k2p9:e3'`. A bare `@token` triggers PowerShell argument splatting.

> **Completion criterion**: Subtree expanded into leaf actionable refs without invalidating the parent snapshot context.

---

## 4. Semantic Action Dispatch

Act on qualified element references using headless semantic actions before resorting to physical pointer movement:

1. **Verify Qualified Ref Token (Rule 12)**:
   - Validate that the target matches `@<snapshot_id>:e<N>`. Reject bare `@e8` tokens to prevent stale mutation.
2. **Execute Headless Semantic Actions**:
   - Preferred commands: `click`, `set-value`, `type`, `select`, `toggle`, `check`, `uncheck`, `expand`, `collapse`.
   - Headless actions dispatch directly via the OS accessibility API without pointer repositioning or focus stealing.
3. **Headed Fallback for Custom Canvas Elements**:
   - When an application control lacks semantic action patterns, pass `--headed mouse-click` to simulate physical cursor positioning and hardware events.

> **Completion criterion**: Action dispatched with structured activation steps and parsed 2D disposition metadata.

---

## 5. Verify & 2D Disposition Recovery

Inspect action envelopes to confirm delivery and handle stale states deterministically:

1. **Evaluate 2D Outcome Matrix**:
   - **`DeliveryDisposition`**: `NotDelivered`, `DeliveryUncertain`, `DeliveredUnverified`, or `DeliveredVerified`.
   - **`RetryDisposition`**: `Safe`, `Unsafe`, or `Unknown`.
   - **Transaction Rollback Rule**: If delivery is `DeliveryUncertain` or retry is `Unsafe`, trigger transaction rollback (Rule 8) and take a fresh observation.
2. **Handle Standard Error Refusals**:
   - `STALE_REF`: The UI changed; re-drill the region or take a new snapshot. Never retry the stale ref.
   - `AMBIGUOUS_TARGET`: An identical twin appeared or uniqueness was lost; retake snapshot with higher timeout or target an adjacent unique anchor.
   - `TIMEOUT` (`resolution_identity_unknown`): Live read delayed; safe to retry.
3. **Dynamic State Waiting**:
   - After asynchronous actions, call `agent-desktop wait --element '@s:eN' --timeout-ms 5000` or `wait --window "Title"` instead of inserting arbitrary time sleeps.

> **Completion criterion**: Action verified via subsequent observation or safely rolled back upon uncertain delivery.

---

## The Three Foundational Pillars

### 1. The Visual Brief Pillar
Every major desktop introspection session renders an interactive HTML visual brief in `%TEMP%` displaying the hierarchical accessibility tree, surface boundaries, and active ref allocations with Tailwind CSS and Mermaid diagrams.

### 2. The Mandatory Checkpoint Pillar
The agent must never execute destructive or non-idempotent desktop mutations without verifying qualified ref tokens (`@<snapshot_id>:e<N>`) and checking `is_retry_safe` disposition gates before dispatch.

### 3. Evidence Tri-State & Subprocess Isolation
Never collapse `Unknown` into `Absent` or boolean `False`. A failed property read or timed-out subtree must withhold uniqueness claims (`CaptureProof`) rather than assuming an element is unique, executing behind isolated subprocess transports with Rule 14 pipe drainage.

---

## Anti-Patterns

- **Bare Ref Splatting** — Passing `@e12` instead of qualified `'@s8f3k2p9:e12'` in PowerShell, triggering argument splatting and command failure.
- **Fixed Sleep Polling** — Inserting arbitrary `time.sleep()` after actions instead of using condition-based `agent-desktop wait`.
- **Skeletonizing Focused Surfaces** — Applying `--skeleton` to menus or modal dialogs, which are already focused and compact.
- **Double-Clicking Uncertain Actions** — Repeating an action whose delivery was `DeliveryUncertain` without checking `is_retry_safe`.
- **Pixel-Matching Fragility** — Attempting coordinate OCR or visual screenshot diffing when native semantic accessibility trees are available.
- **Leaking Subprocess Transports** — Omitting `finally` block pipe drainage on async subprocess CLI runners (Rule 14 & Rule 53).
