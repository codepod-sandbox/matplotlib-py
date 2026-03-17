# Copyright (c) 2024 CodePod Contributors
# BSD 3-Clause License (see LICENSE at repository root)
"""matplotlib.axis — XAxis and YAxis wrappers."""

from matplotlib.ticker import (
    AutoLocator, ScalarFormatter,
    FixedLocator, FixedFormatter,
    NullLocator, NullFormatter,
)


class _TickerPair:
    """Holds a (locator, formatter) pair for major or minor ticks."""

    def __init__(self, locator, formatter):
        self.locator = locator
        self.formatter = formatter


class Axis:
    """Base class for a single axis (x or y)."""

    def __init__(self):
        self._major = _TickerPair(AutoLocator(), ScalarFormatter())
        self._minor = _TickerPair(NullLocator(), NullFormatter())
        self._ticks = None   # None means "use locator"; list means "fixed"

    # --- major ---
    def get_major_locator(self):
        return self._major.locator

    def set_major_locator(self, locator):
        self._major.locator = locator
        self._ticks = None  # clear fixed ticks

    def get_major_formatter(self):
        return self._major.formatter

    def set_major_formatter(self, formatter):
        self._major.formatter = formatter

    # --- minor ---
    def get_minor_locator(self):
        return self._minor.locator

    def set_minor_locator(self, locator):
        self._minor.locator = locator

    def get_minor_formatter(self):
        return self._minor.formatter

    def set_minor_formatter(self, formatter):
        self._minor.formatter = formatter

    # --- explicit ticks ---
    def set_ticks(self, ticks, labels=None):
        """Set explicit tick positions (and optionally labels)."""
        ticks = list(ticks)
        self._ticks = ticks
        self._major.locator = FixedLocator(ticks)
        if labels is not None:
            self._major.formatter = FixedFormatter(list(labels))
        else:
            self._major.formatter = ScalarFormatter()

    def get_ticks(self):
        """Return the fixed tick list, or [] if using auto locator."""
        return list(self._ticks) if self._ticks is not None else []

    def tick_values(self, vmin, vmax):
        """Ask the locator for tick positions in [vmin, vmax]."""
        return self._major.locator.tick_values(vmin, vmax)

    def format_ticks(self, values):
        """Format a sequence of tick values using the major formatter."""
        fmt = self._major.formatter
        # ScalarFormatter (and some others) need set_locs + a view interval
        # to choose the right number of significant digits.
        if hasattr(fmt, 'set_locs'):
            if fmt.axis is None:
                fmt.create_dummy_axis()
            vals_list = list(values)
            if vals_list:
                vmin, vmax = min(vals_list), max(vals_list)
                fmt.axis.set_view_interval(vmin, vmax)
                fmt.axis.set_data_interval(vmin, vmax)
            fmt.set_locs(vals_list)
        return [fmt(v, i) for i, v in enumerate(values)]


class XAxis(Axis):
    """X-axis."""


class YAxis(Axis):
    """Y-axis."""
