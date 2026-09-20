"""Offline dependency-contract test (WP31R2).

Prevents the CI-environment gap exposed by workflow run 35469646309 from
recurring: `book/_config.yml` enables the `sphinxcontrib.mermaid` Sphinx
extension (WP27, for the Exercise 4 nested-cross-validation diagram), but the
distribution providing it was never pinned in the requirements file CI
actually installs from, so "Build Jupyter Book" failed with
`ModuleNotFoundError: No module named 'sphinxcontrib.mermaid'` even though it
built successfully in every local `.venv` that happened to have the package
installed out of band.

Deliberately narrow: a small explicit extension -> PyPI distribution map, not
a universal import-to-PyPI dependency resolver.

Run:
    .venv/bin/python -m unittest discover -s tests -p 'test_deploy_dependency_contract.py'
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

# Sphinx extension module name -> the PyPI distribution that provides it.
# Extend this map, narrowly, whenever book/_config.yml enables a new
# third-party extra_extension that isn't part of jupyter-book itself.
EXTENSION_DISTRIBUTIONS = {
    "sphinxcontrib.mermaid": "sphinxcontrib-mermaid",
}


def _extra_extensions() -> list[str]:
    cfg = yaml.safe_load((REPO_ROOT / "book" / "_config.yml").read_text(encoding="utf-8"))
    return cfg.get("sphinx", {}).get("extra_extensions", [])


def _requirements_path() -> Path:
    """The requirements file `.github/workflows/deploy.yml` actually installs
    from (`pip install -r <file>`), not merely assumed to be requirements.txt."""
    workflow = (REPO_ROOT / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")
    match = re.search(r"pip install -r (\S+)", workflow)
    if not match:
        raise AssertionError(
            "deploy.yml no longer installs Python dependencies with "
            "'pip install -r <file>'; this test's assumption about the "
            "canonical requirements file is stale and must be updated"
        )
    return REPO_ROOT / match.group(1)


def _pinned_versions(requirements_text: str) -> dict[str, str]:
    pins: dict[str, str] = {}
    for line in requirements_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+-]+)$", line)
        if m:
            pins[m.group(1).lower()] = m.group(2)
    return pins


class MermaidDependencyContract(unittest.TestCase):
    def test_mermaid_extension_is_still_declared_and_mapped(self):
        # Guard the guard: if book/_config.yml ever stops enabling Mermaid,
        # or the extension name changes, this should fail loudly rather than
        # let the coverage below silently become a no-op.
        self.assertIn(
            "sphinxcontrib.mermaid",
            _extra_extensions(),
            "book/_config.yml no longer lists sphinxcontrib.mermaid under "
            "sphinx.extra_extensions -- update this test if Mermaid support "
            "was intentionally removed (it must stay available for the "
            "Exercise 4 nested-CV diagram).",
        )
        self.assertIn("sphinxcontrib.mermaid", EXTENSION_DISTRIBUTIONS)

    def test_every_enabled_extension_with_a_known_distribution_is_exactly_pinned(self):
        requirements_path = _requirements_path()
        pins = _pinned_versions(requirements_path.read_text(encoding="utf-8"))

        for extension in _extra_extensions():
            distribution = EXTENSION_DISTRIBUTIONS.get(extension)
            if distribution is None:
                continue  # part of jupyter-book itself, or not yet tracked here
            self.assertIn(
                distribution.lower(),
                pins,
                f"book/_config.yml enables Sphinx extension {extension!r}, which "
                f"requires the distribution {distribution!r}, but "
                f"{requirements_path.relative_to(REPO_ROOT)} (installed by "
                f".github/workflows/deploy.yml) does not pin an exact version of "
                f"it. CI will fail 'Build Jupyter Book' with ModuleNotFoundError, "
                f"exactly as in run 35469646309.",
            )


if __name__ == "__main__":
    unittest.main()
