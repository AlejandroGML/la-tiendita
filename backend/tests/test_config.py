"""Tests for cache-related settings in ``app.config.Settings``.

Verifies the TTL defaults mandated by the redis-cache-layer spec, that env
variables override them, and that ``CACHE_ENABLED`` parses to a real bool.
"""

import os

import pytest


def _make_settings(monkeypatch, **overrides):
    """Build an isolated ``Settings`` instance ignoring the on-disk ``.env``.

    The module-level ``settings`` singleton is created at import time, so to
    exercise env overrides we instantiate a fresh object with the cache env
    vars set on the environment and the secret/database vars stubbed.
    """
    # Required-by-base-settings values that have no default.
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://x:x@localhost:5432/x")
    monkeypatch.setenv("SECRET_KEY", "unit-test-secret")
    # Clear any cache env that could leak from the host environment.
    for key in (
        "REDIS_URL",
        "CACHE_ENABLED",
        "CACHE_PREFIX",
        "CACHE_TTL_PRODUCTS_LIST",
        "CACHE_TTL_PRODUCTS_DETAIL",
        "CACHE_TTL_CATEGORIES_LIST",
        "CACHE_TTL_PROMOTIONS_ACTIVE",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in overrides.items():
        monkeypatch.setenv(key, str(value))

    from app.config import Settings

    return Settings(_env_file=None)


def test_cache_ttl_defaults(monkeypatch):
    settings = _make_settings(monkeypatch)

    assert settings.CACHE_TTL_PRODUCTS_LIST == 60
    assert settings.CACHE_TTL_PRODUCTS_DETAIL == 300
    assert settings.CACHE_TTL_CATEGORIES_LIST == 600
    assert settings.CACHE_TTL_PROMOTIONS_ACTIVE == 120


def test_cache_ttl_env_override(monkeypatch):
    settings = _make_settings(
        monkeypatch,
        CACHE_TTL_PRODUCTS_LIST="10",
        CACHE_TTL_PROMOTIONS_ACTIVE="7",
    )

    assert settings.CACHE_TTL_PRODUCTS_LIST == 10
    assert settings.CACHE_TTL_PROMOTIONS_ACTIVE == 7
    # Untouched fields keep their defaults.
    assert settings.CACHE_TTL_PRODUCTS_DETAIL == 300


def test_cache_enabled_false_is_bool(monkeypatch):
    settings = _make_settings(monkeypatch, CACHE_ENABLED="false")

    assert settings.CACHE_ENABLED is False
    assert isinstance(settings.CACHE_ENABLED, bool)


def test_cache_prefix_and_redis_url_defaults(monkeypatch):
    settings = _make_settings(monkeypatch)

    assert settings.CACHE_PREFIX == "tiendita"
    assert settings.REDIS_URL == "redis://localhost:6379/0"
