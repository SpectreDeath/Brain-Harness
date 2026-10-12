"""Click group consolidation for coding harness calibrator per Rule 6."""

from __future__ import annotations

import click

from harness.commands.calibrator.brief import calibrator_brief_cli
from harness.commands.calibrator.recommend import calibrator_recommend_cli
from harness.commands.calibrator.repatch import calibrator_repatch_cli
from harness.commands.calibrator.staging import calibrator_staging_cli


@click.group("calibrator")
def calibrator_group() -> None:
    """Empirical coding harness component calibration, staging simulation, and forecasting."""


# Consolidate command registrations in a single place per Rule 6
calibrator_group.add_command(calibrator_recommend_cli)
calibrator_group.add_command(calibrator_staging_cli)
calibrator_group.add_command(calibrator_repatch_cli)
calibrator_group.add_command(calibrator_brief_cli)
