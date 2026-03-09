"""
matplotlib.pyplot — stateful module-level plotting API.
"""

import matplotlib
from matplotlib.figure import Figure

# ------------------------------------------------------------------
# Re-exports
# ------------------------------------------------------------------
rcParams = matplotlib.rcParams
rc_context = matplotlib.rc_context

# ------------------------------------------------------------------
# Global state: figure management
# ------------------------------------------------------------------
_figures = {}        # num -> Figure
_fig_order = []      # creation-order list of figure numbers
_next_num = 1        # auto-incrementing figure number
_current_fig = None
_current_ax = None


def _ensure():
    """Ensure there is a current Figure and Axes."""
    global _current_fig, _current_ax
    if _current_fig is None:
        fig, ax = subplots()
    return _current_fig, _current_ax


# ------------------------------------------------------------------
# Figure management
# ------------------------------------------------------------------

def figure(num=None, figsize=None, dpi=100, clear=False, **kwargs):
    """Create a new Figure, or activate an existing one by number/label.

    Parameters
    ----------
    num : int or str or Figure or None
        If None, a new figure is created with the next auto-number.
        If int, activate existing figure with that number or create one.
        If str, treated as a label — find existing or create new.
        If Figure instance, activate it if tracked, else raise ValueError.
    figsize : (float, float), optional
    dpi : int
    clear : bool
        If True, clear the figure after getting/creating it.
    """
    global _current_fig, _current_ax, _next_num

    # Accept a Figure instance
    if isinstance(num, Figure):
        for n, f in _figures.items():
            if f is num:
                _current_fig = f
                _current_ax = f._axes[-1] if f._axes else None
                if clear:
                    f.clear()
                return f
        raise ValueError(
            "The passed figure is not managed by this pyplot instance"
        )

    # Save original num to detect string labels
    label_arg = num if isinstance(num, str) else None

    # Resolve the figure number
    if num is None:
        num = _next_num

    if isinstance(num, str):
        # Search by label
        label = num
        for n, fig in _figures.items():
            if fig.get_label() == label:
                num = n
                break
        else:
            # Not found — create with next number
            num = _next_num

    if num in _figures:
        # Activate existing figure
        fig = _figures[num]
        _current_fig = fig
        _current_ax = fig._axes[-1] if fig._axes else None
        if clear:
            fig.clear()
        return fig

    # Create a new figure
    fig = Figure(figsize=figsize, dpi=dpi)
    fig.number = num
    # If the original num argument was a string label, set it
    # (we captured it above before overwriting num)
    if isinstance(label_arg, str):
        fig.set_label(label_arg)
    _figures[num] = fig
    _fig_order.append(num)
    if isinstance(num, int) and num >= _next_num:
        _next_num = num + 1

    _current_fig = fig
    _current_ax = None
    return fig


def get_fignums():
    """Return a sorted list of existing figure numbers."""
    return sorted(_figures.keys())


def get_figlabels():
    """Return a list of existing figure labels sorted by figure number."""
    return [_figures[n].get_label() for n in sorted(_figures.keys())]


def fignum_exists(num):
    """Return whether figure number *num* exists.

    Also accepts string labels.
    """
    if isinstance(num, str):
        for fig in _figures.values():
            if fig.get_label() == num:
                return True
        return False
    return num in _figures


def close(fig=None):
    """Close figure(s).

    Parameters
    ----------
    fig : None, 'all', int, str, or Figure
        - None: close the current figure
        - ``'all'``: close all figures
        - int: close figure with that number
        - str: close figure with that label
        - Figure instance: close that figure
    """
    global _current_fig, _current_ax, _next_num

    if fig is None:
        # Close current figure
        if _current_fig is None:
            return
        fig = _current_fig

    if isinstance(fig, str) and fig == 'all':
        _figures.clear()
        _fig_order.clear()
        _current_fig = None
        _current_ax = None
        _next_num = 1
        return

    if isinstance(fig, str):
        # Search by label
        num = None
        for n, f in _figures.items():
            if f.get_label() == fig:
                num = n
                break
        if num is None:
            return  # Not found
    elif isinstance(fig, int):
        num = fig
    elif isinstance(fig, Figure):
        # Find the number for this figure
        num = None
        for n, f in _figures.items():
            if f is fig:
                num = n
                break
        if num is None:
            return  # Not tracked
    elif isinstance(fig, float):
        raise TypeError("close() does not accept float figure numbers")
    else:
        raise TypeError(
            f"close() argument must be 'all', an int, or a Figure, "
            f"not {type(fig).__name__}"
        )

    if num in _figures:
        del _figures[num]
        if num in _fig_order:
            _fig_order.remove(num)

    # Update current figure
    if _current_fig is not None and _current_fig.number == num:
        if _fig_order:
            last_num = _fig_order[-1]
            _current_fig = _figures[last_num]
            _current_ax = (_current_fig._axes[-1]
                           if _current_fig._axes else None)
        else:
            _current_fig = None
            _current_ax = None


# ------------------------------------------------------------------
# Axes management
# ------------------------------------------------------------------

def gcf():
    """Get current figure, creating one if needed."""
    _ensure()
    return _current_fig


def gca():
    """Get current axes, creating one if needed."""
    global _current_ax
    _ensure()
    _current_ax = _current_fig.gca()
    return _current_ax


def sca(ax):
    """Set the current axes to *ax*, and the current figure to its parent."""
    global _current_fig, _current_ax
    _current_ax = ax
    _current_fig = ax.figure
    # Also update the figure's axes stack
    _current_fig.sca(ax)


def subplot(*args, **kwargs):
    """Add a subplot to the current figure, with reuse semantics.

    If a subplot with the same grid position already exists, it is
    returned instead of creating a new one.

    Usage: ``subplot(nrows, ncols, index)`` or ``subplot(NCI)`` where
    NCI is a 3-digit integer.
    """
    global _current_ax
    _ensure()

    if len(args) == 1 and isinstance(args[0], int) and args[0] >= 100:
        # 3-digit form: subplot(211) -> (2, 1, 1)
        n = args[0]
        nrows, ncols, index = n // 100, (n % 100) // 10, n % 10
    elif len(args) == 3:
        nrows, ncols, index = args
    elif len(args) == 0:
        nrows, ncols, index = 1, 1, 1
    else:
        nrows, ncols, index = 1, 1, 1

    pos = (nrows, ncols, index)

    # Reuse: check if an axes with the same grid position exists
    for ax in _current_fig._axes:
        if ax._position == pos:
            _current_ax = ax
            return ax

    # Create new subplot
    ax = _current_fig.add_subplot(nrows, ncols, index)
    _current_ax = ax
    return ax


def axes(**kwargs):
    """Add a new axes to the current figure (never reuses existing axes)."""
    global _current_ax
    _ensure()
    rect = kwargs.pop('rect', None)
    ax = _current_fig.add_axes(rect, **kwargs)
    _current_ax = ax
    return ax


def subplots(nrows=1, ncols=1, figsize=None, dpi=100, **kwargs):
    """Create a Figure and a set of subplots."""
    global _current_fig, _current_ax, _next_num

    sharex = kwargs.pop('sharex', False)
    sharey = kwargs.pop('sharey', False)
    num = kwargs.pop('num', None)
    clear = kwargs.pop('clear', False)

    # If num is given, try to reuse existing figure
    if num is not None:
        fig = figure(num=num, figsize=figsize, dpi=dpi, clear=clear)
    else:
        fig = Figure(figsize=figsize, dpi=dpi)
        num = _next_num
        fig.number = num
        _figures[num] = fig
        _fig_order.append(num)
        _next_num = num + 1
    _current_fig = fig

    if nrows == 1 and ncols == 1:
        ax = fig.add_subplot(1, 1, 1)
        _current_ax = ax
        return fig, ax

    all_axes = []
    axes_list = []
    for r in range(nrows):
        row = []
        for c in range(ncols):
            ax = fig.add_subplot(nrows, ncols, r * ncols + c + 1)
            row.append(ax)
            all_axes.append(ax)
        axes_list.append(row)

    # Link shared axes
    if sharex and len(all_axes) > 1:
        for ax in all_axes:
            ax._shared_x = all_axes
    if sharey and len(all_axes) > 1:
        for ax in all_axes:
            ax._shared_y = all_axes

    _current_ax = axes_list[0][0] if axes_list else None

    if nrows == 1:
        axes_list = axes_list[0]
    elif ncols == 1:
        axes_list = [row[0] for row in axes_list]

    return fig, axes_list


def cla():
    """Clear the current axes."""
    _ensure()
    _current_ax.cla()


def clf():
    """Clear the current figure."""
    global _current_ax
    _ensure()
    _current_fig.clear()
    _current_ax = None


# ------------------------------------------------------------------
# Interactive mode
# ------------------------------------------------------------------

class _InteractiveContext:
    """Context manager for interactive mode toggling.

    Works both as a plain call and as a context manager::

        plt.ioff()           # sets interactive=False immediately
        with plt.ioff():     # restores state on exit
            ...

    The key subtlety: ``ioff()``/``ion()`` set the state immediately
    *and* return this context.  When used as ``with plt.ioff():``,
    Python calls ``ioff()`` first (setting state and saving old),
    then ``__enter__`` (which must *not* overwrite the saved state).
    ``__exit__`` restores the state that was saved by ``ioff()``/``ion()``.
    """

    def __init__(self, old_state):
        self._old = old_state

    def __enter__(self):
        # State was already set by ion()/ioff(); nothing to do.
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        matplotlib._interactive = self._old
        return False


def ion():
    """Enable interactive mode.

    Also returns a context manager that restores the previous state.
    """
    old = matplotlib._interactive
    matplotlib._interactive = True
    return _InteractiveContext(old)


def ioff():
    """Disable interactive mode.

    Also returns a context manager that restores the previous state.
    """
    old = matplotlib._interactive
    matplotlib._interactive = False
    return _InteractiveContext(old)


def isinteractive():
    """Return whether interactive mode is enabled."""
    return matplotlib.is_interactive()


# ------------------------------------------------------------------
# Plotting functions — delegate to current axes
# ------------------------------------------------------------------

def plot(*args, **kwargs):
    _ensure()
    return _current_ax.plot(*args, **kwargs)


def scatter(x, y, s=None, c=None, **kwargs):
    _ensure()
    kw = dict(kwargs)
    if s is not None:
        kw['s'] = s
    if c is not None:
        kw['c'] = c
    return _current_ax.scatter(x, y, **kw)


def bar(x, height, width=0.8, **kwargs):
    _ensure()
    return _current_ax.bar(x, height, width, **kwargs)


def barh(y, width, height=0.8, **kwargs):
    """Horizontal bar chart — delegates to current axes."""
    _ensure()
    return _current_ax.barh(y, width, height, **kwargs)


def hist(x, bins=10, **kwargs):
    _ensure()
    return _current_ax.hist(x, bins, **kwargs)


def errorbar(x, y, yerr=None, xerr=None, **kwargs):
    """Error-bar plot — delegates to current axes."""
    _ensure()
    return _current_ax.errorbar(x, y, yerr=yerr, xerr=xerr, **kwargs)


def fill_between(x, y1, y2=0, **kwargs):
    """Fill area between two curves — delegates to current axes."""
    _ensure()
    return _current_ax.fill_between(x, y1, y2, **kwargs)


def axhline(y=0, **kwargs):
    """Add a horizontal line — delegates to current axes."""
    _ensure()
    return _current_ax.axhline(y, **kwargs)


def axvline(x=0, **kwargs):
    """Add a vertical line — delegates to current axes."""
    _ensure()
    return _current_ax.axvline(x, **kwargs)


def text(x, y, s, **kwargs):
    """Add text to the current axes."""
    _ensure()
    return _current_ax.text(x, y, s, **kwargs)


# ------------------------------------------------------------------
# Labels / config
# ------------------------------------------------------------------

def xlabel(s):
    _ensure()
    _current_ax.set_xlabel(s)


def ylabel(s):
    _ensure()
    _current_ax.set_ylabel(s)


def title(s):
    _ensure()
    _current_ax.set_title(s)


def suptitle(t, **kwargs):
    """Set a suptitle on the current figure."""
    _ensure()
    return _current_fig.suptitle(t, **kwargs)


def xlim(*args, **kwargs):
    """Get or set the x-axis limits.

    - ``xlim()`` returns current limits.
    - ``xlim(left, right)`` sets limits.
    - ``xlim(left=v)`` / ``xlim(right=v)`` sets one side.
    """
    _ensure()
    if not args and not kwargs:
        return _current_ax.get_xlim()
    if args:
        if len(args) == 1 and hasattr(args[0], '__iter__'):
            left, right = args[0]
        elif len(args) == 2:
            left, right = args
        else:
            left, right = args[0], None
    else:
        left = kwargs.get('left')
        right = kwargs.get('right')
    _current_ax.set_xlim(left, right)


def ylim(*args, **kwargs):
    """Get or set the y-axis limits.

    - ``ylim()`` returns current limits.
    - ``ylim(bottom, top)`` sets limits.
    """
    _ensure()
    if not args and not kwargs:
        return _current_ax.get_ylim()
    if args:
        if len(args) == 1 and hasattr(args[0], '__iter__'):
            bottom, top = args[0]
        elif len(args) == 2:
            bottom, top = args
        else:
            bottom, top = args[0], None
    else:
        bottom = kwargs.get('bottom')
        top = kwargs.get('top')
    _current_ax.set_ylim(bottom, top)


def xticks(*args, **kwargs):
    """Get or set the x-axis tick locations and labels.

    - ``xticks()`` returns current tick locations.
    - ``xticks(ticks)`` sets tick locations.
    - ``xticks(ticks, labels)`` sets locations and labels.
    """
    _ensure()
    if not args and not kwargs:
        return _current_ax.get_xticks()
    ticks = args[0] if args else kwargs.get('ticks')
    labels = args[1] if len(args) > 1 else kwargs.get('labels')
    if ticks is not None:
        _current_ax.set_xticks(ticks, labels=labels, **kwargs)


def yticks(*args, **kwargs):
    """Get or set the y-axis tick locations and labels.

    - ``yticks()`` returns current tick locations.
    - ``yticks(ticks)`` sets tick locations.
    - ``yticks(ticks, labels)`` sets locations and labels.
    """
    _ensure()
    if not args and not kwargs:
        return _current_ax.get_yticks()
    ticks = args[0] if args else kwargs.get('ticks')
    labels = args[1] if len(args) > 1 else kwargs.get('labels')
    if ticks is not None:
        _current_ax.set_yticks(ticks, labels=labels, **kwargs)


def legend(**kwargs):
    _ensure()
    _current_ax.legend(**kwargs)


def grid(visible=True, **kwargs):
    _ensure()
    _current_ax.grid(visible, **kwargs)


# ------------------------------------------------------------------
# Output
# ------------------------------------------------------------------

def savefig(fname, format=None, dpi=None):
    _ensure()
    _current_fig.savefig(fname, format=format, dpi=dpi)


def show():
    """No-op in sandbox environment."""
    pass
