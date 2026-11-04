# 2D Delivery × Retry Disposition Matrix with Stability Sampling

## Context
Extracted during automated repository triad ingestion from `D:\GitHub\cloned\agent-desktop`.

## Distilled Learning
When an agent interacts with a desktop GUI, failure to deliver an action differs crucially from delivering an action without observation verification. agent-desktop pairs DeliveryDisposition with RetryDisposition in every envelope and error. Furthermore, check_with_stability_or_gap samples transient window animations before converting a layout shift into an error, ensuring agent ReAct execution loops know with mathematical certainty whether an action can safely be retried or requires an emergency transaction rollback.

## Triggers & Seam Choices
- **Trigger**: Desktop GUI automation, native accessibility tree walks, ref resolution, or agent ReAct tool retry decisions.
- **Seam Choice**: Integration via Brain Harness IoC container (`AGENT_DESKTOP_KEY`), `agent-desktop-operator` skill, and `plugin.agent_desktop`.
