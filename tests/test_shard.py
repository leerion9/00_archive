"""Tests for core/shard.py."""

from __future__ import annotations

import pytest

from core.shard import assign_worker, parse_task_id, task_id


def test_task_id_roundtrip():
    assert task_id("005930", 2025) == "005930:2025"
    assert parse_task_id("005930:2025") == ("005930", 2025)


def test_assign_worker_pc_only_mode():
    assert assign_worker("005930", 2026, "pc", pc_year_min=None) is True
    assert assign_worker("005930", 2026, "laptop", pc_year_min=None) is False


def test_assign_worker_year_split():
    assert assign_worker("005930", 2026, "pc", pc_year_min=2013) is True
    assert assign_worker("005930", 2012, "laptop", pc_year_min=2013) is True
