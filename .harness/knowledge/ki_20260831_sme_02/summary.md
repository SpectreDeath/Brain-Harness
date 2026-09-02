# Agentic Neural Network (ANN) Textual Backpropagation & Momentum Smoothing

## Context
When multi-agent swarms or sequential execution pipelines fail, standard agents either retry blindly with the exact same prompts or hallucinate modifications without structural memory. 

## Distilled Learning
Implement an Agentic Neural Network ($\mathcal{ANN}$) backpropagation engine (`TextualGradientEngine`):
1. **Global Textual Loss Signal ($G_{\text{global}}$)**:
   - Evaluates multi-step trajectory status and error payloads to compute bounded loss $\in [0, 1]$.
   - Identifies failed layer indices, structural suggestions, and inter-layer flow updates.
2. **Local Layerwise Gradient ($G_{\text{local},\ell}$)**:
   - Combines global loss and layer-specific failure status using mixing coefficient $\beta$:
     $$\text{Loss}_{\text{combined}} = \beta \cdot \text{Loss}_{\text{global}} + (1 - \beta) \cdot \text{Loss}_{\text{local}}$$
   - Generates node prompt refinements and inserts missing validator nodes.
3. **Momentum Velocity Smoothing (`MomentumBuffer`)**:
   - Maintains update history across iterations with momentum coefficient $\alpha = 0.7$:
     $$G'_{t} = \alpha \cdot G_{t} + (1 - \alpha) \cdot G_{t-1}$$
   - Prevents abrupt oscillatory swings in agent prompt instructions and preserves validated optimizations.

## Triggers & Seam Choices
- **Trigger**: Post-mortem analysis on failed multi-agent task trajectories or autonomous skill refinement loops.
- **Seam Choice**: Encapsulate in `src/harness/agent/textual_gradient.py` and integrate with `DynamicTrajectoryEscalator`.
