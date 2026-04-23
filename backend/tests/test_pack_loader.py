from pathlib import Path

import pytest

from app.reviewer.pack_loader import list_packs, load_pack


PACKS_DIR = Path(__file__).resolve().parent.parent / "app" / "packs"


def test_tone_and_hedging_loads():
    pack = load_pack("tone-and-hedging", PACKS_DIR)
    assert pack.id == "tone-and-hedging"
    assert pack.name
    assert pack.guidelines
    assert "tone.definitive_language" in pack.guidelines
    assert pack.can_rewrite is False


def test_list_packs_includes_tone_and_hedging():
    summaries = list_packs(PACKS_DIR)
    ids = [s.id for s in summaries]
    assert "tone-and-hedging" in ids


def test_load_missing_pack():
    with pytest.raises(FileNotFoundError):
        load_pack("does-not-exist", PACKS_DIR)
