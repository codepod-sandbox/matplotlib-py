# Copyright (c) 2024 CodePod Contributors — BSD 3-Clause License
# Ported from lib/matplotlib/tests/test_text.py (annotation section)
import pytest


def test_renderer_svg_draw_arrow_no_error():
    """RendererSVG.draw_arrow must produce valid SVG with a path element."""
    from matplotlib._svg_backend import RendererSVG
    r = RendererSVG(200, 200, 100)
    r.draw_arrow(10, 100, 150, 50, '->', '#ff0000', 1.5)
    svg = r.get_result()
    assert '<path' in svg or '<line' in svg
    assert 'marker-end' in svg or 'polygon' in svg.lower() or '<path' in svg


def test_renderer_svg_draw_arrow_no_head():
    """draw_arrow with style '-' must draw a line without arrowhead."""
    from matplotlib._svg_backend import RendererSVG
    r = RendererSVG(200, 200, 100)
    r.draw_arrow(10, 100, 150, 50, '-', '#000000', 1.0)
    svg = r.get_result()
    assert '<polyline' in svg or '<line' in svg or '<path' in svg


def test_renderer_pil_draw_arrow_no_error():
    """RendererPIL.draw_arrow must not raise."""
    from matplotlib._pil_backend import RendererPIL
    r = RendererPIL(200, 200, 100)
    r.draw_arrow(10, 100, 150, 50, '->', '#ff0000', 1.5)
    # Just check it produces bytes without error
    result = r.get_result()
    assert len(result) > 0
