import pytest

from portable_java_manager import PortableJavaManager


def test_offer_portable_java_noninteractive_yes():
    m = PortableJavaManager(interactive_mode=False, non_interactive_answer=True)
    assert m.offer_portable_java(True, "No system Java", "17") is True


def test_offer_portable_java_noninteractive_no():
    m = PortableJavaManager(interactive_mode=False, non_interactive_answer=False)
    assert m.offer_portable_java(True, "No system Java", "17") is False
