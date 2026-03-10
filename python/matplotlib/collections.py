"""matplotlib.collections --- Collection and PathCollection artists."""

from matplotlib.artist import Artist
from matplotlib.colors import to_hex, to_rgba


class Collection(Artist):
    """Base class for collections of similar artists."""

    zorder = 1

    def __init__(self, **kwargs):
        super().__init__()
        if kwargs:
            self.set(**kwargs)


class PathCollection(Collection):
    """A collection of paths with offsets, used by scatter()."""

    def __init__(self, offsets=None, sizes=None, facecolors=None,
                 edgecolors=None, label=None, **kwargs):
        super().__init__(**kwargs)

        self._offsets = list(offsets) if offsets is not None else []
        self._sizes = list(sizes) if sizes is not None else [20.0]
        self._facecolors = list(facecolors) if facecolors is not None else []
        self._edgecolors = list(edgecolors) if edgecolors is not None else []

        if label is not None:
            self.set_label(label)

    # --- offsets ---
    def get_offsets(self):
        return list(self._offsets)

    def set_offsets(self, offsets):
        self._offsets = list(offsets)

    # --- sizes ---
    def get_sizes(self):
        return list(self._sizes)

    def set_sizes(self, sizes):
        self._sizes = list(sizes)

    # --- facecolors ---
    def get_facecolors(self):
        return list(self._facecolors)

    def set_facecolors(self, colors):
        self._facecolors = list(colors)

    # --- edgecolors ---
    def get_edgecolors(self):
        return list(self._edgecolors)

    def set_edgecolors(self, colors):
        self._edgecolors = list(colors)

    # --- draw (new renderer architecture) ---
    def draw(self, renderer, layout):
        if not self.get_visible():
            return
        if not self._offsets:
            return
        import math
        color = to_hex(self._facecolors[0]) if self._facecolors else to_hex('C0')
        s = self._sizes[0] if self._sizes else 20.0
        r = max(1.0, math.sqrt(s) / 2)
        for pt in self._offsets:
            cx = layout.sx(pt[0])
            cy = layout.sy(pt[1])
            renderer.draw_circle(cx, cy, r, color)

    # --- backend-compatible dict ---
    def _as_element(self):
        """Return a dict compatible with the existing backend renderers."""
        # Determine a single representative colour for the backend
        if self._facecolors:
            fc = self._facecolors[0]
            color_hex = to_hex(fc)
        else:
            color_hex = to_hex('C0')

        xs = [pt[0] for pt in self._offsets]
        ys = [pt[1] for pt in self._offsets]
        s = self._sizes[0] if self._sizes else 20.0

        return {
            'type': 'scatter',
            'x': xs,
            'y': ys,
            's': s,
            'color': color_hex,
            'label': self.get_label() or None,
        }
