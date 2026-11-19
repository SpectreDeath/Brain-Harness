# Google Research `psycholab`: ASCII Multi-Agent Gridworld Games, Conflict Resolution & RGB Visualizer

## 1. Context & Provenance

- **Upstream Repository**: `https://github.com/google-research/google-research` (`psycholab/` subproject, 12 files)
- **Snapshot Reference**: `google-research-master` (archive snapshot, non-git)
- **Publication Reference**: *Foolproof Cooperative Learning* (`https://arxiv.org/abs/1906.09831`) and repeated grid prisoner's dilemma (`https://arxiv.org/abs/1206.3277`)
- **Primary Verified Sources**:
  - `psycholab/README.md` (`L1-L103`)
  - `psycholab/game.py` (`L1-L705`, sha256 `49553816cc70f01ba36da326bedcff2e909efb066fa8a575dcaa97073aadbe26`)
  - `psycholab/visualizer.py` (`L31-L95`, sha256 `ffa20439be6e56b6a19f39671491113b78448ba490fa149bb1b2d497f73065e9`)

---

## 2. Core Problem & Architectural Thesis

Evaluating multi-agent coordination, social dilemmas, and visual RL policies requires lightweight deterministic environments where simultaneous agent collisions and spatial layouts can be configured rapidly. `psycholab` compiles ASCII-art maps + typed `Item`/`Player` descriptors into Gym-compatible discrete or RGB-rendered (`HxWx3 uint8`) multi-agent gridworlds with explicit multi-pass conflict resolution.

---

## 3. Verified Implementation Invariants

### A. Multi-Pass Simultaneous Conflict Resolution & Event Rewards (`game.py` `L480-L651`)
- `Game.solve_conflicts(actions)` (`L480-L583`) applies four sequential collision passes before mutating state:
  1. Rejects moves into `player_walls`, `absolute_walls`, or impassable/non-pushable `items` (`<player>_goes_in_walls`, `<player>_blocked_by_<item>`).
  2. Cancels opposing head-on crossings (`((MOVING_ACTIONS[a] + MOVING_ACTIONS[b])**2).sum() == 0`) between non-passable players.
  3. Cancels moves into occupied cells held by standing (`other_action == 0`) non-passable players.
  4. Resolves simultaneous target-cell contentions by randomly choosing one winner and reverting losers to stand (`<player>_lost_the_drawn`).
- Event names feed directly into declarative `reward_events`, `apply_effects`, `terminal_step`, and ordered RGB `render` (`walls > agents > items`, alphabetical precedence within layers, `L625-L651`), plus `discrete_state` / `one_hot_state` encodings (`L653-L699`).

### B. Live Multi-Pane Environment Visualizer (`visualizer.py` `L31-L95`)
- `Visualizer` wraps any `Game` instance (`fps`, `by_episode`, optional `FFMpegWriter` MP4 recording at 300 dpi) to display the current spatial RGB grid alongside per-player and mean cumulative reward curves.

---

## 4. Applicability to Brain Harness & Anti-Patterns

- **Harness Seam Targets**: Multi-agent simulation and resource-arbitration harnesses can mirror `psycholab`'s ordered conflict-resolution pipeline (static boundary guards -> bilateral swap guards -> stationary contention -> fair randomized tie-breaking) to keep concurrent state updates reproducible and observable via structured event logs.
- **Anti-Patterns**:
  - **Do not apply player moves sequentially in dictionary iteration order** without simultaneous conflict resolution — naive sequential updates create silent turn-order unfairness biased toward earlier keys.
  - **Do not conflate discrete state index encoding with continuous RGB rendering** — expose explicit `tabular` vs visual observation modes cleanly.
