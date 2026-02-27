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
