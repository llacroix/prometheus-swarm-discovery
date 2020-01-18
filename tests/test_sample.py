# -*- coding: utf-8 -*-
import pytest


def f():
    raise Exception("test")


def test_something():
    with pytest.raises(Exception):
        f()
