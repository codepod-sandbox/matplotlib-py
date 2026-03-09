"""
Upstream matplotlib tests imported from lib/matplotlib/tests/test_figure.py.

These tests are copied (or minimally adapted) from the real matplotlib test
suite to validate compatibility of our Figure implementation.
"""

import pytest

import matplotlib.pyplot as plt
from matplotlib.figure import Figure


# ===================================================================
# Figure sizing (1 test — direct import)
# ===================================================================

def test_set_fig_size():
    fig = plt.figure()

    # check figwidth
    fig.set_figwidth(5)
    assert fig.get_figwidth() == 5

    # check figheight
    fig.set_figheight(1)
    assert fig.get_figheight() == 1

    # check using set_size_inches
    fig.set_size_inches(2, 4)
    assert fig.get_figwidth() == 2
    assert fig.get_figheight() == 4

    # check using tuple to first argument
    fig.set_size_inches((1, 3))
    assert fig.get_figwidth() == 1
    assert fig.get_figheight() == 3


# ===================================================================
# Figure repr (1 test — direct import)
# ===================================================================

def test_figure_repr():
    fig = plt.figure(figsize=(10, 20), dpi=10)
    assert repr(fig) == "<Figure size 100x200 with 0 Axes>"


# ===================================================================
# Figure label (1 test — direct import)
# ===================================================================

def test_figure_label():
    """Upstream: test_figure.py::test_figure_label"""
    plt.close('all')
    fig_today = plt.figure('today')
    plt.figure(3)
    plt.figure('tomorrow')
    plt.figure()
    plt.figure(0)
    plt.figure(1)
    plt.figure(3)
    assert plt.get_fignums() == [0, 1, 3, 4, 5]
    assert plt.get_figlabels() == ['', 'today', '', 'tomorrow', '']
    plt.close(10)
    plt.close()
    plt.close(5)
    plt.close('tomorrow')
    assert plt.get_fignums() == [0, 1]
    assert plt.get_figlabels() == ['', 'today']
    plt.figure(fig_today)
    assert plt.gcf() == fig_today
    with pytest.raises(ValueError):
        plt.figure(Figure())


# ===================================================================
# Figure num exists (1 test — direct import)
# ===================================================================

def test_fignum_exists():
    """Upstream: test_figure.py::test_fignum_exists"""
    plt.figure('one')
    plt.figure(2)
    plt.figure('three')
    plt.figure()
    assert plt.fignum_exists('one')
    assert plt.fignum_exists(2)
    assert plt.fignum_exists('three')
    assert plt.fignum_exists(4)
    plt.close('one')
    plt.close(4)
    assert not plt.fignum_exists('one')
    assert not plt.fignum_exists(4)


# ===================================================================
# CLF keyword (1 test — direct import)
# ===================================================================

def test_clf_keyword():
    """Upstream: test_figure.py::test_clf_keyword"""
    text1 = 'A fancy plot'
    text2 = 'Really fancy!'

    fig0 = plt.figure(num=1)
    fig0.suptitle(text1)
    assert [t.get_text() for t in fig0.texts] == [text1]

    fig1 = plt.figure(num=1, clear=False)
    fig1.text(0.5, 0.5, text2)
    assert fig0 is fig1
    assert [t.get_text() for t in fig1.texts] == [text1, text2]

    fig2, ax2 = plt.subplots(2, 1, num=1, clear=True)
    assert fig0 is fig2
    assert [t.get_text() for t in fig2.texts] == []


# ===================================================================
# GCA (1 test — direct import)
# ===================================================================

def test_gca():
    """Upstream: test_figure.py::test_gca"""
    fig = plt.figure()

    ax0 = fig.add_axes([0, 0, 1, 1])
    assert fig.gca() is ax0

    ax1 = fig.add_subplot(111)
    assert fig.gca() is ax1

    # Re-adding existing axes should not duplicate, but make current
    fig.add_axes(ax0)
    assert fig.axes == [ax0, ax1]
    assert fig.gca() is ax0

    fig.sca(ax0)
    assert fig.axes == [ax0, ax1]

    fig.add_subplot(ax1)
    assert fig.axes == [ax0, ax1]
    assert fig.gca() is ax1


# ===================================================================
# Axes remove (Task 5)
# ===================================================================

def test_axes_remove():
    """Upstream: test_figure.py::test_axes_remove"""
    fig, axs = plt.subplots(2, 2)
    axs[-1][-1].remove()
    for ax in [axs[0][0], axs[0][1], axs[1][0]]:
        assert ax in fig.axes
    assert axs[-1][-1] not in fig.axes
    assert len(fig.axes) == 3


# ===================================================================
# Invalid figure size (Task 6)
# ===================================================================

@pytest.mark.parametrize('width, height', [
    (1, float('nan')),
    (-1, 1),
    (float('inf'), 1),
])
def test_invalid_figure_size(width, height):
    """Upstream: test_figure.py::test_invalid_figure_size"""
    with pytest.raises(ValueError):
        plt.figure(figsize=(width, height))

    fig = plt.figure()
    with pytest.raises(ValueError):
        fig.set_size_inches(width, height)


# ===================================================================
# Figure clear (Task 7)
# ===================================================================

@pytest.mark.parametrize('clear_meth', ['clear', 'clf'])
def test_figure_clear(clear_meth):
    """Upstream: test_figure.py::test_figure_clear (simplified)"""
    fig = plt.figure()

    # a) empty figure
    getattr(fig, clear_meth)()
    assert fig.axes == []

    # b) single axes
    fig.add_subplot(111)
    getattr(fig, clear_meth)()
    assert fig.axes == []

    # c) multiple axes
    for i in range(2):
        fig.add_subplot(2, 1, i + 1)
    getattr(fig, clear_meth)()
    assert fig.axes == []


# ===================================================================
# Suptitle / supxlabel / supylabel (Task 8)
# ===================================================================

def test_get_suptitle_supxlabel_supylabel():
    """Upstream: test_figure.py::test_get_suptitle_supxlabel_supylabel"""
    fig, ax = plt.subplots()
    assert fig.get_suptitle() == ""
    assert fig.get_supxlabel() == ""
    assert fig.get_supylabel() == ""
    fig.suptitle('suptitle')
    assert fig.get_suptitle() == 'suptitle'
    fig.supxlabel('supxlabel')
    assert fig.get_supxlabel() == 'supxlabel'
    fig.supylabel('supylabel')
    assert fig.get_supylabel() == 'supylabel'


# ===================================================================
# Savefig args / pyplot axes (Task 9)
# ===================================================================

def test_savefig_args():
    """Upstream: test_figure.py::test_savefig — arg count validation"""
    fig = plt.figure()
    with pytest.raises(TypeError):
        fig.savefig("fname1.png", "fname2.png")


def test_pyplot_axes():
    """Upstream: test_axes.py::test_pyplot_axes"""
    fig1, ax1 = plt.subplots()
    fig2, ax2 = plt.subplots()
    plt.sca(ax1)
    assert ax1 is plt.gca()
    assert fig1 is plt.gcf()
    plt.close(fig1)
    plt.close(fig2)
