from __future__ import annotations

from labtools import __version__, smoke_test


def test_package_smoke_payload_covers_public_modules() -> None:
    payload = smoke_test()

    assert payload["version"] == __version__
    assert payload["modules"] == (
        "labtools.calculators",
        "labtools.reagent_templates",
        "labtools.western_blot",
        "labtools.pcr_qpcr",
        "labtools.cell_culture",
        "labtools.elisa",
    )
