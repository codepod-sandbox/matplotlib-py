"""Tests for matplotlib.lines module — Line2D artist."""

import pytest

from matplotlib.lines import Line2D
from matplotlib.colors import to_hex


class TestLine2DConstruction:
    def test_basic_construction(self):
        """Line2D stores x/y data."""
        line = Line2D([1, 2, 3], [4, 5, 6])
        assert line.get_xdata() == [1, 2, 3]
        assert line.get_ydata() == [4, 5, 6]

    def test_default_color(self):
        """Default color is C0."""
        line = Line2D([0], [0])
        assert line.get_color() == 'C0'

    def test_default_linewidth(self):
        """Default linewidth is 1.5."""
        line = Line2D([0], [0])
        assert line.get_linewidth() == 1.5

    def test_default_linestyle(self):
        """Default linestyle is '-'."""
        line = Line2D([0], [0])
        assert line.get_linestyle() == '-'

    def test_default_marker(self):
        """Default marker is 'None' (string)."""
        line = Line2D([0], [0])
        assert line.get_marker() == 'None'

    def test_default_markersize(self):
        """Default markersize is 6.0."""
        line = Line2D([0], [0])
        assert line.get_markersize() == 6.0

    def test_default_fillstyle(self):
        """Default fillstyle is 'full'."""
        line = Line2D([0], [0])
        assert line.get_fillstyle() == 'full'

    def test_default_drawstyle(self):
        """Default drawstyle is 'default'."""
        line = Line2D([0], [0])
        assert line.get_drawstyle() == 'default'

    def test_explicit_kwargs(self):
        """Explicit kwargs override defaults."""
        line = Line2D([0], [0], color='red', linewidth=3.0,
                       linestyle='--', marker='o')
        assert line.get_color() == 'red'
        assert line.get_linewidth() == 3.0
        assert line.get_linestyle() == '--'
        assert line.get_marker() == 'o'

    def test_label(self):
        """Label is set via kwarg."""
        line = Line2D([0], [0], label='test')
        assert line.get_label() == 'test'

    def test_no_label(self):
        """No label kwarg gives empty label."""
        line = Line2D([0], [0])
        assert line.get_label() == ''


class TestLine2DSetters:
    def test_set_get_color(self):
        line = Line2D([0], [0])
        line.set_color('blue')
        assert line.get_color() == 'blue'

    def test_set_c_alias(self):
        """set_c is an alias for set_color."""
        line = Line2D([0], [0])
        line.set_c('green')
        assert line.get_color() == 'green'

    def test_set_get_linewidth(self):
        line = Line2D([0], [0])
        line.set_linewidth(5.0)
        assert line.get_linewidth() == 5.0

    def test_set_lw_alias(self):
        """set_lw is an alias for set_linewidth."""
        line = Line2D([0], [0])
        line.set_lw(2.5)
        assert line.get_linewidth() == 2.5

    def test_set_get_linestyle(self):
        line = Line2D([0], [0])
        line.set_linestyle(':')
        assert line.get_linestyle() == ':'

    def test_set_ls_alias(self):
        """set_ls is an alias for set_linestyle."""
        line = Line2D([0], [0])
        line.set_ls('-.')
        assert line.get_linestyle() == '-.'

    def test_set_get_marker(self):
        line = Line2D([0], [0])
        line.set_marker('s')
        assert line.get_marker() == 's'

    def test_set_get_markersize(self):
        line = Line2D([0], [0])
        line.set_markersize(12.0)
        assert line.get_markersize() == 12.0

    def test_set_ms_alias(self):
        """set_ms is an alias for set_markersize."""
        line = Line2D([0], [0])
        line.set_ms(8.0)
        assert line.get_markersize() == 8.0

    def test_set_get_fillstyle(self):
        line = Line2D([0], [0])
        line.set_fillstyle('none')
        assert line.get_fillstyle() == 'none'

    def test_set_get_drawstyle(self):
        line = Line2D([0], [0])
        line.set_drawstyle('steps')
        assert line.get_drawstyle() == 'steps'


class TestLine2DData:
    def test_get_data(self):
        """get_data returns (xdata, ydata) tuple."""
        line = Line2D([1, 2], [3, 4])
        x, y = line.get_data()
        assert x == [1, 2]
        assert y == [3, 4]

    def test_set_data(self):
        """set_data replaces both x and y."""
        line = Line2D([1, 2], [3, 4])
        line.set_data([10, 20], [30, 40])
        assert line.get_xdata() == [10, 20]
        assert line.get_ydata() == [30, 40]

    def test_set_xdata(self):
        line = Line2D([1, 2], [3, 4])
        line.set_xdata([10, 20, 30])
        assert line.get_xdata() == [10, 20, 30]
        assert line.get_ydata() == [3, 4]  # unchanged

    def test_set_ydata(self):
        line = Line2D([1, 2], [3, 4])
        line.set_ydata([10, 20, 30])
        assert line.get_ydata() == [10, 20, 30]
        assert line.get_xdata() == [1, 2]  # unchanged

    def test_data_is_copy(self):
        """get_xdata/get_ydata return copies, not references."""
        line = Line2D([1, 2], [3, 4])
        xd = line.get_xdata()
        xd.append(999)
        assert line.get_xdata() == [1, 2]


class TestLine2DAsElement:
    def test_as_element_type(self):
        """_as_element returns dict with type='line'."""
        line = Line2D([1, 2], [3, 4], color='red')
        elem = line._as_element()
        assert elem['type'] == 'line'

    def test_as_element_data(self):
        line = Line2D([1, 2], [3, 4])
        elem = line._as_element()
        assert elem['x'] == [1, 2]
        assert elem['y'] == [3, 4]

    def test_as_element_color_hex(self):
        """Color is converted to hex in the element dict."""
        line = Line2D([0], [0], color='red')
        elem = line._as_element()
        assert elem['color'] == '#ff0000'

    def test_as_element_marker_none(self):
        """Marker 'None' becomes None in element dict."""
        line = Line2D([0], [0])
        elem = line._as_element()
        assert elem['marker'] is None

    def test_as_element_marker_set(self):
        line = Line2D([0], [0], marker='o')
        elem = line._as_element()
        assert elem['marker'] == 'o'


class TestLine2DArtist:
    def test_zorder(self):
        """Line2D default zorder is 2."""
        line = Line2D([0], [0])
        assert line.get_zorder() == 2

    def test_visible(self):
        """Line2D defaults to visible."""
        line = Line2D([0], [0])
        assert line.get_visible() is True

    def test_set_visible(self):
        line = Line2D([0], [0])
        line.set_visible(False)
        assert line.get_visible() is False

    def test_set_alpha(self):
        line = Line2D([0], [0])
        line.set_alpha(0.5)
        assert line.get_alpha() == 0.5

    def test_batch_set(self):
        """Artist.set() applies multiple properties."""
        line = Line2D([0], [0])
        line.set(color='red', linewidth=3.0, visible=False)
        assert line.get_color() == 'red'
        assert line.get_linewidth() == 3.0
        assert line.get_visible() is False

    def test_remove_from_axes(self):
        """Line2D.remove() removes from axes' lines list."""
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        lines = ax.plot([1, 2], [3, 4])
        line = lines[0]
        assert line in ax.lines
        line.remove()
        assert line not in ax.lines
        plt.close('all')
