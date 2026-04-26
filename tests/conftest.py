"""Top-level pytest configuration.

Registers hypothesis profiles BEFORE any test module is imported so the
HYPOTHESIS_PROFILE env var (set by CI) takes effect on the first
@hypothesis.given(...) decorator that runs. The previous registration
inside test_property_based.py only fired when that file was first
imported, by which point hypothesis had already initialized its default
settings — leading to 100-example runs under coverage that blew past the
GitHub-hosted Linux runner's RAM ceiling.
"""

from __future__ import annotations

import os

try:
    from hypothesis import HealthCheck, Verbosity, settings

    settings.register_profile(
        "ci",
        max_examples=25,
        deadline=None,
        verbosity=Verbosity.normal,
        database=None,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
    )
    settings.register_profile(
        "dev",
        max_examples=10,
        deadline=None,
        verbosity=Verbosity.normal,
    )
    settings.register_profile(
        "thorough",
        max_examples=1000,
        deadline=None,
        verbosity=Verbosity.verbose,
    )
    settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "ci"))
except ImportError:
    # hypothesis not installed; tests that need it skip themselves.
    pass
