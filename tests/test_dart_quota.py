# -*- coding: utf-8 -*-
from pathlib import Path

import pytest

from core.dart_client import DartQuotaExceeded, DartQuotaLedger


def test_dart_quota_soft_stop(tmp_path: Path):
    path = tmp_path / "dart_quota.json"
    ledger = DartQuotaLedger(path, soft_limit=3, hard_limit=40_000)
    ledger.reserve(1)
    ledger.reserve(1)
    st = ledger.state()
    assert st.count == 2
    assert st.remaining_soft == 1
    ledger.reserve(1)
    with pytest.raises(DartQuotaExceeded):
        ledger.reserve(1)
