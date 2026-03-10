"""matplotlib.container --- Container classes for grouped artists."""


class Container(tuple):
    """Base container: a tuple of artists with label support."""

    def __new__(cls, artists, *args, **kwargs):
        return super().__new__(cls, artists)

    def __init__(self, artists, *args, **kwargs):
        # tuple is immutable so __new__ handles the data;
        # __init__ only stores the label.
        self._label = ''

    def get_label(self):
        return self._label

    def set_label(self, s):
        self._label = str(s) if s is not None else '_nolegend_'

    def remove(self):
        """Remove every artist in the container from its axes."""
        for artist in self:
            if hasattr(artist, 'remove'):
                artist.remove()


class BarContainer(Container):
    """Container for bar-chart rectangles and optional errorbars."""

    def __new__(cls, patches, errorbar=None, label=None):
        return super().__new__(cls, patches)

    def __init__(self, patches, errorbar=None, label=None):
        super().__init__(patches)
        self._patches = list(patches)
        self.errorbar = errorbar
        if label is not None:
            self.set_label(label)

    @property
    def patches(self):
        return self._patches

    def __iter__(self):
        return iter(self._patches)

    def __len__(self):
        return len(self._patches)

    def __getitem__(self, index):
        return self._patches[index]


class ErrorbarContainer(Container):
    """Container for errorbar artists (plot-line, cap-lines, bar-line-cols)."""

    def __new__(cls, lines, has_xerr=False, has_yerr=False, label=None):
        return super().__new__(cls, lines)

    def __init__(self, lines, has_xerr=False, has_yerr=False, label=None):
        super().__init__(lines)
        # lines is expected to be a 3-tuple: (plotline, caplines, barlinecols)
        self.lines = lines
        self._has_xerr = has_xerr
        self._has_yerr = has_yerr
        if label is not None:
            self.set_label(label)

    @property
    def has_xerr(self):
        return self._has_xerr

    @property
    def has_yerr(self):
        return self._has_yerr


class StemContainer(Container):
    """Container for stem plot artists (markerline, stemlines, baseline)."""

    def __new__(cls, markerline_stemlines_baseline, label=None):
        return super().__new__(cls, markerline_stemlines_baseline)

    def __init__(self, markerline_stemlines_baseline, label=None):
        super().__init__(markerline_stemlines_baseline)
        self.markerline = markerline_stemlines_baseline[0]
        self.stemlines = markerline_stemlines_baseline[1]
        self.baseline = markerline_stemlines_baseline[2]
        if label is not None:
            self.set_label(label)
