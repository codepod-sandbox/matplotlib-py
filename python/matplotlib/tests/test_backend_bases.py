"""
Tests for backend_bases (RendererBase, AxesLayout) and the new
RendererSVG / RendererPIL classes.
"""

import re
import pytest


# ===================================================================
# TestRendererBase
# ===================================================================

class TestRendererBase:
    """RendererBase stores dimensions and all methods raise NotImplementedError."""

    def test_init_stores_dimensions(self):
        from matplotlib.backend_bases import RendererBase
        r = RendererBase(800, 600, 100)
        assert r.width == 800
        assert r.height == 600
        assert r.dpi == 100

    @pytest.mark.parametrize("method,args", [
        ("draw_line", ([0, 1], [0, 1], "#000", 1.5, "-")),
        ("draw_markers", ([0, 1], [0, 1], "#000", 3)),
        ("draw_rect", (10, 20, 100, 50, "#000", None)),
        ("draw_circle", (50, 50, 10, "#f00")),
        ("draw_polygon", ([(0, 0), (1, 1), (2, 0)], "#00f", 0.5)),
        ("draw_text", (100, 200, "hello", 12, "#000", "left")),
        ("set_clip_rect", (0, 0, 100, 100)),
        ("clear_clip", ()),
        ("get_result", ()),
    ])
    def test_methods_raise_not_implemented(self, method, args):
        from matplotlib.backend_bases import RendererBase
        r = RendererBase(800, 600, 100)
        with pytest.raises(NotImplementedError):
            getattr(r, method)(*args)


# ===================================================================
# TestAxesLayout
# ===================================================================

class TestAxesLayout:
    """AxesLayout stores geometry and provides correct coordinate transforms."""

    def test_init_stores_geometry(self):
        from matplotlib.backend_bases import AxesLayout
        layout = AxesLayout(70, 40, 500, 400, 0.0, 10.0, 0.0, 5.0)
        assert layout.plot_x == 70
        assert layout.plot_y == 40
        assert layout.plot_w == 500
        assert layout.plot_h == 400
        assert layout.xmin == 0.0
        assert layout.xmax == 10.0
        assert layout.ymin == 0.0
        assert layout.ymax == 5.0

    def test_sx_maps_xmin_to_plot_x(self):
        from matplotlib.backend_bases import AxesLayout
        layout = AxesLayout(70, 40, 500, 400, 0.0, 10.0, 0.0, 5.0)
        assert abs(layout.sx(0.0) - 70.0) < 1e-9

    def test_sx_maps_xmax_to_plot_x_plus_plot_w(self):
        from matplotlib.backend_bases import AxesLayout
        layout = AxesLayout(70, 40, 500, 400, 0.0, 10.0, 0.0, 5.0)
        assert abs(layout.sx(10.0) - 570.0) < 1e-9

    def test_sx_midpoint(self):
        from matplotlib.backend_bases import AxesLayout
        layout = AxesLayout(70, 40, 500, 400, 0.0, 10.0, 0.0, 5.0)
        assert abs(layout.sx(5.0) - 320.0) < 1e-9

    def test_sy_maps_ymin_to_plot_y_plus_plot_h(self):
        """ymin maps to bottom of plot (plot_y + plot_h) because y is inverted."""
        from matplotlib.backend_bases import AxesLayout
        layout = AxesLayout(70, 40, 500, 400, 0.0, 10.0, 0.0, 5.0)
        assert abs(layout.sy(0.0) - 440.0) < 1e-9

    def test_sy_maps_ymax_to_plot_y(self):
        """ymax maps to top of plot (plot_y) because y is inverted."""
        from matplotlib.backend_bases import AxesLayout
        layout = AxesLayout(70, 40, 500, 400, 0.0, 10.0, 0.0, 5.0)
        assert abs(layout.sy(5.0) - 40.0) < 1e-9

    def test_sy_midpoint(self):
        from matplotlib.backend_bases import AxesLayout
        layout = AxesLayout(70, 40, 500, 400, 0.0, 10.0, 0.0, 5.0)
        assert abs(layout.sy(2.5) - 240.0) < 1e-9


# ===================================================================
# TestRendererSVG
# ===================================================================

class TestRendererSVG:
    """RendererSVG produces correct SVG elements."""

    def _make_renderer(self, w=800, h=600, dpi=100):
        from matplotlib._svg_backend import RendererSVG
        return RendererSVG(w, h, dpi)

    def test_get_result_is_valid_svg(self):
        r = self._make_renderer()
        svg = r.get_result()
        assert svg.startswith('<svg ')
        assert svg.strip().endswith('</svg>')
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg

    def test_draw_line_produces_polyline(self):
        r = self._make_renderer()
        r.draw_line([0, 100], [0, 100], "#ff0000", 2.0, "-")
        svg = r.get_result()
        assert '<polyline' in svg
        assert 'stroke="#ff0000"' in svg

    def test_draw_line_dashed(self):
        r = self._make_renderer()
        r.draw_line([0, 100], [0, 100], "#000", 1.5, "--")
        svg = r.get_result()
        assert 'stroke-dasharray' in svg

    def test_draw_line_dotted(self):
        r = self._make_renderer()
        r.draw_line([0, 100], [0, 100], "#000", 1.5, ":")
        svg = r.get_result()
        assert 'stroke-dasharray="2,2"' in svg

    def test_draw_markers_produces_circles(self):
        r = self._make_renderer()
        r.draw_markers([10, 20, 30], [40, 50, 60], "#00ff00", 4)
        svg = r.get_result()
        assert svg.count('<circle') == 3

    def test_draw_rect_produces_rect(self):
        r = self._make_renderer()
        r.draw_rect(10, 20, 100, 50, "#0000ff", None)
        svg = r.get_result()
        assert '<rect ' in svg
        assert 'x="10"' in svg

    def test_draw_rect_with_fill(self):
        r = self._make_renderer()
        r.draw_rect(10, 20, 100, 50, "#000", "#ff0000")
        svg = r.get_result()
        assert 'fill="#ff0000"' in svg

    def test_draw_circle_produces_circle(self):
        r = self._make_renderer()
        r.draw_circle(50, 60, 10, "#f00")
        svg = r.get_result()
        assert '<circle' in svg
        assert 'cx="50"' in svg
        assert 'cy="60"' in svg
        assert 'r="10"' in svg

    def test_draw_polygon_produces_polygon(self):
        r = self._make_renderer()
        r.draw_polygon([(0, 0), (100, 0), (50, 50)], "#00f", 0.5)
        svg = r.get_result()
        assert '<polygon' in svg
        assert 'fill-opacity="0.5"' in svg

    def test_draw_text_produces_text(self):
        r = self._make_renderer()
        r.draw_text(100, 200, "Hello World", 14, "#000", "left")
        svg = r.get_result()
        assert '<text' in svg
        assert 'Hello World' in svg
        assert 'text-anchor="start"' in svg

    def test_draw_text_center_anchor(self):
        r = self._make_renderer()
        r.draw_text(100, 200, "Centered", 14, "#000", "center")
        svg = r.get_result()
        assert 'text-anchor="middle"' in svg

    def test_draw_text_right_anchor(self):
        r = self._make_renderer()
        r.draw_text(100, 200, "Right", 14, "#000", "right")
        svg = r.get_result()
        assert 'text-anchor="end"' in svg

    def test_draw_text_escapes_html(self):
        r = self._make_renderer()
        r.draw_text(100, 200, "<b>bold</b>", 14, "#000", "left")
        svg = r.get_result()
        assert '&lt;b&gt;bold&lt;/b&gt;' in svg

    def test_clip_rect_and_clear(self):
        r = self._make_renderer()
        r.set_clip_rect(10, 20, 100, 80)
        r.draw_line([0, 50], [0, 50], "#000", 1, "-")
        svg_clipped = r.get_result()
        assert '<clipPath' in svg_clipped
        assert 'clip-path="url(#' in svg_clipped

    def test_clear_clip_removes_clipping(self):
        r = self._make_renderer()
        r.set_clip_rect(10, 20, 100, 80)
        r.draw_line([0, 50], [0, 50], "#000", 1, "-")
        r.clear_clip()
        r.draw_line([0, 50], [0, 50], "#f00", 1, "-")
        svg = r.get_result()
        # Second polyline should NOT have clip-path
        polylines = re.findall(r'<polyline[^/]*/>', svg)
        assert len(polylines) == 2
        assert 'clip-path' in polylines[0]
        assert 'clip-path' not in polylines[1]

    def test_multiple_draw_calls_accumulate(self):
        r = self._make_renderer()
        r.draw_line([0, 1], [0, 1], "#000", 1, "-")
        r.draw_line([2, 3], [2, 3], "#f00", 1, "-")
        r.draw_markers([10], [10], "#0f0", 3)
        svg = r.get_result()
        assert svg.count('<polyline') == 2
        assert svg.count('<circle') == 1


# ===================================================================
# TestRendererPIL
# ===================================================================

class TestRendererPIL:
    """RendererPIL produces valid PNG output."""

    def _make_renderer(self, w=200, h=150, dpi=100):
        from matplotlib._pil_backend import RendererPIL
        return RendererPIL(w, h, dpi)

    def test_init_creates_image(self):
        r = self._make_renderer()
        assert r.width == 200
        assert r.height == 150

    def test_get_result_returns_png_bytes(self):
        r = self._make_renderer()
        result = r.get_result()
        assert isinstance(result, bytes)
        assert result[:4] == b'\x89PNG'

    def test_draw_line_no_crash(self):
        r = self._make_renderer()
        r.draw_line([10, 100], [10, 100], "#ff0000", 2.0, "-")
        result = r.get_result()
        assert result[:4] == b'\x89PNG'

    def test_draw_markers_no_crash(self):
        r = self._make_renderer()
        r.draw_markers([10, 50, 90], [10, 80, 40], "#00ff00", 4)
        result = r.get_result()
        assert result[:4] == b'\x89PNG'

    def test_draw_rect_no_crash(self):
        r = self._make_renderer()
        r.draw_rect(10, 20, 80, 50, "#0000ff", None)
        result = r.get_result()
        assert result[:4] == b'\x89PNG'

    def test_draw_rect_with_fill(self):
        r = self._make_renderer()
        r.draw_rect(10, 20, 80, 50, "#000", "#ff0000")
        result = r.get_result()
        assert result[:4] == b'\x89PNG'

    def test_draw_circle_no_crash(self):
        r = self._make_renderer()
        r.draw_circle(50, 50, 20, "#f00")
        result = r.get_result()
        assert result[:4] == b'\x89PNG'

    def test_draw_polygon_no_crash(self):
        r = self._make_renderer()
        r.draw_polygon([(10, 10), (100, 10), (50, 80)], "#00f", 0.5)
        result = r.get_result()
        assert result[:4] == b'\x89PNG'

    def test_draw_text_no_crash(self):
        r = self._make_renderer()
        r.draw_text(50, 75, "Hello", 12, "#000", "left")
        result = r.get_result()
        assert result[:4] == b'\x89PNG'

    def test_multiple_draws(self):
        r = self._make_renderer()
        r.draw_line([10, 100], [10, 100], "#f00", 2, "-")
        r.draw_markers([50], [50], "#0f0", 5)
        r.draw_rect(10, 10, 50, 50, "#00f", "#00f")
        result = r.get_result()
        assert result[:4] == b'\x89PNG'


# --- Task 4-6 tests ---
from matplotlib.backend_bases import AxesLayout
from matplotlib._svg_backend import RendererSVG
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Circle, Polygon
from matplotlib.collections import PathCollection
from matplotlib.text import Text


class TestLine2DDraw:
    def _layout(self):
        return AxesLayout(plot_x=0, plot_y=0, plot_w=100, plot_h=100,
                          xmin=0.0, xmax=10.0, ymin=0.0, ymax=10.0)

    def test_draw_produces_polyline(self):
        line = Line2D([0, 5, 10], [0, 10, 5], color='#ff0000', linewidth=2.0)
        r = RendererSVG(100, 100, 100)
        line.draw(r, self._layout())
        assert '<polyline' in r.get_result()

    def test_draw_with_marker(self):
        line = Line2D([0, 10], [0, 10], color='#000', marker='o')
        r = RendererSVG(100, 100, 100)
        line.draw(r, self._layout())
        assert '<circle' in r.get_result()

    def test_draw_invisible(self):
        line = Line2D([0, 10], [0, 10], color='#000')
        line.set_visible(False)
        r = RendererSVG(100, 100, 100)
        line.draw(r, self._layout())
        assert '<polyline' not in r.get_result()

    def test_draw_none_linestyle(self):
        line = Line2D([0, 10], [0, 10], color='#000', linestyle='None', marker='o')
        r = RendererSVG(100, 100, 100)
        line.draw(r, self._layout())
        result = r.get_result()
        assert '<polyline' not in result
        assert '<circle' in result


class TestRectangleDraw:
    def _layout(self):
        return AxesLayout(plot_x=0, plot_y=0, plot_w=100, plot_h=100,
                          xmin=0.0, xmax=10.0, ymin=0.0, ymax=10.0)

    def test_draw_produces_rect(self):
        rect = Rectangle((2, 0), 3, 5, facecolor='#0000ff')
        r = RendererSVG(100, 100, 100)
        rect.draw(r, self._layout())
        assert '<rect' in r.get_result()

    def test_draw_invisible(self):
        rect = Rectangle((0, 0), 5, 5)
        rect.set_visible(False)
        r = RendererSVG(100, 100, 100)
        rect.draw(r, self._layout())
        assert '<rect' not in r.get_result()


class TestCircleDraw:
    def _layout(self):
        return AxesLayout(plot_x=0, plot_y=0, plot_w=100, plot_h=100,
                          xmin=0.0, xmax=10.0, ymin=0.0, ymax=10.0)

    def test_draw_produces_circle(self):
        c = Circle((5, 5), 2, facecolor='#ff0000')
        r = RendererSVG(100, 100, 100)
        c.draw(r, self._layout())
        assert '<circle' in r.get_result()


class TestPolygonPatch:
    def _layout(self):
        return AxesLayout(plot_x=0, plot_y=0, plot_w=100, plot_h=100,
                          xmin=0.0, xmax=10.0, ymin=0.0, ymax=10.0)

    def test_init(self):
        p = Polygon([(0, 0), (1, 1), (2, 0)], facecolor='#00ff00')
        assert len(p.get_xy()) == 3

    def test_draw_produces_polygon(self):
        p = Polygon([(0, 0), (10, 10), (10, 0)], facecolor='#00ff00')
        r = RendererSVG(100, 100, 100)
        p.draw(r, self._layout())
        assert '<polygon' in r.get_result()

    def test_get_set_xy(self):
        p = Polygon([(0, 0), (1, 1)])
        p.set_xy([(2, 2), (3, 3), (4, 4)])
        assert len(p.get_xy()) == 3


class TestPathCollectionDraw:
    def _layout(self):
        return AxesLayout(plot_x=0, plot_y=0, plot_w=100, plot_h=100,
                          xmin=0.0, xmax=10.0, ymin=0.0, ymax=10.0)

    def test_draw_produces_circles(self):
        pc = PathCollection(offsets=[(2, 3), (5, 7)], sizes=[20], facecolors=['#ff0000'])
        r = RendererSVG(100, 100, 100)
        pc.draw(r, self._layout())
        assert r.get_result().count('<circle') == 2

    def test_draw_empty(self):
        pc = PathCollection(offsets=[], sizes=[20], facecolors=['#ff0000'])
        r = RendererSVG(100, 100, 100)
        pc.draw(r, self._layout())
        assert '<circle' not in r.get_result()

    def test_draw_invisible(self):
        pc = PathCollection(offsets=[(5, 5)], sizes=[20], facecolors=['#ff0000'])
        pc.set_visible(False)
        r = RendererSVG(100, 100, 100)
        pc.draw(r, self._layout())
        assert '<circle' not in r.get_result()


class TestTextDraw:
    def _layout(self):
        return AxesLayout(plot_x=0, plot_y=0, plot_w=100, plot_h=100,
                          xmin=0.0, xmax=10.0, ymin=0.0, ymax=10.0)

    def test_draw_produces_text(self):
        t = Text(5, 5, 'hello')
        r = RendererSVG(100, 100, 100)
        t.draw(r, self._layout())
        result = r.get_result()
        assert 'hello' in result
        assert '<text' in result

    def test_draw_invisible(self):
        t = Text(5, 5, 'hidden')
        t.set_visible(False)
        r = RendererSVG(100, 100, 100)
        t.draw(r, self._layout())
        assert 'hidden' not in r.get_result()
