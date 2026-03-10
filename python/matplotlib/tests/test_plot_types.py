"""Tests for new plot types."""

import math


class TestDrawWedge:
    def test_renderer_base_raises(self):
        from matplotlib.backend_bases import RendererBase
        r = RendererBase(100, 100, 72)
        try:
            r.draw_wedge(50, 50, 40, 0, 90, '#ff0000')
            assert False, "Should have raised NotImplementedError"
        except NotImplementedError:
            pass

    def test_svg_draw_wedge_quarter(self):
        from matplotlib._svg_backend import RendererSVG
        r = RendererSVG(200, 200, 72)
        r.draw_wedge(100, 100, 50, 0, 90, '#ff0000')
        svg = r.get_result()
        assert '<path' in svg
        assert '#ff0000' in svg

    def test_svg_draw_wedge_full_circle(self):
        from matplotlib._svg_backend import RendererSVG
        r = RendererSVG(200, 200, 72)
        r.draw_wedge(100, 100, 50, 0, 360, '#00ff00')
        svg = r.get_result()
        assert '#00ff00' in svg
        assert '<circle' in svg

    def test_pil_draw_wedge(self):
        from matplotlib._pil_backend import RendererPIL
        r = RendererPIL(200, 200, 72)
        r.draw_wedge(100, 100, 50, 0, 90, '#ff0000')
        result = r.get_result()
        assert isinstance(result, bytes)
        assert len(result) > 0


class TestWedgePatch:
    def test_wedge_creation(self):
        from matplotlib.patches import Wedge
        w = Wedge((0, 0), 1.0, 0, 90)
        assert w._center == (0, 0)
        assert w._r == 1.0
        assert w._theta1 == 0
        assert w._theta2 == 90

    def test_wedge_color(self):
        from matplotlib.patches import Wedge
        w = Wedge((0, 0), 1.0, 0, 90, facecolor='red')
        fc = w.get_facecolor()
        assert fc[0] == 1.0  # red channel

    def test_wedge_draw(self):
        from matplotlib.patches import Wedge
        from matplotlib._svg_backend import RendererSVG
        from matplotlib.backend_bases import AxesLayout
        w = Wedge((5, 5), 3.0, 0, 180, facecolor='blue')
        renderer = RendererSVG(200, 200, 72)
        layout = AxesLayout(10, 10, 180, 180, 0, 10, 0, 10)
        w.draw(renderer, layout)
        svg = renderer.get_result()
        assert '<path' in svg or '<circle' in svg


class TestStemContainer:
    def test_stem_container_creation(self):
        from matplotlib.container import StemContainer
        sc = StemContainer(('marker', ['s1', 's2'], 'base'), label='test')
        assert sc.markerline == 'marker'
        assert sc.stemlines == ['s1', 's2']
        assert sc.baseline == 'base'
        assert sc.get_label() == 'test'
