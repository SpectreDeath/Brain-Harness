"""Tests for Domain 2: Terraform IaC plugin."""

from __future__ import annotations

import pytest

from plugins.terraform_iac.main import (
    detect_state_drift,
    estimate_resource_costs,
    parse_hcl_blocks,
)


@pytest.mark.unit
class TestTerraformIacPlugin:
    def test_parse_hcl_blocks(self) -> None:
        hcl = (
            'resource "aws_instance" "web" {\n'
            '  ami = "ami-12345"\n'
            '}\n'
            'variable "region" {\n'
            '  default = "us-east-1"\n'
            '}\n'
        )
        res = parse_hcl_blocks(hcl)
        assert res["status"] == "ok"
        assert res["total_blocks_found"] == 2
        assert res["blocks"][0]["resource_type"] == "aws_instance"
        assert res["blocks"][0]["name"] == "web"

    def test_detect_state_drift(self) -> None:
        declared = {"instance_type": "t3.micro", "tags": {"env": "prod"}}
        actual = {"instance_type": "t3.large", "tags": {"env": "prod"}, "extra_sg": "sg-999"}
        res = detect_state_drift(declared, actual)
        assert res["status"] == "ok"
        assert res["has_drift"] is True
        assert res["drift_count"] == 2  # instance_type mismatch + extra_sg unexpected

    def test_estimate_resource_costs(self) -> None:
        resources = [
            {"type": "aws_instance", "instance_type": "t3.micro", "name": "app-server"},
            {"type": "aws_db_instance", "instance_type": "db.t3.micro", "name": "postgres"},
        ]
        res = estimate_resource_costs(resources)
        assert res["status"] == "ok"
        assert res["estimated_monthly_usd"] == 22.50
