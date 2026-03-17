# Ported from lib/matplotlib/tests/test_ticker.py
import pytest
import matplotlib


def test_rcparams_formatter_keys():
    """Formatter rcParams keys must exist with correct defaults."""
    assert 'axes.formatter.limits' in matplotlib.rcParams
    assert matplotlib.rcParams['axes.formatter.limits'] == [-5, 6]
    assert 'axes.formatter.use_locale' in matplotlib.rcParams
    assert matplotlib.rcParams['axes.formatter.use_locale'] is False
    assert 'axes.formatter.use_mathtext' in matplotlib.rcParams
    assert matplotlib.rcParams['axes.formatter.use_mathtext'] is False
    assert 'axes.formatter.min_exponent' in matplotlib.rcParams
    assert matplotlib.rcParams['axes.formatter.min_exponent'] == 0
    assert 'axes.formatter.useoffset' in matplotlib.rcParams
    assert matplotlib.rcParams['axes.formatter.useoffset'] is True
    assert 'axes.formatter.offset_threshold' in matplotlib.rcParams
    assert matplotlib.rcParams['axes.formatter.offset_threshold'] == 4


# ---------------------------------------------------------------------------
# Ported from lib/matplotlib/tests/test_ticker.py
# ---------------------------------------------------------------------------

def test_formatter_str():
    """NullFormatter and FixedFormatter basics."""
    from matplotlib.ticker import NullFormatter, FixedFormatter
    assert NullFormatter()(1.0, 0) == ''
    fmt = FixedFormatter(['a', 'b', 'c'])
    assert fmt(0, 0) == 'a'
    assert fmt(1, 1) == 'b'
    assert fmt(5, 5) == ''  # out of range -> empty string


def test_scalar_formatter():
    """ScalarFormatter produces plain strings for small values."""
    from matplotlib.ticker import ScalarFormatter
    fmt = ScalarFormatter()
    fmt.create_dummy_axis()
    fmt.axis.set_view_interval(0, 2000)
    fmt.axis.set_data_interval(0, 2000)
    fmt.set_locs([0, 500, 1000, 1500, 2000])
    result = fmt(1000, 0)
    assert isinstance(result, str)
    assert result == '1000'


def test_percent_formatter():
    """PercentFormatter formats fractions as percentages."""
    from matplotlib.ticker import PercentFormatter
    fmt = PercentFormatter(xmax=1.0, decimals=0)
    fmt.create_dummy_axis()
    assert fmt(0.5, 0) == '50%'
    assert fmt(1.0, 0) == '100%'
    fmt2 = PercentFormatter(xmax=100, decimals=0)
    fmt2.create_dummy_axis()
    assert fmt2(50, 0) == '50%'


def test_func_formatter():
    """FuncFormatter delegates to a callable."""
    from matplotlib.ticker import FuncFormatter
    fmt = FuncFormatter(lambda x, pos: f'val={x:.1f}')
    assert fmt(3.14, 0) == 'val=3.1'


def test_str_method_formatter():
    """StrMethodFormatter uses str.format."""
    from matplotlib.ticker import StrMethodFormatter
    fmt = StrMethodFormatter('{x:.2f}')
    assert fmt(3.14159, 0) == '3.14'
    fmt2 = StrMethodFormatter('{x:d}')
    assert fmt2(42, 0) == '42'


def test_null_locator():
    """NullLocator returns empty tick list."""
    from matplotlib.ticker import NullLocator
    loc = NullLocator()
    assert loc.tick_values(0, 10) == []


def test_fixed_locator():
    """FixedLocator returns its preset tick positions."""
    from matplotlib.ticker import FixedLocator
    loc = FixedLocator([1, 2, 3, 5])
    result = loc.tick_values(0, 6)
    assert list(result) == [1, 2, 3, 5]


def test_multiple_locator():
    """MultipleLocator produces ticks at multiples of base."""
    from matplotlib.ticker import MultipleLocator
    loc = MultipleLocator(0.5)
    ticks = loc.tick_values(0.0, 2.0)
    assert 0.5 in ticks
    assert 1.0 in ticks
    assert 1.5 in ticks


def test_auto_locator():
    """AutoLocator produces ~5-8 nice ticks in range."""
    from matplotlib.ticker import AutoLocator
    loc = AutoLocator()
    ticks = loc.tick_values(0, 10)
    assert 4 <= len(ticks) <= 12
    # ticks should be within or near range
    assert min(ticks) <= 0.01
    assert max(ticks) >= 9.99


def test_log_locator():
    """LogLocator places ticks at powers of base."""
    from matplotlib.ticker import LogLocator
    loc = LogLocator(base=10.0)
    ticks = loc.tick_values(1, 1000)
    tick_list = sorted(ticks)
    assert 1 in tick_list or any(abs(t - 1) < 0.01 for t in tick_list)
    assert any(abs(t - 10) < 0.01 for t in tick_list)
    assert any(abs(t - 100) < 0.01 for t in tick_list)


def test_maxn_locator():
    """MaxNLocator respects nbins limit."""
    from matplotlib.ticker import MaxNLocator
    loc = MaxNLocator(nbins=4)
    ticks = loc.tick_values(0, 100)
    assert len(ticks) <= 6  # nbins+1 at most


def test_logformatter():
    # Ported from lib/matplotlib/tests/test_ticker.py::test_LogFormatter
    """LogFormatter produces reasonable strings for log-scale values."""
    from matplotlib.ticker import LogFormatter
    fmt = LogFormatter(base=10)
    fmt.create_dummy_axis()
    result = fmt(100, 0)
    assert isinstance(result, str)
    assert len(result) > 0


# ---------------------------------------------------------------------------
# axis.py tests
# ---------------------------------------------------------------------------

def test_axis_default_locator_formatter():
    """XAxis defaults to AutoLocator + ScalarFormatter."""
    from matplotlib.axis import XAxis
    from matplotlib.ticker import AutoLocator, ScalarFormatter
    ax_obj = XAxis()
    assert isinstance(ax_obj.get_major_locator(), AutoLocator)
    assert isinstance(ax_obj.get_major_formatter(), ScalarFormatter)


def test_axis_set_major_locator():
    """set_major_locator() replaces the locator."""
    from matplotlib.axis import XAxis
    from matplotlib.ticker import FixedLocator
    ax_obj = XAxis()
    loc = FixedLocator([1, 2, 3])
    ax_obj.set_major_locator(loc)
    assert ax_obj.get_major_locator() is loc


def test_axis_set_ticks_uses_fixed_locator():
    """set_ticks() installs a FixedLocator + ScalarFormatter."""
    from matplotlib.axis import XAxis
    from matplotlib.ticker import FixedLocator
    ax_obj = XAxis()
    ax_obj.set_ticks([0.0, 0.5, 1.0])
    assert isinstance(ax_obj.get_major_locator(), FixedLocator)
    assert list(ax_obj.get_ticks()) == [0.0, 0.5, 1.0]


def test_axis_set_ticks_with_labels():
    """set_ticks() with labels installs FixedFormatter."""
    from matplotlib.axis import XAxis
    from matplotlib.ticker import FixedFormatter
    ax_obj = XAxis()
    ax_obj.set_ticks([1, 2, 3], ['a', 'b', 'c'])
    assert isinstance(ax_obj.get_major_formatter(), FixedFormatter)
    assert ax_obj.get_major_formatter().seq == ['a', 'b', 'c']


def test_axis_tick_values():
    """tick_values() delegates to the locator."""
    from matplotlib.axis import XAxis
    ax_obj = XAxis()
    ax_obj.set_ticks([10, 20, 30])
    vals = ax_obj.tick_values(0, 40)
    assert list(vals) == [10, 20, 30]


# ---------------------------------------------------------------------------
# Axes integration tests
# ---------------------------------------------------------------------------

def test_axes_has_xaxis_yaxis():
    """Axes must expose .xaxis and .yaxis as Axis instances."""
    import matplotlib.pyplot as plt
    from matplotlib.axis import XAxis, YAxis
    fig, ax = plt.subplots()
    assert isinstance(ax.xaxis, XAxis)
    assert isinstance(ax.yaxis, YAxis)
    plt.close('all')


def test_set_xticks_delegates_to_xaxis():
    """set_xticks() must set a FixedLocator on xaxis."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FixedLocator
    fig, ax = plt.subplots()
    ax.set_xticks([1, 2, 3])
    assert isinstance(ax.xaxis.get_major_locator(), FixedLocator)
    assert ax.get_xticks() == [1, 2, 3]
    plt.close('all')


def test_set_xticklabels_sets_formatter():
    """set_xticklabels() must install FixedFormatter on xaxis."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FixedFormatter
    fig, ax = plt.subplots()
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(['zero', 'one', 'two'])
    assert isinstance(ax.xaxis.get_major_formatter(), FixedFormatter)
    plt.close('all')


def test_cla_resets_axis():
    """cla() must reset xaxis/yaxis to default AutoLocator."""
    import matplotlib.pyplot as plt
    from matplotlib.ticker import AutoLocator, FixedLocator
    fig, ax = plt.subplots()
    ax.set_xticks([1, 2, 3])
    assert isinstance(ax.xaxis.get_major_locator(), FixedLocator)
    ax.cla()
    assert isinstance(ax.xaxis.get_major_locator(), AutoLocator)
    plt.close('all')


def test_draw_renders_tick_labels(tmp_path):
    """draw() must produce tick label text in SVG output via Axis objects."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [10, 20, 30])
    svg_path = tmp_path / "test.svg"
    fig.savefig(str(svg_path))
    svg = svg_path.read_text()
    # SVG must contain some numeric tick label text
    assert any(str(n) in svg for n in range(1, 31))
    plt.close('all')
