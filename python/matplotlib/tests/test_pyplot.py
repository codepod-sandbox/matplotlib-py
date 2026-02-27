"""Tests for matplotlib.pyplot state-machine API.

Covers interactive mode, figure management, close, subplot/axes,
clear, figure properties, labels, limits, and auto-numbering.
"""

import pytest

import matplotlib
import matplotlib.pyplot as plt


@pytest.fixture(autouse=True)
def _reset_pyplot_state():
    """Reset all pyplot global state before each test."""
    plt.close('all')
    plt._next_num = 1
    matplotlib._interactive = False
    yield
    plt.close('all')
    plt._next_num = 1
    matplotlib._interactive = False


# ===================================================================
# Interactive mode (5 tests)
# ===================================================================

class TestInteractiveMode:
    def test_ioff(self):
        """ion() then ioff() makes interactive False."""
        plt.ion()
        assert plt.isinteractive() is True
        plt.ioff()
        assert plt.isinteractive() is False

    def test_ion(self):
        """ioff() then ion() makes interactive True."""
        plt.ioff()
        assert plt.isinteractive() is False
        plt.ion()
        assert plt.isinteractive() is True

    def test_ioff_context(self):
        """ioff() as context manager restores interactive state on exit."""
        plt.ion()
        assert plt.isinteractive() is True
        with plt.ioff():
            assert plt.isinteractive() is False
        assert plt.isinteractive() is True

    def test_ion_context(self):
        """ion() as context manager restores interactive state on exit."""
        plt.ioff()
        assert plt.isinteractive() is False
        with plt.ion():
            assert plt.isinteractive() is True
        assert plt.isinteractive() is False

    def test_nested_ion_ioff(self):
        """Nested context managers preserve and restore state correctly."""
        plt.ioff()
        assert plt.isinteractive() is False
        with plt.ion():
            assert plt.isinteractive() is True
            with plt.ioff():
                assert plt.isinteractive() is False
            # After inner context exits, back to True
            assert plt.isinteractive() is True
        # After outer context exits, back to False
        assert plt.isinteractive() is False


# ===================================================================
# Close (3 tests)
# ===================================================================

class TestClose:
    def test_close_all(self):
        """close('all') removes all figures."""
        plt.figure()
        plt.figure()
        assert len(plt.get_fignums()) == 2
        plt.close('all')
        assert plt.get_fignums() == []

    def test_close_by_num(self):
        """close(num) removes only the specified figure."""
        plt.figure()
        plt.figure()
        assert plt.get_fignums() == [1, 2]
        plt.close(1)
        assert plt.get_fignums() == [2]

    def test_close_float_raises(self):
        """close(1.0) raises TypeError."""
        with pytest.raises(TypeError, match="float"):
            plt.close(1.0)


# ===================================================================
# Figure management (4 tests)
# ===================================================================

class TestFigureManagement:
    def test_figure_label(self):
        """Figures created with string labels appear in get_figlabels."""
        plt.figure('a')
        plt.figure('b')
        assert plt.get_figlabels() == ['a', 'b']

    def test_fignum_exists(self):
        """fignum_exists returns True/False correctly."""
        fig = plt.figure()
        num = fig.number
        assert plt.fignum_exists(num) is True
        plt.close(num)
        assert plt.fignum_exists(num) is False

    def test_gca(self):
        """fig.gca() returns the same axes each call (no duplicates)."""
        fig = plt.figure()
        ax1 = fig.gca()
        ax2 = fig.gca()
        assert ax1 is ax2
        assert len(fig.get_axes()) == 1

    def test_gcf(self):
        """plt.gcf() returns the most recently created/activated figure."""
        fig1 = plt.figure()
        fig2 = plt.figure()
        assert plt.gcf() is fig2


# ===================================================================
# Subplot and Axes (2 tests)
# ===================================================================

class TestSubplotAxes:
    def test_subplot_reuse(self):
        """subplot(1,1,1) called twice returns the same axes."""
        plt.figure()
        ax1 = plt.subplot(1, 1, 1)
        ax2 = plt.subplot(1, 1, 1)
        assert ax1 is ax2

    def test_axes_always_new(self):
        """axes() called twice always returns different axes."""
        plt.figure()
        ax1 = plt.axes()
        ax2 = plt.axes()
        assert ax1 is not ax2


# ===================================================================
# Clear (2 tests)
# ===================================================================

class TestClear:
    def test_clf(self):
        """clf() removes all axes from the current figure."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [4, 5, 6])
        assert len(fig.get_axes()) > 0
        plt.clf()
        assert fig.get_axes() == []

    def test_cla(self):
        """cla() clears the current axes' elements."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [4, 5, 6])
        assert len(ax._elements) > 0
        plt.cla()
        assert ax._elements == []
        assert ax.get_title() == ''
        assert ax.get_xlabel() == ''
        assert ax.get_ylabel() == ''


# ===================================================================
# Figure properties (5 tests)
# ===================================================================

class TestFigureProperties:
    def test_set_fig_size(self):
        """set_figwidth, set_figheight, set_size_inches work correctly."""
        fig = plt.figure()
        # set_figwidth / set_figheight
        fig.set_figwidth(10)
        assert fig.get_figwidth() == 10.0
        fig.set_figheight(8)
        assert fig.get_figheight() == 8.0
        assert fig.get_size_inches() == (10.0, 8.0)
        # set_size_inches with two args
        fig.set_size_inches(5, 4)
        assert fig.get_size_inches() == (5.0, 4.0)
        # set_size_inches with tuple
        fig.set_size_inches((7, 3))
        assert fig.get_size_inches() == (7.0, 3.0)

    def test_suptitle(self):
        """fig.suptitle() sets and get_suptitle() retrieves the suptitle."""
        fig = plt.figure()
        fig.suptitle('Hello')
        assert fig.get_suptitle() == 'Hello'

    def test_figure_repr(self):
        """Figure repr contains size and axes count."""
        fig = plt.figure(figsize=(6.4, 4.8), dpi=100)
        r = repr(fig)
        assert '640x480' in r
        assert '0 Axes' in r
        fig.add_subplot(1, 1, 1)
        r = repr(fig)
        assert '1 Axes' in r

    def test_axes_remove(self):
        """delaxes removes one axes, leaving the others."""
        fig, axes_list = plt.subplots(2, 2)
        assert len(fig.get_axes()) == 4
        # axes_list is a list of lists for 2x2
        ax_to_remove = fig.get_axes()[0]
        fig.delaxes(ax_to_remove)
        assert len(fig.get_axes()) == 3
        assert ax_to_remove not in fig.get_axes()

    def test_figure_clear(self):
        """figure.clear() removes axes and resets suptitle."""
        fig = plt.figure()
        fig.add_subplot(1, 1, 1)
        fig.suptitle('Title')
        assert len(fig.get_axes()) == 1
        assert fig.get_suptitle() == 'Title'
        fig.clear()
        assert fig.get_axes() == []
        assert fig.get_suptitle() == ''


# ===================================================================
# Additional tests (9 tests)
# ===================================================================

class TestAdditional:
    def test_get_set_labels(self):
        """set_xlabel/set_ylabel reflected by get_xlabel/get_ylabel."""
        fig, ax = plt.subplots()
        ax.set_xlabel('X Label')
        ax.set_ylabel('Y Label')
        assert ax.get_xlabel() == 'X Label'
        assert ax.get_ylabel() == 'Y Label'

    def test_xlim_ylim(self):
        """plt.xlim() and plt.ylim() work as both getters and setters."""
        fig, ax = plt.subplots()
        # Set limits
        plt.xlim(0, 10)
        plt.ylim(-5, 5)
        # Get limits
        assert plt.xlim() == (0, 10)
        assert plt.ylim() == (-5, 5)

    def test_figure_number_auto(self):
        """Figures get auto-incrementing numbers starting from 1."""
        fig1 = plt.figure()
        fig2 = plt.figure()
        fig3 = plt.figure()
        assert fig1.number == 1
        assert fig2.number == 2
        assert fig3.number == 3

    def test_close_by_figure_instance(self):
        """close(fig) removes that specific figure from tracking."""
        fig1 = plt.figure()
        fig2 = plt.figure()
        assert plt.get_fignums() == [1, 2]
        plt.close(fig1)
        assert plt.get_fignums() == [2]
        assert not plt.fignum_exists(fig1.number)

    def test_reactivate_figure(self):
        """figure(num) with existing num reactivates it without creating new."""
        fig1 = plt.figure()
        fig2 = plt.figure()
        assert plt.gcf() is fig2
        reactivated = plt.figure(fig1.number)
        assert reactivated is fig1
        assert plt.gcf() is fig1
        # No new figure was created
        assert plt.get_fignums() == [1, 2]

    def test_suptitle_via_pyplot(self):
        """plt.suptitle() delegates to current figure."""
        fig = plt.figure()
        plt.suptitle('Test Title')
        assert fig.get_suptitle() == 'Test Title'

    def test_subplot_3digit(self):
        """subplot(211) is equivalent to subplot(2, 1, 1)."""
        fig = plt.figure()
        ax1 = plt.subplot(211)
        assert ax1._position == (2, 1, 1)

    def test_subplots_grid(self):
        """subplots(2, 2) returns a list of 4 axes in correct shape."""
        fig, axes_list = plt.subplots(2, 2)
        # 2x2 returns list of lists
        assert len(axes_list) == 2
        assert len(axes_list[0]) == 2
        assert len(fig.get_axes()) == 4

    def test_figure_with_clear(self):
        """figure(num, clear=True) clears an existing figure."""
        fig = plt.figure(1)
        fig.add_subplot(1, 1, 1)
        fig.suptitle('Old Title')
        assert len(fig.get_axes()) == 1
        fig2 = plt.figure(1, clear=True)
        assert fig2 is fig
        assert fig2.get_axes() == []
        assert fig2.get_suptitle() == ''
