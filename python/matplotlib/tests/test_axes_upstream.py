"""
Upstream matplotlib tests imported from lib/matplotlib/tests/test_axes.py.

These tests are copied or minimally adapted from the real matplotlib test
suite to validate compatibility of our Axes implementation.
"""

import numpy as np
import pytest

import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# 1. test_get_labels (upstream ~line 4200)
# ---------------------------------------------------------------------------
def test_get_labels():
    fig, ax = plt.subplots()
    ax.set_xlabel('x label')
    ax.set_ylabel('y label')
    assert ax.get_xlabel() == 'x label'
    assert ax.get_ylabel() == 'y label'


# ---------------------------------------------------------------------------
# 2. test_inverted_limits (upstream ~line 2260)  -- first two stanzas
# ---------------------------------------------------------------------------
def test_inverted_limits():
    # Invert x-axis, then plot: x-limits should be reversed
    fig, ax = plt.subplots()
    ax.invert_xaxis()
    ax.plot([-5, -3, 2, 4], [1, 2, -3, 5])
    assert ax.get_xlim() == (4, -5)
    assert ax.get_ylim() == (-3, 5)

    # Invert y-axis, then plot: y-limits should be reversed
    fig, ax = plt.subplots()
    ax.invert_yaxis()
    ax.plot([-5, -3, 2, 4], [1, 2, -3, 5])
    assert ax.get_xlim() == (-5, 4)
    assert ax.get_ylim() == (5, -3)


# ---------------------------------------------------------------------------
# 3. test_fill_between_input (upstream ~line 5700)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    'x, y1, y2', [
        (np.zeros((2, 2)), 3, 3),
        (np.arange(0.0, 2, 0.02), np.zeros((2, 2)), 3),
        (np.arange(0.0, 2, 0.02), 3, np.zeros((2, 2))),
    ], ids=['2d_x_input', '2d_y1_input', '2d_y2_input']
)
def test_fill_between_input(x, y1, y2):
    fig, ax = plt.subplots()
    with pytest.raises(ValueError):
        ax.fill_between(x, y1, y2)


# ---------------------------------------------------------------------------
# 4. test_fill_betweenx_input (upstream ~line 5720)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    'y, x1, x2', [
        (np.zeros((2, 2)), 3, 3),
        (np.arange(0.0, 2, 0.02), np.zeros((2, 2)), 3),
        (np.arange(0.0, 2, 0.02), 3, np.zeros((2, 2))),
    ], ids=['2d_y_input', '2d_x1_input', '2d_x2_input']
)
def test_fill_betweenx_input(y, x1, x2):
    fig, ax = plt.subplots()
    with pytest.raises(ValueError):
        ax.fill_betweenx(y, x1, x2)


# ---------------------------------------------------------------------------
# 5. test_bar_ticklabel_fail (upstream ~line 3040)  -- smoke test
# ---------------------------------------------------------------------------
def test_bar_ticklabel_fail():
    fig, ax = plt.subplots()
    ax.bar([], [])


# ---------------------------------------------------------------------------
# 6. test_bar_color_none_alpha (upstream ~line 3120)
# ---------------------------------------------------------------------------
def test_bar_color_none_alpha():
    fig, ax = plt.subplots()
    rects = ax.bar([1, 2], [2, 4], alpha=0.3, color='none', edgecolor='r')
    for rect in rects:
        assert rect.get_facecolor() == (0, 0, 0, 0)
        assert rect.get_edgecolor() == (1, 0, 0, 0.3)


# ---------------------------------------------------------------------------
# 7. test_bar_edgecolor_none_alpha (upstream ~line 3135)
# ---------------------------------------------------------------------------
def test_bar_edgecolor_none_alpha():
    fig, ax = plt.subplots()
    rects = ax.bar([1, 2], [2, 4], alpha=0.3, color='r', edgecolor='none')
    for rect in rects:
        assert rect.get_facecolor() == (1, 0, 0, 0.3)
        assert rect.get_edgecolor() == (0, 0, 0, 0)


# ---------------------------------------------------------------------------
# 8. test_nan_bar_values (upstream ~line 3020)  -- smoke test
# ---------------------------------------------------------------------------
def test_nan_bar_values():
    fig, ax = plt.subplots()
    ax.bar([0, 1], [np.nan, 4])


# ---------------------------------------------------------------------------
# 9. test_scatter_empty_data (upstream ~line 4650)
# ---------------------------------------------------------------------------
def test_scatter_empty_data():
    fig, ax = plt.subplots()
    ax.scatter([], [])


# ---------------------------------------------------------------------------
# 10. test_annotate_default_arrow (upstream ~line 4400)
# ---------------------------------------------------------------------------
def test_annotate_default_arrow():
    fig, ax = plt.subplots()
    ann = ax.annotate("foo", (0, 1), xytext=(2, 3))
    assert ann.arrow_patch is None
    ann = ax.annotate("foo", (0, 1), xytext=(2, 3), arrowprops={})
    assert ann.arrow_patch is not None


# ---------------------------------------------------------------------------
# 11. test_color_None (upstream ~line 7600)
# ---------------------------------------------------------------------------
def test_color_None():
    fig, ax = plt.subplots()
    ax.plot([1, 2], [1, 2], color=None)


# ---------------------------------------------------------------------------
# 12. test_zero_linewidth (upstream ~line 7610)
# ---------------------------------------------------------------------------
def test_zero_linewidth():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1], ls='--', lw=0)


# ---------------------------------------------------------------------------
# 13. test_empty_line_plots (upstream ~line 7580) -- second stanza only
# ---------------------------------------------------------------------------
def test_empty_line_plots():
    fig, ax = plt.subplots()
    line = ax.plot([], [])
    assert len(line) == 1


# ---------------------------------------------------------------------------
# 14. test_errorbar_nonefmt (upstream ~line 3700)
# ---------------------------------------------------------------------------
def test_errorbar_nonefmt():
    x = list(range(5))
    y = list(range(5))
    fig, ax = plt.subplots()
    ec = ax.errorbar(x, y, xerr=1, yerr=1, fmt='none')
    plotline, _, barlines = ec.lines
    assert plotline is None


# ---------------------------------------------------------------------------
# 15. test_inverted_cla (upstream ~line 2290)
# ---------------------------------------------------------------------------
def test_inverted_cla():
    """Upstream: test_axes.py::test_inverted_cla (simplified, no imshow)"""
    fig, ax = plt.subplots()

    # New axis is not inverted
    assert not ax.xaxis_inverted()
    assert not ax.yaxis_inverted()

    # Invert, then clear — should reset
    ax.invert_yaxis()
    assert ax.yaxis_inverted()
    ax.cla()
    assert not ax.yaxis_inverted()

    # Plot after clear — not inverted
    ax.plot([0, 1, 2], [0, 1, 2])
    assert not ax.xaxis_inverted()
    assert not ax.yaxis_inverted()


# ---------------------------------------------------------------------------
# 16. test_bar_labels (upstream ~line 3060)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("x", "width", "label", "expected_labels", "container_label"),
    [
        ("x", 1, "x", ["_nolegend_"], "x"),
        (["a", "b", "c"], [10, 20, 15], ["A", "B", "C"],
         ["A", "B", "C"], "_nolegend_"),
        (["a", "b", "c"], [10, 20, 15], ["R", "Y", "_nolegend_"],
         ["R", "Y", "_nolegend_"], "_nolegend_"),
        (["a", "b", "c"], [10, 20, 15], "bars",
         ["_nolegend_", "_nolegend_", "_nolegend_"], "bars"),
    ]
)
def test_bar_labels(x, width, label, expected_labels, container_label):
    """Upstream: test_axes.py::test_bar_labels"""
    _, ax = plt.subplots()
    bar_container = ax.bar(x, width, label=label)
    bar_labels = [bar.get_label() for bar in bar_container]
    assert expected_labels == bar_labels
    assert bar_container.get_label() == container_label


# ---------------------------------------------------------------------------
# 17. test_bar_labels_length (upstream ~line 3090)
# ---------------------------------------------------------------------------
def test_bar_labels_length():
    """Upstream: test_axes.py::test_bar_labels_length"""
    _, ax = plt.subplots()
    with pytest.raises(ValueError):
        ax.bar(["x", "y"], [1, 2], label=["X", "Y", "Z"])
    _, ax = plt.subplots()
    with pytest.raises(ValueError):
        ax.bar(["x", "y"], [1, 2], label=["X"])


# ---------------------------------------------------------------------------
# 18. test_scatter_size_arg_size (upstream ~line 4660)
# ---------------------------------------------------------------------------
def test_scatter_size_arg_size():
    """Upstream: test_axes.py::test_scatter_size_arg_size"""
    x = list(range(4))
    fig, ax = plt.subplots()
    with pytest.raises(ValueError, match='same size as x and y'):
        ax.scatter(x, x, x[1:])
    with pytest.raises(ValueError, match='same size as x and y'):
        ax.scatter(x[1:], x[1:], x)
    with pytest.raises(ValueError, match='float'):
        ax.scatter(x, x, 'foo')


# ---------------------------------------------------------------------------
# 19. test_twinx_cla (upstream ~line 2350)
# ---------------------------------------------------------------------------
def test_twinx_cla():
    """Upstream: test_axes.py::test_twinx_cla (adapted)"""
    fig, ax = plt.subplots()
    ax2 = ax.twinx()

    # After cla(), twin axes should preserve shared connection
    ax2.cla()
    assert ax2 in fig.axes
    assert ax in fig.axes

    # Shared x-limits should still work
    ax.set_xlim(0, 10)
    assert ax2.get_xlim() == (0, 10)


# ---------------------------------------------------------------------------
# 20. test_hist_with_empty_input (upstream ~line 5200)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize('data, expected_number_of_hists',
                         [([], 1),
                          ([[]], 1),
                          ([[], []], 2)])
def test_hist_with_empty_input(data, expected_number_of_hists):
    """Upstream: test_axes.py::test_hist_with_empty_input"""
    fig, ax = plt.subplots()
    hists, _, _ = ax.hist(data)
    if not isinstance(hists, list) or (isinstance(hists, list) and len(hists) > 0 and isinstance(hists[0], (int, float))):
        assert 1 == expected_number_of_hists
    else:
        assert len(hists) == expected_number_of_hists


# ---------------------------------------------------------------------------
# 21. test_axes_clear_resets_scale (upstream-inspired)
# ---------------------------------------------------------------------------
def test_axes_clear_resets_scale():
    """Upstream-inspired: cla() resets axis scale."""
    fig, ax = plt.subplots()
    ax.set_xscale('log')
    ax.set_yscale('log')
    assert ax.get_xscale() == 'log'
    assert ax.get_yscale() == 'log'
    ax.cla()
    assert ax.get_xscale() == 'linear'
    assert ax.get_yscale() == 'linear'


# ---------------------------------------------------------------------------
# 22. test_axes_set_kwargs (upstream-inspired)
# ---------------------------------------------------------------------------
def test_axes_set_kwargs():
    """Upstream-inspired: set(**kwargs) batch setter."""
    fig, ax = plt.subplots()
    ax.set(xlabel='X', ylabel='Y', title='T')
    assert ax.get_xlabel() == 'X'
    assert ax.get_ylabel() == 'Y'
    assert ax.get_title() == 'T'
    ax.set(xlim=(0, 10), ylim=(-1, 1))
    assert ax.get_xlim() == (0, 10)
    assert ax.get_ylim() == (-1, 1)


# ---------------------------------------------------------------------------
# 23. test_axes_twinx_shared_xlim (upstream-inspired)
# ---------------------------------------------------------------------------
def test_axes_twinx_shared_xlim():
    """Upstream-inspired: twinx shares x limits."""
    fig, ax = plt.subplots()
    ax.set_xlim(0, 5)
    ax2 = ax.twinx()
    assert ax2.get_xlim() == (0, 5)
    ax.set_xlim(1, 10)
    assert ax2.get_xlim() == (1, 10)


# ---------------------------------------------------------------------------
# 24. test_axes_twiny_shared_ylim (upstream-inspired)
# ---------------------------------------------------------------------------
def test_axes_twiny_shared_ylim():
    """Upstream-inspired: twiny shares y limits."""
    fig, ax = plt.subplots()
    ax.set_ylim(-3, 3)
    ax2 = ax.twiny()
    assert ax2.get_ylim() == (-3, 3)
    ax.set_ylim(0, 100)
    assert ax2.get_ylim() == (0, 100)
