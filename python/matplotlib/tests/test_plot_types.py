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


class TestStep:
    def test_step_pre(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        lines = ax.step([1, 2, 3], [1, 4, 2], where='pre')
        assert len(lines) == 1
        line = lines[0]
        xd = line.get_xdata()
        yd = line.get_ydata()
        assert len(xd) == 5

    def test_step_post(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        lines = ax.step([1, 2, 3], [1, 4, 2], where='post')
        line = lines[0]
        xd = line.get_xdata()
        assert len(xd) == 5

    def test_step_mid(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        lines = ax.step([1, 2, 3], [1, 4, 2], where='mid')
        line = lines[0]
        xd = line.get_xdata()
        assert len(xd) == 7

    def test_step_returns_line_list(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.step([0, 1], [0, 1])
        assert isinstance(result, list)

    def test_step_invalid_where(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        try:
            ax.step([1, 2], [1, 2], where='invalid')
            assert False, "Should raise ValueError"
        except ValueError:
            pass


class TestStairs:
    def test_stairs_basic(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        line = ax.stairs([3, 2, 5, 1])
        xd = line.get_xdata()
        yd = line.get_ydata()
        assert len(xd) == 2 * 4

    def test_stairs_with_edges(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        line = ax.stairs([3, 2, 5], [10, 20, 30, 40])
        xd = line.get_xdata()
        assert xd[0] == 10
        assert xd[-1] == 40

    def test_stairs_is_line(self):
        from matplotlib.lines import Line2D
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.stairs([1, 2, 3])
        assert isinstance(result, Line2D)


class TestStackplot:
    def test_stackplot_basic(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.stackplot([1, 2, 3], [1, 2, 3], [2, 1, 2])
        assert len(result) == 2

    def test_stackplot_returns_polygons(self):
        from matplotlib.patches import Polygon
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.stackplot([1, 2, 3], [1, 2, 3])
        assert len(result) == 1
        assert isinstance(result[0], Polygon)

    def test_stackplot_labels(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.stackplot([1, 2, 3], [1, 2, 3], [2, 1, 2],
                              labels=['A', 'B'])
        assert result[0].get_label() == 'A'
        assert result[1].get_label() == 'B'

    def test_stackplot_cumulative(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        polys = ax.stackplot([1, 2], [10, 20], [5, 10])
        assert len(ax.patches) >= 2


class TestStem:
    def test_stem_basic(self):
        from matplotlib.container import StemContainer
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.stem([1, 2, 3], [4, 5, 6])
        assert isinstance(result, StemContainer)

    def test_stem_has_markerline(self):
        from matplotlib.lines import Line2D
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        sc = ax.stem([1, 2, 3], [4, 5, 6])
        assert isinstance(sc.markerline, Line2D)

    def test_stem_has_baseline(self):
        from matplotlib.lines import Line2D
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        sc = ax.stem([1, 2, 3], [4, 5, 6])
        assert isinstance(sc.baseline, Line2D)

    def test_stem_stemlines_count(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        sc = ax.stem([1, 2, 3], [4, 5, 6])
        assert len(sc.stemlines) == 3

    def test_stem_y_only(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        sc = ax.stem([4, 5, 6])
        assert sc.markerline.get_xdata() == [0, 1, 2]

    def test_stem_custom_bottom(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        sc = ax.stem([1, 2], [3, 4], bottom=1)
        assert sc.baseline.get_ydata() == [1, 1]


class TestPie:
    def test_pie_basic(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        result = ax.pie([1, 2, 3])
        wedges, texts = result[0], result[1]
        assert len(wedges) == 3

    def test_pie_wedge_angles_sum_to_360(self):
        from matplotlib.patches import Wedge
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        wedges, texts = ax.pie([1, 1, 1, 1])
        assert len(wedges) == 4
        for w in wedges:
            assert isinstance(w, Wedge)
            span = w._theta2 - w._theta1
            assert abs(span - 90.0) < 0.01

    def test_pie_labels(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        wedges, texts = ax.pie([1, 2], labels=['A', 'B'])
        assert len(texts) == 2
        assert texts[0].get_text() == 'A'
        assert texts[1].get_text() == 'B'

    def test_pie_colors(self):
        from matplotlib.colors import to_hex
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        wedges, texts = ax.pie([1, 1], colors=['red', 'blue'])
        assert to_hex(wedges[0]._facecolor) == to_hex('red')
        assert to_hex(wedges[1]._facecolor) == to_hex('blue')

    def test_pie_startangle(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        wedges, texts = ax.pie([1], startangle=90)
        assert wedges[0]._theta1 == 90

    def test_pie_autopct(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        wedges, texts, autotexts = ax.pie([1, 3], autopct='%1.0f%%')
        assert len(autotexts) == 2
        assert autotexts[0].get_text() == '25%'
        assert autotexts[1].get_text() == '75%'

    def test_pie_sets_equal_aspect(self):
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.pie([1, 2, 3])
        assert ax.get_aspect() == 'equal'
