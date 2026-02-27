"""Tests for matplotlib.collections module --- Collection and PathCollection."""

import pytest

from matplotlib.collections import Collection, PathCollection
from matplotlib.colors import to_hex


# ===================================================================
# Collection base class
# ===================================================================

class TestCollection:
    def test_default_zorder(self):
        """Collection class zorder is 1."""
        assert Collection.zorder == 1

    def test_instance_zorder(self):
        """Collection instance inherits zorder=1."""
        c = Collection()
        assert c.get_zorder() == 1

    def test_default_visible(self):
        """Collection is visible by default."""
        c = Collection()
        assert c.get_visible() is True

    def test_default_alpha(self):
        """Collection alpha is None by default."""
        c = Collection()
        assert c.get_alpha() is None

    def test_default_label(self):
        """Collection label is empty string by default."""
        c = Collection()
        assert c.get_label() == ''

    def test_set_kwargs_forwarded(self):
        """Collection forwards kwargs to Artist.set()."""
        c = Collection(visible=False, alpha=0.5)
        assert c.get_visible() is False
        assert c.get_alpha() == 0.5


# ===================================================================
# PathCollection construction defaults
# ===================================================================

class TestPathCollectionDefaults:
    def test_default_offsets(self):
        """Default offsets is an empty list."""
        pc = PathCollection()
        assert pc.get_offsets() == []

    def test_default_sizes(self):
        """Default sizes is [20.0]."""
        pc = PathCollection()
        assert pc.get_sizes() == [20.0]

    def test_default_facecolors(self):
        """Default facecolors is an empty list."""
        pc = PathCollection()
        assert pc.get_facecolors() == []

    def test_default_edgecolors(self):
        """Default edgecolors is an empty list."""
        pc = PathCollection()
        assert pc.get_edgecolors() == []

    def test_default_label(self):
        """Default label is empty string (inherited from Artist)."""
        pc = PathCollection()
        assert pc.get_label() == ''

    def test_default_zorder(self):
        """PathCollection inherits Collection zorder=1."""
        pc = PathCollection()
        assert pc.get_zorder() == 1


# ===================================================================
# PathCollection with explicit data
# ===================================================================

class TestPathCollectionExplicitData:
    def test_explicit_offsets(self):
        """Offsets passed at construction are stored."""
        offsets = [(1, 2), (3, 4)]
        pc = PathCollection(offsets=offsets)
        assert pc.get_offsets() == [(1, 2), (3, 4)]

    def test_explicit_sizes(self):
        """Sizes passed at construction are stored."""
        pc = PathCollection(sizes=[10.0, 30.0, 50.0])
        assert pc.get_sizes() == [10.0, 30.0, 50.0]

    def test_explicit_facecolors(self):
        """Facecolors passed at construction are stored."""
        pc = PathCollection(facecolors=['red', 'blue'])
        assert pc.get_facecolors() == ['red', 'blue']

    def test_explicit_edgecolors(self):
        """Edgecolors passed at construction are stored."""
        pc = PathCollection(edgecolors=['green'])
        assert pc.get_edgecolors() == ['green']

    def test_explicit_label(self):
        """Label passed at construction is stored."""
        pc = PathCollection(label='scatter1')
        assert pc.get_label() == 'scatter1'

    def test_all_params_at_once(self):
        """All parameters can be set simultaneously at construction."""
        pc = PathCollection(
            offsets=[(0, 0)],
            sizes=[50.0],
            facecolors=['red'],
            edgecolors=['black'],
            label='full',
        )
        assert pc.get_offsets() == [(0, 0)]
        assert pc.get_sizes() == [50.0]
        assert pc.get_facecolors() == ['red']
        assert pc.get_edgecolors() == ['black']
        assert pc.get_label() == 'full'


# ===================================================================
# get/set offsets round-trip
# ===================================================================

class TestOffsetsRoundTrip:
    def test_set_get_offsets(self):
        """set_offsets then get_offsets returns the same data."""
        pc = PathCollection()
        pc.set_offsets([(10, 20), (30, 40)])
        assert pc.get_offsets() == [(10, 20), (30, 40)]

    def test_set_offsets_replaces(self):
        """set_offsets replaces previous offsets entirely."""
        pc = PathCollection(offsets=[(1, 2)])
        pc.set_offsets([(5, 6), (7, 8)])
        assert pc.get_offsets() == [(5, 6), (7, 8)]

    def test_set_offsets_empty(self):
        """set_offsets with empty list clears offsets."""
        pc = PathCollection(offsets=[(1, 2)])
        pc.set_offsets([])
        assert pc.get_offsets() == []


# ===================================================================
# get/set sizes round-trip
# ===================================================================

class TestSizesRoundTrip:
    def test_set_get_sizes(self):
        """set_sizes then get_sizes returns the same data."""
        pc = PathCollection()
        pc.set_sizes([100.0, 200.0])
        assert pc.get_sizes() == [100.0, 200.0]

    def test_set_sizes_replaces(self):
        """set_sizes replaces previous sizes entirely."""
        pc = PathCollection(sizes=[5.0])
        pc.set_sizes([10.0, 15.0, 20.0])
        assert pc.get_sizes() == [10.0, 15.0, 20.0]

    def test_set_sizes_empty(self):
        """set_sizes with empty list clears sizes."""
        pc = PathCollection()
        pc.set_sizes([])
        assert pc.get_sizes() == []


# ===================================================================
# get/set facecolors round-trip
# ===================================================================

class TestFacecolorsRoundTrip:
    def test_set_get_facecolors(self):
        """set_facecolors then get_facecolors returns the same data."""
        pc = PathCollection()
        pc.set_facecolors(['red', 'green'])
        assert pc.get_facecolors() == ['red', 'green']

    def test_set_facecolors_replaces(self):
        """set_facecolors replaces previous facecolors."""
        pc = PathCollection(facecolors=['blue'])
        pc.set_facecolors(['yellow', 'cyan'])
        assert pc.get_facecolors() == ['yellow', 'cyan']

    def test_set_facecolors_empty(self):
        """set_facecolors with empty list clears facecolors."""
        pc = PathCollection(facecolors=['red'])
        pc.set_facecolors([])
        assert pc.get_facecolors() == []

    def test_facecolors_tuples(self):
        """Facecolors can be RGBA tuples."""
        colors = [(1.0, 0.0, 0.0, 1.0), (0.0, 0.0, 1.0, 0.5)]
        pc = PathCollection(facecolors=colors)
        assert pc.get_facecolors() == colors


# ===================================================================
# get/set edgecolors round-trip
# ===================================================================

class TestEdgecolorsRoundTrip:
    def test_set_get_edgecolors(self):
        """set_edgecolors then get_edgecolors returns the same data."""
        pc = PathCollection()
        pc.set_edgecolors(['black', 'white'])
        assert pc.get_edgecolors() == ['black', 'white']

    def test_set_edgecolors_replaces(self):
        """set_edgecolors replaces previous edgecolors."""
        pc = PathCollection(edgecolors=['gray'])
        pc.set_edgecolors(['red', 'blue'])
        assert pc.get_edgecolors() == ['red', 'blue']

    def test_set_edgecolors_empty(self):
        """set_edgecolors with empty list clears edgecolors."""
        pc = PathCollection(edgecolors=['black'])
        pc.set_edgecolors([])
        assert pc.get_edgecolors() == []

    def test_edgecolors_tuples(self):
        """Edgecolors can be RGBA tuples."""
        colors = [(0.0, 0.0, 0.0, 1.0)]
        pc = PathCollection(edgecolors=colors)
        assert pc.get_edgecolors() == colors


# ===================================================================
# Data returned as copies (not references)
# ===================================================================

class TestDataCopies:
    def test_get_offsets_returns_copy(self):
        """get_offsets returns a new list each time, not the internal one."""
        pc = PathCollection(offsets=[(1, 2)])
        result = pc.get_offsets()
        result.append((99, 99))
        assert pc.get_offsets() == [(1, 2)]

    def test_set_offsets_copies_input(self):
        """set_offsets copies the input; later mutations do not affect the object."""
        data = [(1, 2), (3, 4)]
        pc = PathCollection()
        pc.set_offsets(data)
        data.append((5, 6))
        assert pc.get_offsets() == [(1, 2), (3, 4)]

    def test_get_sizes_returns_copy(self):
        """get_sizes returns a new list, not the internal one."""
        pc = PathCollection(sizes=[20.0])
        result = pc.get_sizes()
        result.append(999.0)
        assert pc.get_sizes() == [20.0]

    def test_set_sizes_copies_input(self):
        """set_sizes copies the input list."""
        data = [10.0, 20.0]
        pc = PathCollection()
        pc.set_sizes(data)
        data.append(30.0)
        assert pc.get_sizes() == [10.0, 20.0]

    def test_get_facecolors_returns_copy(self):
        """get_facecolors returns a new list, not the internal one."""
        pc = PathCollection(facecolors=['red'])
        result = pc.get_facecolors()
        result.append('blue')
        assert pc.get_facecolors() == ['red']

    def test_set_facecolors_copies_input(self):
        """set_facecolors copies the input list."""
        data = ['red']
        pc = PathCollection()
        pc.set_facecolors(data)
        data.append('green')
        assert pc.get_facecolors() == ['red']

    def test_get_edgecolors_returns_copy(self):
        """get_edgecolors returns a new list, not the internal one."""
        pc = PathCollection(edgecolors=['black'])
        result = pc.get_edgecolors()
        result.append('white')
        assert pc.get_edgecolors() == ['black']

    def test_set_edgecolors_copies_input(self):
        """set_edgecolors copies the input list."""
        data = ['black']
        pc = PathCollection()
        pc.set_edgecolors(data)
        data.append('white')
        assert pc.get_edgecolors() == ['black']

    def test_constructor_offsets_copies_input(self):
        """Constructor copies the offsets argument."""
        data = [(1, 2)]
        pc = PathCollection(offsets=data)
        data.append((3, 4))
        assert pc.get_offsets() == [(1, 2)]

    def test_constructor_sizes_copies_input(self):
        """Constructor copies the sizes argument."""
        data = [10.0]
        pc = PathCollection(sizes=data)
        data.append(20.0)
        assert pc.get_sizes() == [10.0]


# ===================================================================
# _as_element returns correct dict structure
# ===================================================================

class TestAsElement:
    def test_type_is_scatter(self):
        """_as_element dict has type='scatter'."""
        pc = PathCollection()
        elem = pc._as_element()
        assert elem['type'] == 'scatter'

    def test_required_keys(self):
        """_as_element dict contains all required keys."""
        pc = PathCollection()
        elem = pc._as_element()
        assert set(elem.keys()) == {'type', 'x', 'y', 's', 'color', 'label'}

    def test_offsets_split_to_xy(self):
        """_as_element splits offsets into separate x and y lists."""
        pc = PathCollection(offsets=[(1, 10), (2, 20), (3, 30)])
        elem = pc._as_element()
        assert elem['x'] == [1, 2, 3]
        assert elem['y'] == [10, 20, 30]

    def test_empty_offsets_gives_empty_xy(self):
        """_as_element with no offsets produces empty x and y."""
        pc = PathCollection()
        elem = pc._as_element()
        assert elem['x'] == []
        assert elem['y'] == []

    def test_size_from_first_element(self):
        """_as_element uses the first size value."""
        pc = PathCollection(sizes=[42.0, 100.0])
        elem = pc._as_element()
        assert elem['s'] == 42.0

    def test_default_size_in_element(self):
        """_as_element uses default size 20.0 when using defaults."""
        pc = PathCollection()
        elem = pc._as_element()
        assert elem['s'] == 20.0

    def test_empty_sizes_fallback(self):
        """_as_element uses 20.0 fallback when sizes list is empty."""
        pc = PathCollection(sizes=[])
        elem = pc._as_element()
        assert elem['s'] == 20.0

    def test_color_from_facecolor(self):
        """_as_element converts first facecolor to hex."""
        pc = PathCollection(facecolors=['red'])
        elem = pc._as_element()
        assert elem['color'] == to_hex('red')

    def test_color_default_when_no_facecolors(self):
        """_as_element uses C0 color when no facecolors are set."""
        pc = PathCollection()
        elem = pc._as_element()
        assert elem['color'] == to_hex('C0')

    def test_label_in_element(self):
        """_as_element includes the label."""
        pc = PathCollection(label='test_label')
        elem = pc._as_element()
        assert elem['label'] == 'test_label'

    def test_label_none_when_unset(self):
        """_as_element label is None when no label was set."""
        pc = PathCollection()
        elem = pc._as_element()
        assert elem['label'] is None


# ===================================================================
# Label support
# ===================================================================

class TestLabelSupport:
    def test_label_via_constructor(self):
        """Label set in constructor is retrievable."""
        pc = PathCollection(label='my_scatter')
        assert pc.get_label() == 'my_scatter'

    def test_label_via_set_label(self):
        """Label set via set_label is retrievable."""
        pc = PathCollection()
        pc.set_label('updated')
        assert pc.get_label() == 'updated'

    def test_label_overwrite(self):
        """set_label overwrites a previously set label."""
        pc = PathCollection(label='first')
        pc.set_label('second')
        assert pc.get_label() == 'second'

    def test_label_numeric_coerced_to_string(self):
        """Numeric label is coerced to string."""
        pc = PathCollection(label=42)
        assert pc.get_label() == '42'

    def test_label_none_becomes_nolegend(self):
        """set_label(None) produces '_nolegend_'."""
        pc = PathCollection()
        pc.set_label(None)
        assert pc.get_label() == '_nolegend_'


# ===================================================================
# Artist integration (zorder, visible, alpha)
# ===================================================================

class TestArtistIntegration:
    def test_pathcollection_is_collection(self):
        """PathCollection is a subclass of Collection."""
        assert issubclass(PathCollection, Collection)

    def test_zorder_class_attribute(self):
        """PathCollection class inherits zorder=1 from Collection."""
        assert PathCollection.zorder == 1

    def test_visible_default(self):
        """PathCollection is visible by default."""
        pc = PathCollection()
        assert pc.get_visible() is True

    def test_set_visible_false(self):
        """PathCollection visibility can be toggled."""
        pc = PathCollection()
        pc.set_visible(False)
        assert pc.get_visible() is False

    def test_alpha_default(self):
        """PathCollection alpha is None by default."""
        pc = PathCollection()
        assert pc.get_alpha() is None

    def test_set_alpha(self):
        """PathCollection alpha can be set."""
        pc = PathCollection()
        pc.set_alpha(0.7)
        assert pc.get_alpha() == 0.7

    def test_set_zorder(self):
        """PathCollection zorder can be changed."""
        pc = PathCollection()
        pc.set_zorder(5)
        assert pc.get_zorder() == 5

    def test_figure_default_none(self):
        """PathCollection has no figure by default."""
        pc = PathCollection()
        assert pc.figure is None

    def test_axes_default_none(self):
        """PathCollection has no axes by default."""
        pc = PathCollection()
        assert pc.axes is None

    def test_kwargs_forwarded_to_artist(self):
        """Extra kwargs are forwarded through Collection to Artist.set()."""
        pc = PathCollection(visible=False, alpha=0.3)
        assert pc.get_visible() is False
        assert pc.get_alpha() == 0.3
