from pathlib import Path

from app.reviewer.pack_loader import load_pack
from app.reviewer.prompts import (
    render_consolidator_instructions,
    render_reviewer_instructions,
)


PACKS_DIR = Path(__file__).resolve().parent.parent / "app" / "packs"


def test_reviewer_instructions_inline_guidelines():
    pack = load_pack("tone-and-hedging", PACKS_DIR)
    rendered = render_reviewer_instructions(pack)
    assert "Tone & Hedging" in rendered
    assert "tone.definitive_language" in rendered
    # Must include JSON output contract.
    assert '"issues"' in rendered


def test_consolidator_instructions_inline_guidelines():
    pack = load_pack("tone-and-hedging", PACKS_DIR)
    rendered = render_consolidator_instructions(pack)
    assert "Tone & Hedging" in rendered
    assert "keep" in rendered
    assert "confidence" in rendered
