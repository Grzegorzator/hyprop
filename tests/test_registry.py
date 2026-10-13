"""Tests for hyprop.core.registry."""

import pytest

from hyprop.core.exceptions import RegistryError
from hyprop.core.registry import get_model, list_models, register_model


def test_register_and_get():
    @register_model("regression", "dummy_law")
    class DummyLaw:
        pass

    assert get_model("regression", "dummy_law") is DummyLaw
    assert "dummy_law" in list_models("regression")["regression"]


def test_default_name_is_lowercase_class_name():
    @register_model("tank")
    class MyTank:
        pass

    assert get_model("tank", "mytank") is MyTank


def test_unknown_category_rejected():
    with pytest.raises(RegistryError):
        register_model("warp_drive")


def test_duplicate_registration_rejected():
    @register_model("injector", "dup")
    class A:
        pass

    with pytest.raises(RegistryError):

        @register_model("injector", "dup")
        class B:
            pass


def test_missing_model_lists_available():
    with pytest.raises(RegistryError, match="Available"):
        get_model("geometry", "dodecahedron")
