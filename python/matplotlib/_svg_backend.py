"""
matplotlib._svg_backend — render a Figure to an SVG string.
"""

from matplotlib.colors import to_hex, to_rgb
from matplotlib.backend_bases import RendererBase


class RendererSVG(RendererBase):
    """SVG renderer that accumulates SVG fragments in a list."""

    def __init__(self, width, height, dpi):
        super().__init__(width, height, dpi)
        self._parts = []
        self._clip_id = None
        self._clip_counter = 0

    def draw_line(self, xdata, ydata, color, linewidth, linestyle, opacity=1.0):
        dash = _svg_dash(linestyle)
        points = ' '.join(
            f'{xdata[i]:.2f},{ydata[i]:.2f}' for i in range(len(xdata))
        )
        clip = self._clip_attr()
        opacity_attr = f' opacity="{opacity}"' if opacity < 1.0 else ''
        self._parts.append(
            f'<polyline points="{points}" fill="none" '
            f'stroke="{color}" stroke-width="{linewidth}"{dash}{opacity_attr}{clip}/>'
        )

    def draw_markers(self, xdata, ydata, color, size):
        clip = self._clip_attr()
        for i in range(len(xdata)):
            self._parts.append(
                f'<circle cx="{xdata[i]:.2f}" cy="{ydata[i]:.2f}" '
                f'r="{size}" fill="{color}"{clip}/>'
            )

    def draw_rect(self, x, y, width, height, stroke, fill):
        fill_attr = fill if fill else "none"
        stroke_attr = stroke if stroke else "none"
        clip = self._clip_attr()
        self._parts.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
            f'fill="{fill_attr}" stroke="{stroke_attr}"{clip}/>'
        )

    def draw_circle(self, cx, cy, r, color):
        clip = self._clip_attr()
        self._parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"{clip}/>'
        )

    def draw_wedge(self, cx, cy, r, start_angle, end_angle, color):
        import math
        sweep = end_angle - start_angle
        clip = self._clip_attr()
        if sweep >= 360:
            # Full circle
            self._parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"{clip}/>'
            )
            return
        # SVG y-axis is down, so negate angles
        svg_start = -start_angle
        svg_end = -end_angle
        x1 = cx + r * math.cos(math.radians(svg_start))
        y1 = cy + r * math.sin(math.radians(svg_start))
        x2 = cx + r * math.cos(math.radians(svg_end))
        y2 = cy + r * math.sin(math.radians(svg_end))
        large_arc = 1 if sweep > 180 else 0
        sweep_flag = 1  # CW in SVG screen coords = CCW in math coords
        d = (
            f'M {cx:.2f},{cy:.2f} '
            f'L {x1:.2f},{y1:.2f} '
            f'A {r},{r} 0 {large_arc},{sweep_flag} {x2:.2f},{y2:.2f} Z'
        )
        self._parts.append(
            f'<path d="{d}" fill="{color}"{clip}/>'
        )

    def draw_polygon(self, points, color, alpha):
        pts = ' '.join(f'{x},{y}' for x, y in points)
        clip = self._clip_attr()
        self._parts.append(
            f'<polygon points="{pts}" fill="{color}" '
            f'fill-opacity="{alpha}" stroke="none"{clip}/>'
        )

    def draw_text(self, x, y, text, fontsize, color, ha):
        anchor_map = {"left": "start", "center": "middle", "right": "end"}
        anchor = anchor_map.get(ha, "start")
        clip = self._clip_attr()
        self._parts.append(
            f'<text x="{x}" y="{y}" font-size="{fontsize}" '
            f'fill="{color}" text-anchor="{anchor}"{clip}>'
            f'{_esc(text)}</text>'
        )

    def draw_arrow(self, x1, y1, x2, y2, arrowstyle, color, linewidth):
        """Draw an arrow using SVG path with marker-end for arrowhead."""
        arrow_id = f'arrow-{len(self._parts)}'
        has_end = arrowstyle in ('->', '<->', 'fancy')
        has_start = arrowstyle in ('<-', '<->')

        if has_end or has_start:
            # Define a simple triangle arrowhead marker
            marker = (
                f'<defs>'
                f'<marker id="{arrow_id}-end" markerWidth="8" markerHeight="6" '
                f'refX="7" refY="3" orient="auto">'
                f'<polygon points="0 0, 8 3, 0 6" fill="{color}"/>'
                f'</marker>'
            )
            if has_start:
                marker += (
                    f'<marker id="{arrow_id}-start" markerWidth="8" markerHeight="6" '
                    f'refX="1" refY="3" orient="auto-start-reverse">'
                    f'<polygon points="0 0, 8 3, 0 6" fill="{color}"/>'
                    f'</marker>'
                )
            marker += '</defs>'
            self._parts.append(marker)

        attrs = f'stroke="{color}" stroke-width="{linewidth}" fill="none"'
        if has_end:
            attrs += f' marker-end="url(#{arrow_id}-end)"'
        if has_start:
            attrs += f' marker-start="url(#{arrow_id}-start)"'

        self._parts.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" {attrs}/>'
        )

    def set_clip_rect(self, x, y, width, height):
        self._clip_counter += 1
        self._clip_id = f'clip-{self._clip_counter}'
        self._parts.append(
            f'<defs><clipPath id="{self._clip_id}">'
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}"/>'
            f'</clipPath></defs>'
        )

    def clear_clip(self):
        self._clip_id = None

    def get_result(self):
        header = (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{self.width}" height="{self.height}" '
            f'viewBox="0 0 {self.width} {self.height}">'
        )
        return '\n'.join([header] + self._parts + ['</svg>'])

    def _clip_attr(self):
        if self._clip_id:
            return f' clip-path="url(#{self._clip_id})"'
        return ''


# Named style → (on, off, ...) dash sequences
_NAMED_DASHES = {
    'solid': None,
    '-': None,
    'dashed': (6, 3),
    '--': (6, 3),
    'dotted': (2, 2),
    ':': (2, 2),
    'dashdot': (6, 2, 2, 2),
    '-.': (6, 2, 2, 2),
    'loosely dashed': (6, 6),
    'densely dashed': (4, 1),
    'loosely dotted': (2, 4),
    'densely dotted': (1, 1),
    'loosely dashdotted': (6, 4, 2, 4),
    'densely dashdotted': (4, 1, 2, 1),
}


def _svg_dash(ls):
    """Return SVG stroke-dasharray attribute string for a linestyle."""
    if isinstance(ls, tuple):
        # (offset, (on, off, ...)) format
        offset, dashes = ls
        dash_str = ','.join(str(d) for d in dashes)
        return f' stroke-dasharray="{dash_str}"'

    seq = _NAMED_DASHES.get(ls)
    if seq is None:
        return ''  # solid or unknown → no dasharray
    dash_str = ','.join(str(d) for d in seq)
    return f' stroke-dasharray="{dash_str}"'


def _nice_ticks(lo, hi, target_count):
    """Generate roughly *target_count* nicely-rounded ticks between lo and hi."""
    if hi <= lo:
        return [lo]
    import math
    raw_step = (hi - lo) / max(target_count, 1)
    mag = 10 ** math.floor(math.log10(raw_step + 1e-15))
    residual = raw_step / mag
    if residual <= 1.5:
        step = 1 * mag
    elif residual <= 3:
        step = 2 * mag
    elif residual <= 7:
        step = 5 * mag
    else:
        step = 10 * mag

    start = math.floor(lo / step) * step
    ticks = []
    t = start
    while t <= hi + step * 0.01:
        if lo <= t <= hi:
            ticks.append(round(t, 10))
        t += step
    return ticks if ticks else [lo, hi]


def _fmt_tick(v):
    """Format a tick value nicely."""
    if v == int(v):
        return str(int(v))
    return f'{v:.2g}'


def _esc(s):
    """Escape HTML entities."""
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
