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


def test_annotate_default_arrow():
    """ax.annotate with arrowprops must render without error."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.annotate('hi', xy=(0.5, 0.5), xytext=(0.2, 0.8),
                arrowprops=dict(arrowstyle='->'))
    svg = fig.to_svg()
    assert len(svg) > 0
    plt.close('all')


def test_annotate_no_arrowprops():
    """ax.annotate without arrowprops renders only text."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.annotate('label', xy=(0.5, 0.5))
    svg = fig.to_svg()
    assert 'label' in svg
    plt.close('all')


def test_annotate_arrowprops_styles():
    """Multiple arrowstyle strings must not raise."""
    import matplotlib.pyplot as plt
    for style in ['->', '<-', '<->', '-', 'fancy']:
        fig, ax = plt.subplots()
        ax.annotate('x', xy=(0.5, 0.5), xytext=(0.1, 0.9),
                    arrowprops=dict(arrowstyle=style))
        fig.to_svg()  # must not raise
        plt.close('all')


def test_fancy_arrow_patch_draw():
    """FancyArrowPatch.draw must call renderer.draw_arrow."""
    from matplotlib.patches import FancyArrowPatch
    from matplotlib.backend_bases import AxesLayout
    from matplotlib.scale import LinearScale

    class MockRenderer:
        def __init__(self):
            self.draw_arrow_calls = []
        def draw_arrow(self, *args, **kwargs):
            self.draw_arrow_calls.append(args)

    layout = AxesLayout(0, 0, 100, 100, 0, 1, 0, 1,
                        LinearScale(), LinearScale())
    renderer = MockRenderer()
    patch = FancyArrowPatch((0.1, 0.2), (0.8, 0.7),
                             arrowstyle='->', color='red', linewidth=1.5)
    patch.draw(renderer, layout)
    assert len(renderer.draw_arrow_calls) == 1
