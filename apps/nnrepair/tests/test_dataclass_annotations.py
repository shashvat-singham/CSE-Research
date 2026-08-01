"""Guard against the Python 3.14 dataclass crash.

``dataclasses._is_type`` contains an unguarded dereference::

    ns = sys.modules.get(cls.__module__).__dict__

It is reached only when a dataclass field's annotation is a **string**, which
is what ``from __future__ import annotations`` makes every annotation. If the
defining module is not in ``sys.modules`` at that moment, the lookup returns
``None`` and the ``@dataclass`` decorator raises ``AttributeError``.

That is not hypothetical: Streamlit's hot-reload machinery evicts local modules
from ``sys.modules``, and on Streamlit Community Cloud (Python 3.14) it took
the whole app down at import time on ``nnrepair.experiments``.

Keeping real type objects on dataclass fields makes the path unreachable. This
test enforces that, because the failure only appears on 3.14 and would sail
through local runs on older interpreters.
"""

import dataclasses
import importlib
import pkgutil

import pytest

import nnrepair


def dataclass_types():
    """Every dataclass defined anywhere in the package."""
    found = []
    for info in pkgutil.walk_packages(nnrepair.__path__, prefix="nnrepair."):
        module = importlib.import_module(info.name)
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type)
                and dataclasses.is_dataclass(obj)
                and obj.__module__ == info.name
            ):
                found.append(obj)
    return found


def test_the_package_defines_dataclasses():
    """Sanity check, so the assertions below are not vacuously true."""
    assert len(dataclass_types()) >= 5


@pytest.mark.parametrize("cls", dataclass_types(), ids=lambda c: f"{c.__module__}.{c.__name__}")
def test_field_annotations_are_not_strings(cls):
    string_fields = [f.name for f in dataclasses.fields(cls) if isinstance(f.type, str)]
    assert not string_fields, (
        f"{cls.__module__}.{cls.__name__} has string annotations on "
        f"{string_fields}. That reaches dataclasses._is_type, which dereferences "
        "sys.modules.get(cls.__module__) without a None check and crashes under "
        "Streamlit on Python 3.14. Drop 'from __future__ import annotations' "
        "from this module, or unquote the annotation."
    )


@pytest.mark.parametrize("cls", dataclass_types(), ids=lambda c: f"{c.__module__}.{c.__name__}")
def test_building_the_dataclass_never_consults_is_type(cls, monkeypatch):
    """Re-run ``@dataclass`` and assert the unguarded helper is never called.

    Asserting on the call rather than on a raised error keeps this meaningful
    across interpreter versions. ``_process_class`` also dereferences
    ``sys.modules[cls.__module__]`` directly, but that call site gained a
    membership check in 3.12; ``_is_type`` did not, which is why 3.14 fails
    there specifically.
    """
    called: list[str] = []

    def tripwire(annotation, klass, *args, **kwargs):
        called.append(annotation)
        return False

    monkeypatch.setattr(dataclasses, "_is_type", tripwire)

    rebuilt = type(
        cls.__name__,
        (),
        {"__annotations__": dict(cls.__annotations__), "__module__": __name__},
    )
    dataclasses.dataclass(rebuilt)

    assert not called, (
        f"{cls.__module__}.{cls.__name__} routed {called} through "
        "dataclasses._is_type, which crashes when the defining module is "
        "absent from sys.modules."
    )
