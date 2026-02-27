"""Tests for subplot layouts --- sharex, sharey, GridSpec, twinx, label_outer."""

import pytest

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.gridspec import GridSpec, SubplotSpec


class TestSharexSharey:
    def test_sharex_true(self):
        """sharex=True links x-limits across all subplots."""
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
        ax1.set_xlim(0, 10)
        assert ax2.get_xlim() == (0, 10)
        plt.close('all')

    def test_sharey_true(self):
        """sharey=True links y-limits across all subplots."""
        fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
        ax1.set_ylim(-5, 5)
        assert ax2.get_ylim() == (-5, 5)
        plt.close('all')

    def test_sharex_bidirectional(self):
        """Setting limits on either shared axes updates the other."""
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
        ax2.set_xlim(100, 200)
        assert ax1.get_xlim() == (100, 200)
        plt.close('all')

    def test_sharey_bidirectional(self):
        """Setting limits on either shared axes updates the other."""
        fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
        ax2.set_ylim(10, 20)
        assert ax1.get_ylim() == (10, 20)
        plt.close('all')

    def test_sharex_grid(self):
        """sharex=True on 2x2 grid links all x-limits."""
        fig, axes = plt.subplots(2, 2, sharex=True)
        axes[0][0].set_xlim(0, 100)
        for row in axes:
            for ax in row:
                assert ax.get_xlim() == (0, 100)
        plt.close('all')

    def test_no_share_independent(self):
        """Without share, axes have independent limits."""
        fig, (ax1, ax2) = plt.subplots(1, 2)
        ax1.set_xlim(0, 10)
        ax2.set_xlim(100, 200)
        assert ax1.get_xlim() == (0, 10)
        assert ax2.get_xlim() == (100, 200)
        plt.close('all')


class TestTwinAxes:
    def test_twinx_creates_axes(self):
        """twinx() creates a new Axes on the same Figure."""
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        assert isinstance(ax2, Axes)
        assert ax2.figure is fig
        plt.close('all')

    def test_twinx_shares_x(self):
        """twinx() shares x-axis with parent."""
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        ax1.set_xlim(0, 10)
        assert ax2.get_xlim() == (0, 10)
        plt.close('all')

    def test_twinx_independent_y(self):
        """twinx() has independent y-axis."""
        fig, ax1 = plt.subplots()
        ax2 = ax1.twinx()
        ax1.set_ylim(0, 10)
        ax2.set_ylim(100, 200)
        assert ax1.get_ylim() == (0, 10)
        assert ax2.get_ylim() == (100, 200)
        plt.close('all')

    def test_twiny_creates_axes(self):
        """twiny() creates a new Axes on the same Figure."""
        fig, ax1 = plt.subplots()
        ax2 = ax1.twiny()
        assert isinstance(ax2, Axes)
        assert ax2.figure is fig
        plt.close('all')

    def test_twiny_shares_y(self):
        """twiny() shares y-axis with parent."""
        fig, ax1 = plt.subplots()
        ax2 = ax1.twiny()
        ax1.set_ylim(0, 10)
        assert ax2.get_ylim() == (0, 10)
        plt.close('all')

    def test_twiny_independent_x(self):
        """twiny() has independent x-axis."""
        fig, ax1 = plt.subplots()
        ax2 = ax1.twiny()
        ax1.set_xlim(0, 10)
        ax2.set_xlim(100, 200)
        assert ax1.get_xlim() == (0, 10)
        assert ax2.get_xlim() == (100, 200)
        plt.close('all')


class TestGridSpec:
    def test_gridspec_creation(self):
        """GridSpec(nrows, ncols) creates a grid specification."""
        gs = GridSpec(2, 3)
        assert gs.nrows == 2
        assert gs.ncols == 3

    def test_gridspec_indexing(self):
        """gs[row, col] returns a SubplotSpec."""
        gs = GridSpec(2, 2)
        ss = gs[0, 0]
        assert isinstance(ss, SubplotSpec)

    def test_gridspec_row_slice(self):
        """gs[0, :] spans the full first row."""
        gs = GridSpec(2, 3)
        ss = gs[0, :]
        assert ss.rowspan == (0, 1)
        assert ss.colspan == (0, 3)

    def test_gridspec_col_slice(self):
        """gs[:, 0] spans the full first column."""
        gs = GridSpec(2, 3)
        ss = gs[:, 0]
        assert ss.rowspan == (0, 2)
        assert ss.colspan == (0, 1)

    def test_gridspec_block(self):
        """gs[0:2, 0:2] spans a 2x2 block."""
        gs = GridSpec(3, 3)
        ss = gs[0:2, 0:2]
        assert ss.rowspan == (0, 2)
        assert ss.colspan == (0, 2)

    def test_add_subplot_with_subplotspec(self):
        """Figure.add_subplot(SubplotSpec) creates an axes."""
        fig = plt.figure()
        gs = GridSpec(2, 2)
        ax = fig.add_subplot(gs[0, 0])
        assert isinstance(ax, Axes)
        assert ax.figure is fig
        plt.close('all')

    def test_gridspec_different_spans(self):
        """GridSpec supports axes with different spans."""
        fig = plt.figure()
        gs = GridSpec(2, 2)
        ax_top = fig.add_subplot(gs[0, :])    # top row, full width
        ax_bl = fig.add_subplot(gs[1, 0])     # bottom-left
        ax_br = fig.add_subplot(gs[1, 1])     # bottom-right
        assert len(fig.axes) == 3
        plt.close('all')


class TestLabelOuter:
    def test_label_outer_hides_inner_xlabels(self):
        """label_outer() hides x-tick labels on non-bottom subplots."""
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
        ax1.label_outer()
        assert ax1._xticklabels_visible is False
        assert ax1._xlabel_visible is False
        plt.close('all')

    def test_label_outer_keeps_bottom_xlabels(self):
        """label_outer() keeps x-tick labels on bottom subplots."""
        fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
        ax2.label_outer()
        assert ax2._xticklabels_visible is True
        assert ax2._xlabel_visible is True
        plt.close('all')

    def test_label_outer_hides_inner_ylabels(self):
        """label_outer() hides y-tick labels on non-left subplots."""
        fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
        ax2.label_outer()
        assert ax2._yticklabels_visible is False
        assert ax2._ylabel_visible is False
        plt.close('all')

    def test_label_outer_keeps_left_ylabels(self):
        """label_outer() keeps y-tick labels on left subplots."""
        fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
        ax1.label_outer()
        assert ax1._yticklabels_visible is True
        assert ax1._ylabel_visible is True
        plt.close('all')

    def test_label_outer_2x2(self):
        """label_outer() on a 2x2 grid hides inner labels correctly."""
        fig, axes = plt.subplots(2, 2, sharex=True, sharey=True)
        for row in axes:
            for ax in row:
                ax.label_outer()

        # Top-left (row=0, col=0): keep y-labels, hide x-labels
        assert axes[0][0]._yticklabels_visible is True
        assert axes[0][0]._xticklabels_visible is False

        # Top-right (row=0, col=1): hide both y and x labels
        assert axes[0][1]._yticklabels_visible is False
        assert axes[0][1]._xticklabels_visible is False

        # Bottom-left (row=1, col=0): keep both
        assert axes[1][0]._yticklabels_visible is True
        assert axes[1][0]._xticklabels_visible is True

        # Bottom-right (row=1, col=1): keep x, hide y
        assert axes[1][1]._yticklabels_visible is False
        assert axes[1][1]._xticklabels_visible is True
        plt.close('all')


class TestSubplotLayout:
    def test_subplots_1x1(self):
        """subplots(1,1) returns single Axes, not list."""
        fig, ax = plt.subplots(1, 1)
        assert isinstance(ax, Axes)
        plt.close('all')

    def test_subplots_1xn_flat(self):
        """subplots(1, n) returns flat list, not nested."""
        fig, axes = plt.subplots(1, 3)
        assert isinstance(axes, list)
        assert len(axes) == 3
        assert all(isinstance(a, Axes) for a in axes)
        plt.close('all')

    def test_subplots_nx1_flat(self):
        """subplots(n, 1) returns flat list, not nested."""
        fig, axes = plt.subplots(3, 1)
        assert isinstance(axes, list)
        assert len(axes) == 3
        assert all(isinstance(a, Axes) for a in axes)
        plt.close('all')

    def test_subplots_nxm_nested(self):
        """subplots(n, m) with n>1 and m>1 returns nested list."""
        fig, axes = plt.subplots(2, 3)
        assert isinstance(axes, list)
        assert len(axes) == 2
        assert all(isinstance(row, list) for row in axes)
        assert all(len(row) == 3 for row in axes)
        plt.close('all')

    def test_subplots_figure_axes_count(self):
        """Figure has correct number of axes after subplots()."""
        fig, axes = plt.subplots(2, 3)
        assert len(fig.axes) == 6
        plt.close('all')

    def test_subplot_3digit(self):
        """subplot(211) creates subplot at position (2,1,1)."""
        fig = plt.figure()
        ax = plt.subplot(211)
        assert ax._position == (2, 1, 1)
        plt.close('all')

    def test_subplot_reuse(self):
        """subplot() reuses existing axes at same position."""
        fig = plt.figure()
        ax1 = plt.subplot(211)
        ax2 = plt.subplot(211)
        assert ax1 is ax2
        plt.close('all')

    def test_add_subplot_with_gridspec(self):
        """add_subplot with GridSpec positions axes correctly."""
        from matplotlib.gridspec import GridSpec
        fig = plt.figure()
        gs = GridSpec(2, 2)
        ax1 = fig.add_subplot(gs[0, :])
        ax2 = fig.add_subplot(gs[1, 0])
        ax3 = fig.add_subplot(gs[1, 1])
        assert len(fig.axes) == 3
        plt.close('all')
