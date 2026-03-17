# Copyright (c) 2024 CodePod Contributors — BSD 3-Clause License
"""matplotlib.legend — simplified Legend artist."""

from matplotlib.colors import to_hex


_LOC_MAP = {
    0: 'best', 1: 'upper right', 2: 'upper left',
    3: 'lower left', 4: 'lower right', 5: 'right',
    6: 'center left', 7: 'center right',
    8: 'lower center', 9: 'upper center', 10: 'center',
}
_ROW_H = 20   # pixels per legend row
_PAD = 8      # padding inside box
_SWATCH_W = 22  # width of colour swatch
_MIN_W = 80   # minimum legend box width


class LegendText:
    """Minimal text-like proxy for a legend entry label."""
    def __init__(self, text):
        self._text = text

    def get_text(self):
        return self._text

    def set_text(self, s):
        self._text = s


class Legend:
    """Simplified matplotlib-compatible Legend."""

    def __init__(self, ax, handles, labels, *,
                 loc='best', ncol=1, ncols=None,
                 bbox_to_anchor=None, framealpha=0.8,
                 title=None, fontsize=None):
        self._ax = ax
        self._handles = list(handles)
        self._labels = list(labels)
        self._loc = _LOC_MAP.get(loc, loc) if isinstance(loc, int) else loc
        self._ncol = ncols if ncols is not None else ncol
        self._bbox_to_anchor = bbox_to_anchor
        self._framealpha = framealpha
        self._title_text = LegendText(title) if title else LegendText('')
        self._fontsize = fontsize or 11

        # Build LegendText list for get_texts() API
        self._texts = [LegendText(lbl) for lbl in labels]

    # --- API ---
    def get_texts(self):
        return self._texts

    def get_loc(self):
        return self._loc

    def get_ncol(self):
        return self._ncol

    def get_title(self):
        return self._title_text

    def get_handles(self):
        return list(self._handles)

    # --- Geometry ---
    def _box_size(self):
        """Compute (width, height) of the legend box in pixels."""
        n = len(self._labels)
        if n == 0:
            return (0, 0)
        title_h = _ROW_H if self._title_text.get_text() else 0
        nrows = -(-n // self._ncol)  # ceiling division
        h = title_h + nrows * _ROW_H + _PAD
        # estimate width: swatch + longest label text
        max_len = max((len(lbl) for lbl in self._labels), default=0)
        col_w = _SWATCH_W + max_len * 6 + _PAD  # ~6px per char
        w = max(_MIN_W, col_w * self._ncol + _PAD)
        return (w, h)

    def _box_origin(self, layout):
        """Compute (lx, ly) top-left of legend box using loc."""
        px, py = layout.plot_x, layout.plot_y
        pw, ph = layout.plot_w, layout.plot_h
        w, h = self._box_size()

        if self._bbox_to_anchor is not None:
            bta = self._bbox_to_anchor
            if len(bta) >= 2:
                return (px + bta[0] * pw - w, py + bta[1] * ph - h)

        margin = 5
        loc = self._loc if self._loc != 'best' else 'upper right'

        if loc in ('upper right', 'right'):
            return (px + pw - w - margin, py + margin)
        elif loc == 'upper left':
            return (px + margin, py + margin)
        elif loc == 'lower left':
            return (px + margin, py + ph - h - margin)
        elif loc == 'lower right':
            return (px + pw - w - margin, py + ph - h - margin)
        elif loc == 'upper center':
            return (px + pw / 2 - w / 2, py + margin)
        elif loc == 'lower center':
            return (px + pw / 2 - w / 2, py + ph - h - margin)
        elif loc == 'center left':
            return (px + margin, py + ph / 2 - h / 2)
        elif loc == 'center right':
            return (px + pw - w - margin, py + ph / 2 - h / 2)
        elif loc == 'center':
            return (px + pw / 2 - w / 2, py + ph / 2 - h / 2)
        return (px + pw - w - margin, py + margin)  # fallback upper right

    def draw(self, renderer, layout):
        """Draw legend onto renderer."""
        if not self._labels:
            return

        w, h = self._box_size()
        lx, ly = self._box_origin(layout)

        # Frame
        renderer.draw_rect(lx, ly, w, h, '#999999', '#ffffff')

        # Title
        row = 0
        title = self._title_text.get_text()
        if title:
            renderer.draw_text(
                lx + _PAD, ly + _PAD + row * _ROW_H + 13,
                title, self._fontsize + 1, '#000000', 'left',
            )
            row += 1

        # Entries (simple single-column for now; ncol support is additive)
        for i, (handle, label) in enumerate(
                zip(self._handles, self._labels)):
            col = i % self._ncol
            r = row + i // self._ncol
            ey = ly + _PAD + r * _ROW_H + _ROW_H // 2
            ex = lx + _PAD + col * (w // self._ncol)

            # Colour swatch (line or patch)
            color = '#555555'
            if hasattr(handle, 'get_color'):
                try:
                    color = to_hex(handle.get_color())
                except Exception:
                    pass
            elif hasattr(handle, 'get_facecolor'):
                try:
                    fc = handle.get_facecolor()
                    if len(fc) == 4:
                        color = to_hex(fc[:3])
                except Exception:
                    pass

            renderer.draw_line(
                [ex, ex + _SWATCH_W - 4], [ey, ey],
                color, 2.0, '-', opacity=1.0,
            )
            renderer.draw_text(
                ex + _SWATCH_W, ey + 4,
                self._texts[i].get_text(),
                self._fontsize, '#333333', 'left',
            )
