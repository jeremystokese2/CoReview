from __future__ import annotations

import uuid
from datetime import datetime, timezone

from bs4 import BeautifulSoup
from bs4.element import Tag

from app.db import insert_snapshot
from app.models import Snapshot


BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li"}

# Attributes that leak inline event handlers or layout noise we don't need.
_EVENT_ATTR_PREFIXES = ("on",)
_NOISY_ATTRS = {"class", "lang", "align", "dir"}


def normalise_html(raw_html: str) -> tuple[str, int]:
    """Normalise Office.js HTML for snapshot storage.

    - Parse with lxml.
    - Strip <script>, <style>, inline event handlers.
    - Assign stable data-rid="p_{n}" on each block-level element (p/h1-6/li).
    - Preserve heading hierarchy.
    - Returns (normalised_html, paragraph_count).
    """
    soup = BeautifulSoup(raw_html or "", "lxml")

    for tag in soup.find_all(["script", "style", "meta", "link"]):
        tag.decompose()

    # If the input was a full HTML document, operate on <body>; otherwise use root.
    root: Tag = soup.body if soup.body else soup

    counter = 0
    for el in root.find_all(True):
        if not isinstance(el, Tag):
            continue

        # Strip event handlers and noisy Office attrs.
        for attr_name in list(el.attrs.keys()):
            lower = attr_name.lower()
            if lower.startswith(_EVENT_ATTR_PREFIXES):
                del el.attrs[attr_name]
                continue
            if lower in _NOISY_ATTRS or lower.startswith("mso-"):
                del el.attrs[attr_name]
                continue
            if lower == "style":
                # Strip style entirely for the tracer bullet — we don't need it.
                del el.attrs[attr_name]

        if el.name in BLOCK_TAGS:
            counter += 1
            el["data-rid"] = f"p_{counter}"

    # Render just the body contents if we started with a full doc, otherwise the root.
    if soup.body:
        html_out = "".join(str(c) for c in soup.body.children).strip()
    else:
        html_out = str(soup).strip()

    return html_out, counter


async def create_snapshot(raw_html: str) -> Snapshot:
    normalised, count = normalise_html(raw_html)
    snap = Snapshot(
        id=f"s_{uuid.uuid4().hex[:12]}",
        created_at=datetime.now(timezone.utc),
        html=normalised,
        paragraph_count=count,
    )
    await insert_snapshot(snap)
    return snap
