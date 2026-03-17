# Copyright (c) 2024 CodePod Contributors — BSD 3-Clause License
# Ported from lib/matplotlib/tests/test_artist.py and test_lines.py
import pytest
import matplotlib.pyplot as plt


def test_artist_clip_on_default_true():
    """Artist.clip_on must default to True."""
    from matplotlib.lines import Line2D
    line = Line2D([0], [0])
    assert line.get_clip_on() is True


def test_artist_set_clip_on():
    """set_clip_on(False) must turn off clipping."""
    from matplotlib.patches import Rectangle
    r = Rectangle((0, 0), 1, 1)
    r.set_clip_on(False)
    assert r.get_clip_on() is False


def test_artist_alpha():
    """set_alpha / get_alpha round-trip."""
    from matplotlib.lines import Line2D
    line = Line2D([0], [0])
    assert line.get_alpha() is None  # default
    line.set_alpha(0.5)
    assert line.get_alpha() == 0.5


def test_zorder_defaults():
    """Line2D zorder=2, Patch zorder=1, Text zorder=3."""
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from matplotlib.text import Text
    assert Line2D([0], [0]).get_zorder() == 2
    assert Patch().get_zorder() == 1
    assert Text(0, 0, 'x').get_zorder() == 3


def test_zorder_draw_order_in_svg():
    """Artists with lower zorder must appear earlier in SVG."""
    fig, ax = plt.subplots()
    # Default: patches zorder=1 before lines zorder=2
    ax.bar([1], [1])  # adds a Rectangle (zorder=1)
    ax.plot([1], [1], label='line')  # adds a Line2D (zorder=2)
    svg = fig.to_svg()
    # polyline (line) must appear after rect (bar) in SVG
    rect_pos = svg.find('<rect')
    line_pos = svg.find('<polyline')
    assert rect_pos < line_pos, "Patch (zorder=1) must appear before Line2D (zorder=2)"
    plt.close('all')


def test_alpha_in_svg():
    """A line with alpha=0.5 must store alpha on Line2D and produce opacity in SVG."""
    fig, ax = plt.subplots()
    line, = ax.plot([1, 2], [1, 2], alpha=0.5)
    # Verify alpha is stored on the artist
    assert line.get_alpha() == 0.5
    # Verify opacity appears in SVG output
    svg = fig.to_svg()
    assert 'opacity="0.5"' in svg or 'opacity="0.5' in svg
    plt.close('all')


def test_linestyle_tuple_format():
    """Linestyle as (offset, (on, off)) tuple must appear in SVG."""
    fig, ax = plt.subplots()
    ax.plot([1, 2], [1, 2], linestyle=(0, (3, 5)))
    svg = fig.to_svg()
    assert 'stroke-dasharray' in svg
    plt.close('all')


def test_linestyle_named_solid():
    """linestyle='solid' must produce no stroke-dasharray."""
    fig, ax = plt.subplots()
    ax.plot([1, 2], [1, 2], linestyle='solid')
    svg = fig.to_svg()
    # solid lines produce no dasharray
    assert 'stroke-dasharray' not in svg or svg.count('stroke-dasharray') == 0
    plt.close('all')


def test_linestyle_loosely_dashed():
    """Named extended linestyle 'loosely dashed' must produce dasharray."""
    fig, ax = plt.subplots()
    ax.plot([1, 2], [1, 2], linestyle='loosely dashed')
    svg = fig.to_svg()
    assert 'stroke-dasharray' in svg
    plt.close('all')
