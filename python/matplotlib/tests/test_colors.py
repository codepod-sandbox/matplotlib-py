"""Tests for matplotlib.colors module.

Covers color name resolution, hex conversion, to_rgba / to_rgba_array,
is_color_like, same_color, _has_alpha_channel, Normalize, LogNorm, and
parse_fmt.
"""

import math
import pytest

from matplotlib.colors import (
    CSS4_COLORS,
    TABLEAU_COLORS,
    BASE_COLORS,
    DEFAULT_CYCLE,
    _colors_full_map,
    to_rgba,
    to_rgba_array,
    to_hex,
    to_rgb,
    is_color_like,
    same_color,
    _has_alpha_channel,
    Normalize,
    LogNorm,
    parse_fmt,
)


# ===================================================================
# Color Names (4 tests)
# ===================================================================

class TestColorNames:
    def test_named_colors_resolve(self):
        """Named colors resolve to the correct hex values."""
        assert to_hex('blue') == '#0000ff'
        assert to_hex('red') == '#ff0000'
        assert to_hex('tab:blue') == '#1f77b4'

    def test_grey_gray(self):
        """Every 'grey' CSS4 name has a 'gray' counterpart and vice versa."""
        grey_names = [n for n in CSS4_COLORS if 'grey' in n]
        gray_names = [n for n in CSS4_COLORS if 'gray' in n]
        assert len(grey_names) > 0
        assert len(grey_names) == len(gray_names)
        for name in grey_names:
            gray_eq = name.replace('grey', 'gray')
            assert gray_eq in _colors_full_map, (
                f"Missing gray equivalent for {name}")
            assert _colors_full_map[name] == _colors_full_map[gray_eq]
        for name in gray_names:
            grey_eq = name.replace('gray', 'grey')
            assert grey_eq in _colors_full_map, (
                f"Missing grey equivalent for {name}")
            assert _colors_full_map[name] == _colors_full_map[grey_eq]

    def test_tableau_order(self):
        """TABLEAU_COLORS values match the expected C0-C9 hex order."""
        expected = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
        ]
        assert list(TABLEAU_COLORS.values()) == expected

    def test_cn_colors(self):
        """CN cycle colors C0..C9 resolve to the default color cycle."""
        assert to_hex('C0') == '#1f77b4'
        assert to_hex('C1') == '#ff7f0e'
        assert to_hex('C9') == '#17becf'


# ===================================================================
# Hex Conversion (3 tests)
# ===================================================================

class TestHexConversion:
    def test_hex_shorthand(self):
        """3- and 4-char hex shorthands expand correctly."""
        assert same_color('#123', '#112233')
        assert same_color('#123a', '#112233aa')

    def test_to_hex_roundtrip(self):
        """color -> to_rgba -> to_hex -> to_rgba preserves values."""
        for color in ('red', 'tab:blue', '#abcdef', 'C3'):
            rgba = to_rgba(color)
            hex_str = to_hex(rgba)
            rgba2 = to_rgba(hex_str)
            for a, b in zip(rgba, rgba2):
                assert abs(a - b) < 1e-2, (
                    f"Roundtrip failed for {color}: {rgba} != {rgba2}")

    def test_to_hex_keep_alpha(self):
        """to_hex with keep_alpha=True appends alpha hex digits."""
        assert to_hex((1, 0, 0, 0.5), keep_alpha=True) == '#ff000080'


# ===================================================================
# to_rgba (12 tests)
# ===================================================================

class TestToRgba:
    def test_named_color(self):
        assert to_rgba('red') == (1.0, 0.0, 0.0, 1.0)

    def test_hex_color(self):
        r, g, b, a = to_rgba('#ff8000')
        assert abs(r - 1.0) < 1e-3
        assert abs(g - 0x80 / 255.0) < 1e-3
        assert abs(b - 0.0) < 1e-3
        assert a == 1.0

    def test_rgb_tuple(self):
        assert to_rgba((1, 0, 0)) == (1.0, 0.0, 0.0, 1.0)

    def test_rgba_tuple(self):
        assert to_rgba((1, 0, 0, 0.5)) == (1.0, 0.0, 0.0, 0.5)

    def test_alpha_override(self):
        r, g, b, a = to_rgba('red', alpha=0.5)
        assert a == 0.5
        assert (r, g, b) == (1.0, 0.0, 0.0)

    def test_none_transparent(self):
        assert to_rgba('none') == (0.0, 0.0, 0.0, 0.0)

    def test_grayscale_string(self):
        assert to_rgba('0.5') == (0.5, 0.5, 0.5, 1.0)

    @pytest.mark.parametrize("color_alpha,expected_rgb,expected_a", [
        (('red', 0.5), (1.0, 0.0, 0.0), 0.5),
        (('#ff0000', 0.3), (1.0, 0.0, 0.0), 0.3),
        (((1, 0, 0), 0.7), (1.0, 0.0, 0.0), 0.7),
    ])
    def test_color_alpha_tuple(self, color_alpha, expected_rgb, expected_a):
        """(color, alpha) tuples set the alpha component."""
        r, g, b, a = to_rgba(color_alpha)
        assert (r, g, b) == expected_rgb
        assert abs(a - expected_a) < 1e-10

    def test_explicit_alpha_overrides_tuple(self):
        """Explicit alpha= kwarg overrides the alpha in a (color, alpha) tuple."""
        _, _, _, a = to_rgba(('red', 0.1), alpha=0.9)
        assert a == 0.9

    def test_invalid_alpha_in_tuple(self):
        """(color, alpha) with out-of-range alpha raises ValueError."""
        with pytest.raises(ValueError, match="alpha"):
            to_rgba(('blue', 2.0))
        with pytest.raises(ValueError, match="alpha"):
            to_rgba(('red', -0.1))

    @pytest.mark.parametrize("bad_color", ['5', '-1', 'nan', 'unknown_color'])
    def test_failed_conversions(self, bad_color):
        """Invalid color strings raise ValueError."""
        with pytest.raises(ValueError):
            to_rgba(bad_color)

    def test_invalid_alpha_kwarg(self):
        """alpha kwarg outside [0, 1] raises ValueError."""
        with pytest.raises(ValueError, match="alpha"):
            to_rgba('red', alpha=1.5)
        with pytest.raises(ValueError, match="alpha"):
            to_rgba('red', alpha=-0.5)

    def test_2d_color(self):
        """A 1-D list [r, g, b] is treated like an RGB tuple."""
        assert to_rgba([0.5, 0.5, 0.5]) == (0.5, 0.5, 0.5, 1.0)


# ===================================================================
# to_rgba_array (6 tests)
# ===================================================================

class TestToRgbaArray:
    def test_single_str(self):
        result = to_rgba_array('red')
        assert len(result) == 1
        assert result[0] == (1.0, 0.0, 0.0, 1.0)

    def test_two_colors(self):
        result = to_rgba_array(['k', 'w'])
        assert len(result) == 2
        assert result[0] == (0.0, 0.0, 0.0, 1.0)
        assert result[1] == (1.0, 1.0, 1.0, 1.0)

    def test_none_color(self):
        # "none" as a single string returns empty list (upstream compat)
        result = to_rgba_array('none')
        assert len(result) == 0
        # "none" in a list of colors still resolves to transparent
        result = to_rgba_array(['none'])
        assert len(result) == 1
        assert result[0] == (0.0, 0.0, 0.0, 0.0)

    def test_color_list_with_alpha(self):
        """(list_of_colors, alpha) tuple sets alpha on all colors."""
        result = to_rgba_array((['black', 'white'], 0.9))
        assert len(result) == 2
        assert result[0] == (0.0, 0.0, 0.0, 0.9)
        assert result[1] == (1.0, 1.0, 1.0, 0.9)

    def test_explicit_alpha_overrides(self):
        """Explicit alpha= kwarg overrides the alpha from the tuple."""
        result = to_rgba_array((['black', 'white'], 0.9), alpha=0.5)
        assert len(result) == 2
        assert result[0][3] == 0.5
        assert result[1][3] == 0.5

    def test_alpha_list(self):
        """Per-element alpha list sets individual alpha values."""
        result = to_rgba_array(['red', 'blue'], alpha=[0.2, 0.8])
        assert len(result) == 2
        assert abs(result[0][3] - 0.2) < 1e-10
        assert abs(result[1][3] - 0.8) < 1e-10


# ===================================================================
# is_color_like (1 parametrized test)
# ===================================================================

class TestIsColorLike:
    @pytest.mark.parametrize("value,expected", [
        ('red', True),
        (('red', 0.5), True),
        ('C3', True),
        ('notacolor', False),
        ('#ff0000', True),
        ('0.5', True),
        ((1, 0, 0), True),
    ])
    def test_is_color_like(self, value, expected):
        assert is_color_like(value) == expected


# ===================================================================
# same_color (4 tests)
# ===================================================================

class TestSameColor:
    def test_same_named(self):
        assert same_color('k', (0, 0, 0))

    def test_same_lists(self):
        assert same_color(['red', 'blue'], ['r', 'b'])

    def test_none_equality(self):
        assert same_color('none', 'none')

    def test_mismatched_lengths(self):
        with pytest.raises(ValueError):
            same_color(['r', 'g'], ['r'])


# ===================================================================
# _has_alpha_channel (1 parametrized test)
# ===================================================================

class TestHasAlphaChannel:
    @pytest.mark.parametrize("color,expected", [
        ((1, 0, 0), False),
        ((1, 0, 0, 0.5), True),
        ('#ff0000', False),
        ('#ff000080', True),
        ('#fff', False),
        ('#fffa', True),
        (('red', 0.5), True),
    ])
    def test_has_alpha_channel(self, color, expected):
        assert _has_alpha_channel(color) == expected


# ===================================================================
# Normalize (3 tests)
# ===================================================================

class TestNormalize:
    def test_basic(self):
        norm = Normalize(vmin=0, vmax=10)
        assert norm(0) == 0.0
        assert norm(5) == 0.5
        assert norm(10) == 1.0

    def test_inverse(self):
        norm = Normalize(vmin=0, vmax=10)
        for val in [0.0, 0.25, 0.5, 0.75, 1.0]:
            # norm.inverse maps [0,1] -> data, norm maps data -> [0,1]
            result = norm(norm.inverse(val))
            assert abs(result - val) < 1e-10, (
                f"Roundtrip failed for {val}: got {result}")

    def test_clip(self):
        norm = Normalize(vmin=0, vmax=10, clip=True)
        assert norm(-5) == 0.0
        assert norm(15) == 1.0
        assert norm(5) == 0.5


# ===================================================================
# LogNorm (4 tests)
# ===================================================================

class TestLogNorm:
    def test_basic(self):
        norm = LogNorm(vmin=1, vmax=100)
        result = norm(10)
        assert abs(result - 0.5) < 1e-10

    def test_clip(self):
        norm = LogNorm(vmin=1, vmax=100, clip=True)
        assert norm(1000) == 1.0
        assert norm(0.01) == 0.0

    def test_inverse(self):
        norm = LogNorm(vmin=1, vmax=100)
        for val in [0.0, 0.25, 0.5, 0.75, 1.0]:
            data = norm.inverse(val)
            back = norm(data)
            assert abs(back - val) < 1e-10, (
                f"Roundtrip failed for {val}: got {back}")

    @pytest.mark.parametrize("vmin,vmax", [
        (-1, 2),
        (3, 1),
    ])
    def test_invalid(self, vmin, vmax):
        """LogNorm raises ValueError for invalid vmin/vmax."""
        norm = LogNorm(vmin=vmin, vmax=vmax)
        with pytest.raises(ValueError):
            norm(1)


# ===================================================================
# parse_fmt (5 tests)
# ===================================================================

class TestParseFmt:
    def test_empty(self):
        assert parse_fmt('') == (None, None, None)

    def test_color_only(self):
        assert parse_fmt('r') == ('r', None, None)

    def test_marker_only(self):
        assert parse_fmt('o') == (None, 'o', None)

    def test_full(self):
        assert parse_fmt('ro-') == ('r', 'o', '-')

    def test_dashed(self):
        assert parse_fmt('b--') == ('b', None, '--')
