"""PEP 302/451 Zero-Dependency Mock Virtualization for heavy ML packages."""

from __future__ import annotations

import contextlib
import importlib.machinery
import sys
import types
from typing import Any


class _DynamicProxyMeta(type):
    """Metaclass allowing arbitrary class attribute resolution and subclassing."""

    def __getattr__(cls, name: str) -> Any:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        new_cls = _DynamicProxyMeta(name, (_DynamicProxyClass,), {})
        setattr(cls, name, new_cls)
        return new_cls

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        instance = super().__call__(*args, **kwargs)
        return instance


class _DynamicProxyClass(metaclass=_DynamicProxyMeta):
    """Dynamic class that can be called, instantiated, and accessed recursively."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        val = _DynamicProxyClass()
        setattr(self, name, val)
        return val

    @classmethod
    def __subclasscheck__(cls, subclass: Any) -> bool:
        return True

    @classmethod
    def __instancecheck__(cls, instance: Any) -> bool:
        return True


class MockModule(types.ModuleType):
    """Dynamic synthetic mock module allowing arbitrary attribute and subclass access."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.__file__ = f"<mock {name}>"
        self.__path__: list[str] = []
        self.__loader__ = None
        self.__spec__ = None

    def __getattr__(self, name: str) -> Any:
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(name)
        cls = _DynamicProxyMeta(name, (_DynamicProxyClass,), {})
        setattr(self, name, cls)
        return cls


class ZeroDepMockFinder:
    """PEP 302/451 meta-path hook for synthesizing mock specs on uninstalled heavy packages."""

    def __init__(self, packages_to_mock: tuple[str, ...]) -> None:
        self.packages = set(packages_to_mock)

    def find_spec(self, fullname: str, path: Any = None, target: Any = None) -> Any:
        root_pkg = fullname.split(".")[0]
        if root_pkg in self.packages:
            spec = importlib.machinery.ModuleSpec(fullname, ZeroDepMockLoader(fullname))
            spec.submodule_search_locations = []
            return spec
        return None


class ZeroDepMockLoader:
    """Loader returning synthetic MockModule instances."""

    def __init__(self, fullname: str) -> None:
        self.fullname = fullname

    def create_module(self, spec: Any) -> Any:
        return MockModule(self.fullname)

    def exec_module(self, module: Any) -> None:
        pass


@contextlib.contextmanager
def virtualize_imports(
    packages: tuple[str, ...] = (
        "torch",
        "tensorflow",
        "jax",
        "flax",
        "transformers",
        "datasets",
        "accelerate",
    ),
):
    """Context manager to intercept and virtualize missing heavy dependencies."""
    finder = ZeroDepMockFinder(packages)
    sys.meta_path.insert(0, finder)
    orig_modules = set(sys.modules.keys())
    try:
        yield finder
    finally:
        if finder in sys.meta_path:
            sys.meta_path.remove(finder)
        for mod_name in list(sys.modules.keys()):
            if mod_name not in orig_modules:
                root = mod_name.split(".")[0]
                if root in finder.packages:
                    sys.modules.pop(mod_name, None)


__all__ = [
    "MockModule",
    "ZeroDepMockFinder",
    "ZeroDepMockLoader",
    "virtualize_imports",
]
