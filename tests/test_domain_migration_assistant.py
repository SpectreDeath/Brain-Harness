"""Tests for Migration Assistant plugin."""

from __future__ import annotations

import pytest

from harness.kernel.context import ServiceContext
from harness.services.migration_assistant import (
    MIGRATION_ASSISTANT_KEY,
    MigrationAssistantService,
    PydanticMigrationResult,
    PythonCompatResult,
)
from plugins.software_engineering.migration_assistant.main import (
    MigrationAssistantPlugin,
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

    @pytest.mark.asyncio
    async def test_migration_assistant_plugin_ioc_lifecycle(self) -> None:
        plugin = MigrationAssistantPlugin()
        assert plugin.name == "plugin.migration_assistant"
        assert MIGRATION_ASSISTANT_KEY in plugin.provides

        ctx = ServiceContext()
        await plugin.on_load(ctx)
        await plugin.on_enable()

        service = ctx.require(MIGRATION_ASSISTANT_KEY)
        assert isinstance(service, MigrationAssistantService)

        pydantic_res = service.check_pydantic_v2_readiness("class User(BaseModel): name: str")
        assert isinstance(pydantic_res, PydanticMigrationResult)
        assert pydantic_res.status == "ok"
        assert pydantic_res.ready_for_v2 is True

        compat_res = service.check_python_version_compat("def test(x: int | str) -> bool | None: pass")
        assert isinstance(compat_res, PythonCompatResult)
        assert compat_res.status == "ok"
        assert compat_res.modern_python_compliant is True

        await plugin.on_disable()
        await plugin.on_unload()
