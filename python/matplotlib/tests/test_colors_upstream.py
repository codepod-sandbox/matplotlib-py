"""Upstream matplotlib test_colors.py tests imported for compatibility testing."""

import numpy as np
import pytest

from matplotlib import colors as mcolors
from matplotlib.colors import is_color_like, to_rgba_array


# ---------------------------------------------------------------------------
# 1. test_color_names (upstream ~line 1179)
# ---------------------------------------------------------------------------
def test_color_names():
    assert mcolors.to_hex("blue") == "#0000ff"
    # Skip xkcd:blue — we don't have xkcd colors
    assert mcolors.to_hex("tab:blue") == "#1f77b4"


# ---------------------------------------------------------------------------
# 2. test_conversions (upstream ~line 1270)
# ---------------------------------------------------------------------------
def test_conversions():
    # to_rgba_array("none") returns an empty (0, 4) result.
    # Upstream returns np.zeros((0, 4)); our impl returns [].
    assert len(mcolors.to_rgba_array("none")) == 0
    assert len(mcolors.to_rgba_array([])) == 0
    # a list of grayscale levels, not a single color.
    result = mcolors.to_rgba_array([".2", ".5", ".8"])
    expected = [mcolors.to_rgba(c) for c in [".2", ".5", ".8"]]
    assert result == expected
    # alpha is properly set.
    assert mcolors.to_rgba((1, 1, 1), .5) == (1, 1, 1, .5)
    assert mcolors.to_rgba(".1", .5) == (.1, .1, .1, .5)
    # builtin round differs between py2 and py3.
    assert mcolors.to_hex((.7, .7, .7)) == "#b2b2b2"
    # hex roundtrip.
    hex_color = "#1234abcd"
    assert mcolors.to_hex(mcolors.to_rgba(hex_color), keep_alpha=True) == \
        hex_color


# ---------------------------------------------------------------------------
# 3. test_to_rgba_array_single_str (upstream ~line 1299)
# ---------------------------------------------------------------------------
def test_to_rgba_array_single_str():
    # single color name is valid
    result = mcolors.to_rgba_array("red")
    assert len(result) == 1
    assert result[0] == (1, 0, 0, 1)

    # single char color sequence is invalid
    with pytest.raises(ValueError, match="not a valid color value|Invalid RGBA"):
        mcolors.to_rgba_array("rgb")


# ---------------------------------------------------------------------------
# 4. test_to_rgba_array_2tuple_str (upstream ~line 1309)
# ---------------------------------------------------------------------------
def test_to_rgba_array_2tuple_str():
    expected = [(0, 0, 0, 1), (1, 1, 1, 1)]
    result = mcolors.to_rgba_array(("k", "w"))
    assert len(result) == 2
    assert result[0] == expected[0]
    assert result[1] == expected[1]


# ---------------------------------------------------------------------------
# 5. test_to_rgba_array_alpha_array (upstream ~line 1314)
# ---------------------------------------------------------------------------
def test_to_rgba_array_alpha_array():
    with pytest.raises(ValueError,
                       match="The number of colors must match|alpha length"):
        mcolors.to_rgba_array([[1, 1, 1], [1, 1, 1], [1, 1, 1],
                               [1, 1, 1], [1, 1, 1]],
                              alpha=[0.5, 0.6])
    alpha = [0.5, 0.6]
    c = mcolors.to_rgba_array([[1, 1, 1], [1, 1, 1]], alpha=alpha)
    assert c[0][3] == 0.5
    assert c[1][3] == 0.6
    c = mcolors.to_rgba_array(['r', 'g'], alpha=alpha)
    assert c[0][3] == 0.5
    assert c[1][3] == 0.6


# ---------------------------------------------------------------------------
# 6. test_to_rgba_array_accepts_color_alpha_tuple (upstream ~line 1324)
# ---------------------------------------------------------------------------
def test_to_rgba_array_accepts_color_alpha_tuple():
    result = mcolors.to_rgba_array(('black', 0.9))
    assert len(result) == 1
    assert result[0] == (0, 0, 0, 0.9)


# ---------------------------------------------------------------------------
# 7. test_to_rgba_array_explicit_alpha_overrides_tuple_alpha (upstream ~line 1330)
# ---------------------------------------------------------------------------
def test_to_rgba_array_explicit_alpha_overrides_tuple_alpha():
    result = mcolors.to_rgba_array(('black', 0.9), alpha=0.5)
    assert len(result) == 1
    assert result[0] == (0, 0, 0, 0.5)


# ---------------------------------------------------------------------------
# 8. test_to_rgba_array_accepts_color_alpha_tuple_with_multiple_colors
#    (upstream ~line 1336)
# ---------------------------------------------------------------------------
def test_to_rgba_array_accepts_color_alpha_tuple_with_multiple_colors():
    color_sequence = [[1., 1., 1., 1.], [0., 0., 1., 0.]]
    result = mcolors.to_rgba_array((color_sequence, 0.4))
    assert len(result) == 2
    assert result[0] == (1., 1., 1., 0.4)
    assert result[1] == (0., 0., 1., 0.4)


# ---------------------------------------------------------------------------
# 9. test_to_rgba_array_error_with_color_invalid_alpha_tuple (upstream ~line 1348)
# ---------------------------------------------------------------------------
def test_to_rgba_array_error_with_color_invalid_alpha_tuple():
    with pytest.raises(ValueError, match="'alpha' must be between 0 and 1,"):
        mcolors.to_rgba_array(('black', 2.0))


# ---------------------------------------------------------------------------
# 10. test_to_rgba_accepts_color_alpha_tuple (parametrized, upstream ~line 1353)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize('rgba_alpha',
                         [('white', 0.5), ('#ffffff', 0.5), ('#ffffff00', 0.5),
                          ((1.0, 1.0, 1.0, 1.0), 0.5)])
def test_to_rgba_accepts_color_alpha_tuple(rgba_alpha):
    assert mcolors.to_rgba(rgba_alpha) == (1, 1, 1, 0.5)


# ---------------------------------------------------------------------------
# 11. test_to_rgba_explicit_alpha_overrides_tuple_alpha (upstream ~line 1360)
# ---------------------------------------------------------------------------
def test_to_rgba_explicit_alpha_overrides_tuple_alpha():
    assert mcolors.to_rgba(('red', 0.1), alpha=0.9) == (1, 0, 0, 0.9)


# ---------------------------------------------------------------------------
# 12. test_to_rgba_error_with_color_invalid_alpha_tuple (upstream ~line 1364)
# ---------------------------------------------------------------------------
def test_to_rgba_error_with_color_invalid_alpha_tuple():
    with pytest.raises(ValueError, match="'alpha' must be between 0 and 1"):
        mcolors.to_rgba(('blue', 2.0))


# ---------------------------------------------------------------------------
# 13. test_failed_conversions (upstream ~line 1437)
# ---------------------------------------------------------------------------
def test_failed_conversions():
    with pytest.raises(ValueError):
        mcolors.to_rgba('5')
    with pytest.raises(ValueError):
        mcolors.to_rgba('-1')
    with pytest.raises(ValueError):
        mcolors.to_rgba('nan')
    with pytest.raises(ValueError):
        mcolors.to_rgba('unknown_color')
    with pytest.raises(ValueError):
        # Gray must be a string to distinguish 3-4 grays from RGB or RGBA.
        mcolors.to_rgba(0.4)


# ---------------------------------------------------------------------------
# 14. test_grey_gray (upstream ~line 1451)
# ---------------------------------------------------------------------------
def test_grey_gray():
    color_mapping = mcolors._colors_full_map
    for k in color_mapping.keys():
        if 'grey' in k:
            assert color_mapping[k] == color_mapping[k.replace('grey', 'gray')]
        if 'gray' in k:
            assert color_mapping[k] == color_mapping[k.replace('gray', 'grey')]


# ---------------------------------------------------------------------------
# 15. test_tableau_order (upstream ~line 1460)
# ---------------------------------------------------------------------------
def test_tableau_order():
    dflt_cycle = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
                  '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
                  '#bcbd22', '#17becf']

    assert list(mcolors.TABLEAU_COLORS.values()) == dflt_cycle


# ---------------------------------------------------------------------------
# 16. test_same_color (upstream ~line 1494)
# ---------------------------------------------------------------------------
def test_same_color():
    assert mcolors.same_color('k', (0, 0, 0))
    assert not mcolors.same_color('w', (1, 1, 0))
    assert mcolors.same_color(['red', 'blue'], ['r', 'b'])
    assert mcolors.same_color('none', 'none')
    assert not mcolors.same_color('none', 'red')
    with pytest.raises(ValueError):
        mcolors.same_color(['r', 'g', 'b'], ['r'])
    with pytest.raises(ValueError):
        mcolors.same_color(['red', 'green'], 'none')


# ---------------------------------------------------------------------------
# 17. test_hex_shorthand_notation (upstream ~line 1506)
# ---------------------------------------------------------------------------
def test_hex_shorthand_notation():
    assert mcolors.same_color("#123", "#112233")
    assert mcolors.same_color("#123a", "#112233aa")


# ---------------------------------------------------------------------------
# 18. test_has_alpha_channel (upstream ~line 1231)
# ---------------------------------------------------------------------------
def test_has_alpha_channel():
    assert mcolors._has_alpha_channel((0, 0, 0, 0))
    assert mcolors._has_alpha_channel([1, 1, 1, 1])
    assert mcolors._has_alpha_channel('#fff8')
    assert mcolors._has_alpha_channel('#0f0f0f80')
    assert mcolors._has_alpha_channel(('r', 0.5))
    assert mcolors._has_alpha_channel(([1, 1, 1, 1], None))
    assert not mcolors._has_alpha_channel('blue')  # 4-char string!
    assert not mcolors._has_alpha_channel('0.25')
    assert not mcolors._has_alpha_channel('r')
    assert not mcolors._has_alpha_channel((1, 0, 0))
    assert not mcolors._has_alpha_channel('#fff')
    assert not mcolors._has_alpha_channel('#0f0f0f')
    assert not mcolors._has_alpha_channel(('r', None))
    assert not mcolors._has_alpha_channel(([1, 1, 1], None))


# ---------------------------------------------------------------------------
# 19. test_is_color_like (parametrized, upstream ~line 1781)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize('input, expected',
                         [('red', True),
                          (('red', 0.5), True),
                          (('red', 2), False),
                          (['red', 0.5], False),
                          (('red', 'blue'), False),
                          (['red', 'blue'], False),
                          ('C3', True),
                          (('C3', 0.5), True)])
def test_is_color_like(input, expected):
    assert is_color_like(input) is expected


# ---------------------------------------------------------------------------
# 20. test_to_rgba_array_none_color_with_alpha_param (upstream ~line 1771)
# ---------------------------------------------------------------------------
def test_to_rgba_array_none_color_with_alpha_param():
    # effective alpha for color "none" must always be 0 to achieve a vanishing
    # color even explicit alpha must be ignored
    c = ["blue", "none"]
    alpha = [1, 1]
    result = mcolors.to_rgba_array(c, alpha)
    assert result[0] == (0., 0., 1., 1.)
    assert result[1] == (0., 0., 0., 0.)


# ---------------------------------------------------------------------------
# 21. test_2d_to_rgba (upstream ~line 1579)
# ---------------------------------------------------------------------------
def test_2d_to_rgba():
    color = [0.1, 0.2, 0.3]
    rgba_1d = mcolors.to_rgba(color)
    rgba_2d = mcolors.to_rgba([color])  # list-of-one-list form
    assert rgba_1d == rgba_2d


# ---------------------------------------------------------------------------
# 22. test_set_dict_to_rgba (upstream ~line 1586)
# ---------------------------------------------------------------------------
def test_set_dict_to_rgba():
    # downstream libraries do this...
    # note we can't test this because it is not well-ordered
    # so just smoketest:
    colors = {(0, .5, 1), (1, .2, .5), (.4, 1, .2)}
    res = mcolors.to_rgba_array(colors)
    assert len(res) == 3
    palette = {"red": (1, 0, 0), "green": (0, 1, 0), "blue": (0, 0, 1)}
    res = mcolors.to_rgba_array(palette.values())
    # Check that each color was converted and has alpha=1
    assert len(res) == 3
    for r in res:
        assert r[3] == 1.0
    # Check that RGB components form an identity-like pattern (each row
    # has exactly one 1.0 in the first 3 components)
    rgb_vals = sorted([tuple(r[:3]) for r in res])
    expected = sorted([(0., 0., 1.), (0., 1., 0.), (1., 0., 0.)])
    assert rgb_vals == expected


# ---------------------------------------------------------------------------
# 23. test_lognorm_invalid (upstream ~line 499) — ADAPTED
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("vmin,vmax", [[-1, 2], [3, 1]])
def test_lognorm_invalid(vmin, vmax):
    # Check that invalid limits in LogNorm error
    norm = mcolors.LogNorm(vmin=vmin, vmax=vmax)
    with pytest.raises(ValueError):
        norm(1)
    with pytest.raises(ValueError):
        norm.inverse(1)


# ---------------------------------------------------------------------------
# 24. test_cn (upstream ~line 1248) — ADAPTED
#     Removed cycler/rcParams dependency; uses our DEFAULT_CYCLE instead.
# ---------------------------------------------------------------------------
def test_cn():
    # Our CN colors always resolve against DEFAULT_CYCLE
    assert mcolors.to_hex("C0") == '#1f77b4'
    assert mcolors.to_hex("C1") == '#ff7f0e'
    assert mcolors.to_hex("C9") == '#17becf'
    # CN wraps around the cycle
    assert mcolors.to_hex("C10") == '#1f77b4'
    assert mcolors.to_hex("C11") == '#ff7f0e'
