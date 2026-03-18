"""
matplotlib.rcsetup — default parameters and RcParams dict subclass.
"""

from contextlib import contextmanager

# Default parameter values mirroring real matplotlib defaults.
_default_params = {
    # Axes
    'axes.prop_cycle': [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    ],
    'axes.facecolor': 'white',
    'axes.edgecolor': 'black',
    'axes.linewidth': 0.8,
    'axes.grid': False,
    'axes.grid.which': 'major',
    'axes.titlesize': 'large',
    'axes.titlepad': 6.0,
    'axes.titlelocation': 'center',
    'axes.labelsize': 'medium',
    'axes.labelpad': 4.0,

    # Formatter behavior
    'axes.formatter.limits': [-5, 6],
    'axes.formatter.use_locale': False,
    'axes.formatter.use_mathtext': False,
    'axes.formatter.min_exponent': 0,
    'axes.formatter.useoffset': True,
    'axes.formatter.offset_threshold': 4,
    'axes.unicode_minus': True,
    'axes.autolimit_mode': 'data',

    # Figure
    'figure.figsize': [6.4, 4.8],
    'figure.dpi': 100,
    'figure.facecolor': 'white',
    'figure.edgecolor': 'white',
    'figure.max_open_warning': 20,

    # Lines
    'lines.linewidth': 1.5,
    'lines.linestyle': '-',
    'lines.color': 'C0',
    'lines.marker': 'None',
    'lines.markersize': 6,

    # Patch
    'patch.linewidth': 1.0,
    'patch.facecolor': 'C0',
    'patch.edgecolor': 'black',

    # Legend
    'legend.loc': 'best',
    'legend.frameon': True,
    'legend.fontsize': 'medium',

    # Grid
    'grid.color': '#b0b0b0',
    'grid.linestyle': '-',
    'grid.linewidth': 0.8,
    'grid.alpha': 1.0,

    # Ticks
    'xtick.labelsize': 'medium',
    'ytick.labelsize': 'medium',

    # Text
    'text.antialiased': True,
    'text.usetex': False,

    # Saving
    'savefig.dpi': 'figure',
    'savefig.format': 'png',

    # Image / colormap
    'image.cmap': 'viridis',
    'image.lut': 256,
}


class RcParams(dict):
    """A dictionary subclass for storing matplotlib configuration parameters.

    Behaves like a regular dict but can be extended with validation
    in the future.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __repr__(self):
        lines = [f"RcParams({{"]
        for k in sorted(self):
            lines.append(f"    {k!r}: {self[k]!r},")
        lines.append("})")
        return '\n'.join(lines)

    def __str__(self):
        return self.__repr__()

    def find_all(self, pattern):
        """Return a dict of entries whose keys contain *pattern*."""
        import re
        regex = re.compile(pattern)
        return {k: v for k, v in self.items() if regex.search(k)}

    def copy(self):
        """Return a copy of this RcParams."""
        return RcParams(super().copy())


class _RcContext:
    """Context manager that temporarily overrides rcParams."""

    def __init__(self, rc_params_obj, overrides=None):
        self._rc = rc_params_obj
        self._overrides = overrides or {}
        self._saved = {}

    def __enter__(self):
        # Save current values for keys we will override
        for k in self._overrides:
            if k in self._rc:
                self._saved[k] = self._rc[k]
            else:
                self._saved[k] = _sentinel
        # Apply overrides
        self._rc.update(self._overrides)
        return self._rc

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original values
        for k, v in self._saved.items():
            if v is _sentinel:
                self._rc.pop(k, None)
            else:
                self._rc[k] = v
        return False


# Sentinel for keys that did not exist before context entry
_sentinel = object()


@contextmanager
def rc_context(rc=None):
    """Context manager for temporarily changing rcParams.

    Parameters
    ----------
    rc : dict, optional
        Mapping of rcParams keys to values to set within the context.

    Example
    -------
    >>> import matplotlib
    >>> with matplotlib.rc_context({'lines.linewidth': 3.0}):
    ...     print(matplotlib.rcParams['lines.linewidth'])
    3.0
    """
    # Import here to avoid circular imports at module level
    import matplotlib
    ctx = _RcContext(matplotlib.rcParams, rc)
    ctx.__enter__()
    try:
        yield
    finally:
        ctx.__exit__(None, None, None)
