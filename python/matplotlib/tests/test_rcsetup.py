"""Tests for matplotlib.rcsetup — RcParams and rc_context."""

import pytest

import matplotlib
from matplotlib.rcsetup import RcParams, rc_context, _default_params


class TestRcParamsIsDict:
    def test_rcparams_is_dict_subclass(self):
        """RcParams inherits from dict."""
        assert issubclass(RcParams, dict)

    def test_rcparams_instance_is_dict(self):
        """An RcParams instance passes isinstance check for dict."""
        rc = RcParams({'a': 1})
        assert isinstance(rc, dict)

    def test_global_rcparams_is_rcparams(self):
        """The global matplotlib.rcParams is an RcParams instance."""
        assert isinstance(matplotlib.rcParams, RcParams)


class TestRcParamsDefaults:
    def test_lines_linewidth_default(self):
        """Default lines.linewidth is 1.5."""
        assert matplotlib.rcParams['lines.linewidth'] == 1.5

    def test_figure_figsize_default(self):
        """Default figure.figsize is [6.4, 4.8]."""
        assert matplotlib.rcParams['figure.figsize'] == [6.4, 4.8]

    def test_figure_dpi_default(self):
        """Default figure.dpi is 100."""
        assert matplotlib.rcParams['figure.dpi'] == 100

    def test_lines_linestyle_default(self):
        """Default lines.linestyle is '-'."""
        assert matplotlib.rcParams['lines.linestyle'] == '-'

    def test_axes_facecolor_default(self):
        """Default axes.facecolor is 'white'."""
        assert matplotlib.rcParams['axes.facecolor'] == 'white'

    def test_savefig_format_default(self):
        """Default savefig.format is 'png'."""
        assert matplotlib.rcParams['savefig.format'] == 'png'

    def test_default_params_all_present(self):
        """All keys from _default_params are present in global rcParams."""
        for key in _default_params:
            assert key in matplotlib.rcParams


class TestRcParamsRepr:
    def test_repr_starts_with_rcparams(self):
        """repr output starts with 'RcParams({'."""
        rc = RcParams({'a': 1})
        assert repr(rc).startswith("RcParams({")

    def test_repr_ends_with_closing(self):
        """repr output ends with '})'."""
        rc = RcParams({'a': 1})
        assert repr(rc).rstrip().endswith("})")

    def test_str_equals_repr(self):
        """str(rc) produces the same output as repr(rc)."""
        rc = RcParams({'x': 10, 'y': 20})
        assert str(rc) == repr(rc)

    def test_repr_contains_keys(self):
        """repr includes the stored keys."""
        rc = RcParams({'lines.linewidth': 2.0, 'figure.dpi': 72})
        text = repr(rc)
        assert "'lines.linewidth'" in text
        assert "'figure.dpi'" in text

    def test_repr_sorted_keys(self):
        """Keys in repr appear in sorted order."""
        rc = RcParams({'z_key': 3, 'a_key': 1, 'm_key': 2})
        text = repr(rc)
        pos_a = text.index("'a_key'")
        pos_m = text.index("'m_key'")
        pos_z = text.index("'z_key'")
        assert pos_a < pos_m < pos_z

    def test_repr_empty(self):
        """repr of empty RcParams is well-formed."""
        rc = RcParams()
        text = repr(rc)
        assert text.startswith("RcParams({")
        assert text.rstrip().endswith("})")


class TestRcParamsFindAll:
    def test_find_all_exact_match(self):
        """find_all with a literal key name returns that entry."""
        rc = RcParams({'lines.linewidth': 1.5, 'lines.color': 'C0'})
        result = rc.find_all('lines.linewidth')
        assert 'lines.linewidth' in result
        assert result['lines.linewidth'] == 1.5

    def test_find_all_prefix_pattern(self):
        """find_all with '^lines' matches all lines.* keys."""
        result = matplotlib.rcParams.find_all(r'^lines\.')
        assert len(result) > 0
        for key in result:
            assert key.startswith('lines.')

    def test_find_all_no_match(self):
        """find_all with a pattern matching nothing returns empty dict."""
        rc = RcParams({'a': 1})
        result = rc.find_all('zzz_no_match')
        assert result == {}

    def test_find_all_regex_dot(self):
        """find_all uses regex, so '.' matches any character."""
        rc = RcParams({'abc': 1, 'axc': 2, 'def': 3})
        result = rc.find_all('a.c')
        assert 'abc' in result
        assert 'axc' in result
        assert 'def' not in result

    def test_find_all_returns_dict(self):
        """find_all returns a plain dict, not RcParams."""
        rc = RcParams({'key': 'val'})
        result = rc.find_all('key')
        assert type(result) is dict

    def test_find_all_on_global_rcparams(self):
        """find_all works on the global rcParams instance."""
        result = matplotlib.rcParams.find_all(r'^figure\.')
        assert 'figure.figsize' in result
        assert 'figure.dpi' in result


class TestRcParamsCopy:
    def test_copy_returns_rcparams(self):
        """copy() returns an RcParams instance, not a plain dict."""
        rc = RcParams({'a': 1})
        cp = rc.copy()
        assert isinstance(cp, RcParams)

    def test_copy_has_same_values(self):
        """copy() contains the same key/value pairs."""
        rc = RcParams({'x': 10, 'y': 20})
        cp = rc.copy()
        assert cp == rc

    def test_copy_is_independent(self):
        """Mutating the copy does not affect the original."""
        rc = RcParams({'a': 1, 'b': 2})
        cp = rc.copy()
        cp['a'] = 999
        assert rc['a'] == 1

    def test_original_mutation_does_not_affect_copy(self):
        """Mutating the original does not affect the copy."""
        rc = RcParams({'a': 1})
        cp = rc.copy()
        rc['a'] = 999
        assert cp['a'] == 1

    def test_copy_is_different_object(self):
        """copy() returns a new object, not the same reference."""
        rc = RcParams({'a': 1})
        cp = rc.copy()
        assert rc is not cp


class TestRcContext:
    def test_overrides_value_inside_context(self):
        """rc_context temporarily overrides rcParams values."""
        original = matplotlib.rcParams['lines.linewidth']
        with rc_context({'lines.linewidth': 99.0}):
            assert matplotlib.rcParams['lines.linewidth'] == 99.0
        assert matplotlib.rcParams['lines.linewidth'] == original

    def test_restores_value_on_exit(self):
        """Values are restored after the context manager exits."""
        original = matplotlib.rcParams['figure.dpi']
        with rc_context({'figure.dpi': 300}):
            pass
        assert matplotlib.rcParams['figure.dpi'] == original

    def test_restores_on_exception(self):
        """Values are restored even when an exception occurs."""
        original = matplotlib.rcParams['lines.linewidth']
        with pytest.raises(RuntimeError):
            with rc_context({'lines.linewidth': 42.0}):
                assert matplotlib.rcParams['lines.linewidth'] == 42.0
                raise RuntimeError("deliberate error")
        assert matplotlib.rcParams['lines.linewidth'] == original

    def test_no_overrides(self):
        """rc_context with no arguments does not change rcParams."""
        original_lw = matplotlib.rcParams['lines.linewidth']
        with rc_context():
            assert matplotlib.rcParams['lines.linewidth'] == original_lw
        assert matplotlib.rcParams['lines.linewidth'] == original_lw

    def test_multiple_overrides(self):
        """rc_context can override multiple keys at once."""
        orig_lw = matplotlib.rcParams['lines.linewidth']
        orig_dpi = matplotlib.rcParams['figure.dpi']
        with rc_context({'lines.linewidth': 5.0, 'figure.dpi': 200}):
            assert matplotlib.rcParams['lines.linewidth'] == 5.0
            assert matplotlib.rcParams['figure.dpi'] == 200
        assert matplotlib.rcParams['lines.linewidth'] == orig_lw
        assert matplotlib.rcParams['figure.dpi'] == orig_dpi


class TestRcContextNested:
    def test_nested_contexts(self):
        """Nested rc_context calls each restore correctly."""
        original = matplotlib.rcParams['lines.linewidth']
        with rc_context({'lines.linewidth': 10.0}):
            assert matplotlib.rcParams['lines.linewidth'] == 10.0
            with rc_context({'lines.linewidth': 20.0}):
                assert matplotlib.rcParams['lines.linewidth'] == 20.0
            assert matplotlib.rcParams['lines.linewidth'] == 10.0
        assert matplotlib.rcParams['lines.linewidth'] == original

    def test_nested_different_keys(self):
        """Nested contexts overriding different keys restore independently."""
        orig_lw = matplotlib.rcParams['lines.linewidth']
        orig_dpi = matplotlib.rcParams['figure.dpi']
        with rc_context({'lines.linewidth': 10.0}):
            with rc_context({'figure.dpi': 300}):
                assert matplotlib.rcParams['lines.linewidth'] == 10.0
                assert matplotlib.rcParams['figure.dpi'] == 300
            assert matplotlib.rcParams['figure.dpi'] == orig_dpi
            assert matplotlib.rcParams['lines.linewidth'] == 10.0
        assert matplotlib.rcParams['lines.linewidth'] == orig_lw

    def test_deeply_nested(self):
        """Three levels of nesting restore correctly."""
        original = matplotlib.rcParams['lines.linewidth']
        with rc_context({'lines.linewidth': 1.0}):
            with rc_context({'lines.linewidth': 2.0}):
                with rc_context({'lines.linewidth': 3.0}):
                    assert matplotlib.rcParams['lines.linewidth'] == 3.0
                assert matplotlib.rcParams['lines.linewidth'] == 2.0
            assert matplotlib.rcParams['lines.linewidth'] == 1.0
        assert matplotlib.rcParams['lines.linewidth'] == original


class TestRcContextNewKeys:
    def test_new_key_added_inside_context(self):
        """A new key set via rc_context is visible inside the context."""
        key = '_test_temp_key_12345'
        assert key not in matplotlib.rcParams
        with rc_context({key: 'hello'}):
            assert matplotlib.rcParams[key] == 'hello'

    def test_new_key_removed_on_exit(self):
        """A new key introduced by rc_context is removed on exit."""
        key = '_test_temp_key_67890'
        assert key not in matplotlib.rcParams
        with rc_context({key: 'temporary'}):
            assert key in matplotlib.rcParams
        assert key not in matplotlib.rcParams

    def test_new_key_removed_on_exception(self):
        """A new key is cleaned up even when an exception occurs."""
        key = '_test_temp_key_exception'
        assert key not in matplotlib.rcParams
        with pytest.raises(ValueError):
            with rc_context({key: 'will be removed'}):
                raise ValueError("deliberate")
        assert key not in matplotlib.rcParams

    def test_multiple_new_keys_cleaned_up(self):
        """Multiple new keys are all cleaned up on exit."""
        keys = ['_test_nk_a', '_test_nk_b', '_test_nk_c']
        for k in keys:
            assert k not in matplotlib.rcParams
        overrides = {k: idx for idx, k in enumerate(keys)}
        with rc_context(overrides):
            for k in keys:
                assert k in matplotlib.rcParams
        for k in keys:
            assert k not in matplotlib.rcParams
