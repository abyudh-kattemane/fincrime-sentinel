"""Placeholder test to give CI something to pass on day 1.
Replace with real tests as modules are built."""


def test_project_imports() -> None:
    """Confirm the src package is importable."""
    import src

    assert src is not None


def test_sanity() -> None:
    """Sanity check — if this fails, something is very wrong."""
    assert 1 + 1 == 2
