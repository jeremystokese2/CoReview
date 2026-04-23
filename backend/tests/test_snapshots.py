from app.snapshots import normalise_html


def test_block_elements_get_sequential_data_rid():
    html = "<p>one</p><h2>heading</h2><p>two</p><ul><li>three</li></ul>"
    out, count = normalise_html(html)
    assert count == 4
    assert 'data-rid="p_1"' in out
    assert 'data-rid="p_2"' in out
    assert 'data-rid="p_3"' in out
    assert 'data-rid="p_4"' in out


def test_scripts_styles_and_event_handlers_stripped():
    html = (
        "<p onclick=\"evil()\" style='color:red'>hi</p>"
        "<script>alert(1)</script>"
        "<style>body{}</style>"
    )
    out, count = normalise_html(html)
    assert "<script" not in out
    assert "<style" not in out
    assert "onclick" not in out
    assert "style=" not in out
    assert count == 1


def test_headings_preserved():
    html = "<h1>Intro</h1><p>body</p><h3>deep</h3>"
    out, _ = normalise_html(html)
    assert "<h1" in out
    assert "<h3" in out


def test_empty_input():
    out, count = normalise_html("")
    assert out == ""
    assert count == 0
