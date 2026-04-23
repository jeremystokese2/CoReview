from __future__ import annotations

from jinja2 import Environment, StrictUndefined

from app.reviewer.pack_loader import Pack


_env = Environment(
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
    undefined=StrictUndefined,
)


def render_reviewer_instructions(pack: Pack) -> str:
    template = _env.from_string(pack.reviewer_template)
    return template.render(pack=pack, guidelines=pack.guidelines)


def render_consolidator_instructions(pack: Pack) -> str:
    template = _env.from_string(pack.consolidator_template)
    return template.render(pack=pack, guidelines=pack.guidelines)
