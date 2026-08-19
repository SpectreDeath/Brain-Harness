"""Tests for Domain 4: Migration Assistant plugin."""

from __future__ import annotations

import pytest

from plugins.migration_assistant.main import (
    check_pydantic_v2_readiness,
    check_python_version_compat,
)


@pytest.mark.unit
class TestMigrationAssistantPlugin:
    def test_check_pydantic_v2_readiness(self) -> None:
        v1_code = (
            "from pydantic import BaseModel, validator\n"
            "class UserModel(BaseModel):\n"
            "    name: str\n"
            "    class Config:\n"
            "        orm_mode = True\n"
            "    @validator('name')\n"
            "    def validate_name(cls, v):\n"
            "        return v\n"
        )
        res = check_pydantic_v2_readiness(v1_code)
        assert res["status"] == "ok"
        assert res["ready_for_v2"] is False
        rules = [iss["rule"] for iss in res["issues"]]
        assert "PydanticV1ConfigClass" in rules
        assert "PydanticV1ValidatorDecorator" in rules

    def test_check_python_version_compat(self) -> None:
        legacy_code = (
            "from typing import Union, Optional\n"
            "def foo(x: Union[int, str]) -> Optional[bool]:\n"
            "    pass\n"
        )
        res = check_python_version_compat(legacy_code)
        assert res["status"] == "ok"
        assert res["modern_python_compliant"] is False
        assert res["suggestions_count"] >= 2
