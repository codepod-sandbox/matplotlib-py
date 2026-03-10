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

    def draw_line(self, xdata, ydata, color, linewidth, linestyle):
        dash = _svg_dash(linestyle)
        points = ' '.join(
            f'{xdata[i]:.2f},{ydata[i]:.2f}' for i in range(len(xdata))
        )
        clip = self._clip_attr()
        self._parts.append(
            f'<polyline points="{points}" fill="none" '
            f'stroke="{color}" stroke-width="{linewidth}"{dash}{clip}/>'
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


def render_figure_svg(fig):
    """Return an SVG string for *fig*."""
    dpi = fig.dpi
    fw, fh = fig.figsize
    svg_w = int(fw * dpi)
    svg_h = int(fh * dpi)

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{svg_w}" height="{svg_h}" '
        f'viewBox="0 0 {svg_w} {svg_h}">'
    )
    # White background
    parts.append(f'<rect width="{svg_w}" height="{svg_h}" fill="white"/>')

    for ax in fig._axes:
        _render_axes(parts, ax, svg_w, svg_h)

    parts.append('</svg>')
    return '\n'.join(parts)


def _render_axes(parts, ax, svg_w, svg_h):
    """Render one Axes into the SVG parts list."""
    # Margins
    ml, mr, mt, mb = 70, 20, 40, 50

    plot_x = ml
    plot_y = mt
    plot_w = svg_w - ml - mr
    plot_h = svg_h - mt - mb

    if plot_w <= 0 or plot_h <= 0:
        return

    # Gather data ranges
    xmin, xmax, ymin, ymax = _data_range(ax)

    # Apply axis limits if set
    if ax._xlim:
        if ax._xlim[0] is not None:
            xmin = ax._xlim[0]
        if ax._xlim[1] is not None:
            xmax = ax._xlim[1]
    if ax._ylim:
        if ax._ylim[0] is not None:
            ymin = ax._ylim[0]
        if ax._ylim[1] is not None:
            ymax = ax._ylim[1]

    # Add padding
    dx = (xmax - xmin) or 1.0
    dy = (ymax - ymin) or 1.0
    xmin -= dx * 0.05
    xmax += dx * 0.05
    ymin -= dy * 0.05
    ymax += dy * 0.05

    # Coordinate mappers
    def sx(v):
        return plot_x + (v - xmin) / (xmax - xmin) * plot_w

    def sy(v):
        return plot_y + plot_h - (v - ymin) / (ymax - ymin) * plot_h

    # Plot area border
    parts.append(
        f'<rect x="{plot_x}" y="{plot_y}" width="{plot_w}" height="{plot_h}" '
        f'fill="none" stroke="#000" stroke-width="1"/>'
    )

    # Grid
    if ax._grid:
        xticks = _nice_ticks(xmin, xmax, 8)
        yticks = _nice_ticks(ymin, ymax, 6)
        for t in xticks:
            tx = sx(t)
            if plot_x < tx < plot_x + plot_w:
                parts.append(
                    f'<line x1="{tx:.1f}" y1="{plot_y}" '
                    f'x2="{tx:.1f}" y2="{plot_y + plot_h}" '
                    f'stroke="#ddd" stroke-width="0.5" stroke-dasharray="4,4"/>'
                )
        for t in yticks:
            ty = sy(t)
            if plot_y < ty < plot_y + plot_h:
                parts.append(
                    f'<line x1="{plot_x}" y1="{ty:.1f}" '
                    f'x2="{plot_x + plot_w}" y2="{ty:.1f}" '
                    f'stroke="#ddd" stroke-width="0.5" stroke-dasharray="4,4"/>'
                )

    # Tick marks and labels
    xticks = _nice_ticks(xmin, xmax, 8)
    yticks = _nice_ticks(ymin, ymax, 6)
    for t in xticks:
        tx = sx(t)
        if plot_x <= tx <= plot_x + plot_w:
            parts.append(
                f'<line x1="{tx:.1f}" y1="{plot_y + plot_h}" '
                f'x2="{tx:.1f}" y2="{plot_y + plot_h + 5}" stroke="#000" stroke-width="1"/>'
            )
            parts.append(
                f'<text x="{tx:.1f}" y="{plot_y + plot_h + 18}" '
                f'text-anchor="middle" font-size="11" fill="#333">'
                f'{_fmt_tick(t)}</text>'
            )
    for t in yticks:
        ty = sy(t)
        if plot_y <= ty <= plot_y + plot_h:
            parts.append(
                f'<line x1="{plot_x - 5}" y1="{ty:.1f}" '
                f'x2="{plot_x}" y2="{ty:.1f}" stroke="#000" stroke-width="1"/>'
            )
            parts.append(
                f'<text x="{plot_x - 8}" y="{ty + 4:.1f}" '
                f'text-anchor="end" font-size="11" fill="#333">'
                f'{_fmt_tick(t)}</text>'
            )

    # Clipping rect for data elements
    clip_id = f'clip-{id(ax)}'
    parts.append(f'<defs><clipPath id="{clip_id}">')
    parts.append(
        f'<rect x="{plot_x}" y="{plot_y}" width="{plot_w}" height="{plot_h}"/>'
    )
    parts.append('</clipPath></defs>')

    # Data elements
    for elem in ax._elements:
        etype = elem.get('type', '')
        if etype == 'line':
            _draw_line(parts, elem, sx, sy)
        elif etype == 'scatter':
            _draw_scatter(parts, elem, sx, sy)
        elif etype == 'bar':
            _draw_bar(parts, elem, sx, sy, plot_y, plot_h, ymin, ymax)
        elif etype == 'barh':
            _draw_barh(parts, elem, sx, sy, plot_x, plot_w, xmin, xmax)
        elif etype == 'errorbar':
            _draw_errorbar(parts, elem, sx, sy)
        elif etype == 'fill_between':
            _draw_fill_between(parts, elem, sx, sy, clip_id)
        elif etype == 'fill_betweenx':
            _draw_fill_betweenx(parts, elem, sx, sy, clip_id)
        elif etype == 'axhline':
            _draw_axhline(parts, elem, sx, sy, plot_x, plot_w)
        elif etype == 'axvline':
            _draw_axvline(parts, elem, sx, sy, plot_y, plot_h)
        elif etype == 'text':
            _draw_text(parts, elem, sx, sy)
        # Unknown types are silently ignored

    # Title
    if ax._title:
        parts.append(
            f'<text x="{plot_x + plot_w / 2:.1f}" y="{plot_y - 10}" '
            f'text-anchor="middle" font-size="14" font-weight="bold" fill="#000">'
            f'{_esc(ax._title)}</text>'
        )

    # Axis labels
    if ax._xlabel:
        parts.append(
            f'<text x="{plot_x + plot_w / 2:.1f}" y="{svg_h - 5}" '
            f'text-anchor="middle" font-size="12" fill="#333">'
            f'{_esc(ax._xlabel)}</text>'
        )
    if ax._ylabel:
        ty = plot_y + plot_h / 2
        parts.append(
            f'<text x="15" y="{ty:.1f}" '
            f'text-anchor="middle" font-size="12" fill="#333" '
            f'transform="rotate(-90, 15, {ty:.1f})">'
            f'{_esc(ax._ylabel)}</text>'
        )

    # Legend
    if ax._legend:
        _draw_legend(parts, ax, plot_x + plot_w - 10, plot_y + 10)


# ------------------------------------------------------------------
# Element renderers
# ------------------------------------------------------------------

def _draw_line(parts, elem, sx, sy):
    xd, yd = elem['x'], elem['y']
    if not xd:
        return
    color = elem['color']
    lw = elem.get('linewidth', 1.5)
    ls = elem.get('linestyle', '-')
    dash = ''
    if ls == '--' or ls == 'dashed':
        dash = ' stroke-dasharray="6,3"'
    elif ls == ':' or ls == 'dotted':
        dash = ' stroke-dasharray="2,2"'
    elif ls == '-.' or ls == 'dashdot':
        dash = ' stroke-dasharray="6,2,2,2"'

    points = ' '.join(f'{sx(xd[i]):.2f},{sy(yd[i]):.2f}' for i in range(len(xd)))
    parts.append(
        f'<polyline points="{points}" fill="none" '
        f'stroke="{color}" stroke-width="{lw}"{dash}/>'
    )

    marker = elem.get('marker')
    if marker:
        for i in range(len(xd)):
            cx, cy = sx(xd[i]), sy(yd[i])
            parts.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="3" fill="{color}"/>')


def _draw_scatter(parts, elem, sx, sy):
    xd, yd = elem['x'], elem['y']
    color = elem['color']
    s = elem.get('s', 20)
    import math
    r = max(1, int(math.sqrt(s) / 2))
    for i in range(len(xd)):
        cx, cy = sx(xd[i]), sy(yd[i])
        parts.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r}" fill="{color}"/>')


def _draw_bar(parts, elem, sx, sy, plot_y, plot_h, ymin, ymax):
    xd = elem['x']
    heights = elem['height']
    width = elem['width']
    color = elem['color']

    for i in range(len(xd)):
        x_center = xd[i]
        h = heights[i]
        # Bar from y=0 (or ymin) to y=h
        base_val = max(0, ymin)
        x_left = sx(x_center - width / 2)
        x_right = sx(x_center + width / 2)
        y_top = sy(h)
        y_bottom = sy(base_val)
        bw = max(1, x_right - x_left)
        bh = max(0, y_bottom - y_top)
        parts.append(
            f'<rect x="{x_left:.2f}" y="{y_top:.2f}" '
            f'width="{bw:.2f}" height="{bh:.2f}" fill="{color}"/>'
        )


def _draw_barh(parts, elem, sx, sy, plot_x, plot_w, xmin, xmax):
    """Draw horizontal bars."""
    y_vals = elem['y']
    widths = elem['width']
    height = elem.get('height', 0.8)
    color = elem['color']

    for i in range(len(y_vals)):
        y_center = y_vals[i]
        w = widths[i]
        base_val = max(0, xmin)
        y_top = sy(y_center + height / 2)
        y_bottom = sy(y_center - height / 2)
        x_left = sx(base_val)
        x_right = sx(w)
        bw = max(0, x_right - x_left)
        bh = max(1, y_bottom - y_top)
        parts.append(
            f'<rect x="{x_left:.2f}" y="{y_top:.2f}" '
            f'width="{bw:.2f}" height="{bh:.2f}" fill="{color}"/>'
        )


def _draw_errorbar(parts, elem, sx, sy):
    """Draw error bars (data line + error whiskers)."""
    xd, yd = elem['x'], elem['y']
    color = elem['color']
    yerr = elem.get('yerr')
    xerr = elem.get('xerr')

    # Draw data line
    if len(xd) >= 2:
        points = ' '.join(f'{sx(xd[i]):.2f},{sy(yd[i]):.2f}' for i in range(len(xd)))
        parts.append(
            f'<polyline points="{points}" fill="none" '
            f'stroke="{color}" stroke-width="1.5"/>'
        )

    # Draw markers
    for i in range(len(xd)):
        cx, cy = sx(xd[i]), sy(yd[i])
        parts.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="3" fill="{color}"/>')

    # Draw y error bars
    if yerr:
        for i in range(len(xd)):
            err = yerr[i] if i < len(yerr) else yerr[-1]
            cx = sx(xd[i])
            y_lo = sy(yd[i] - err)
            y_hi = sy(yd[i] + err)
            # Vertical whisker
            parts.append(
                f'<line x1="{cx:.2f}" y1="{y_lo:.2f}" '
                f'x2="{cx:.2f}" y2="{y_hi:.2f}" '
                f'stroke="{color}" stroke-width="1"/>'
            )
            # Caps
            cap = 3
            parts.append(
                f'<line x1="{cx - cap:.2f}" y1="{y_lo:.2f}" '
                f'x2="{cx + cap:.2f}" y2="{y_lo:.2f}" '
                f'stroke="{color}" stroke-width="1"/>'
            )
            parts.append(
                f'<line x1="{cx - cap:.2f}" y1="{y_hi:.2f}" '
                f'x2="{cx + cap:.2f}" y2="{y_hi:.2f}" '
                f'stroke="{color}" stroke-width="1"/>'
            )

    # Draw x error bars
    if xerr:
        for i in range(len(xd)):
            err = xerr[i] if i < len(xerr) else xerr[-1]
            cy = sy(yd[i])
            x_lo = sx(xd[i] - err)
            x_hi = sx(xd[i] + err)
            parts.append(
                f'<line x1="{x_lo:.2f}" y1="{cy:.2f}" '
                f'x2="{x_hi:.2f}" y2="{cy:.2f}" '
                f'stroke="{color}" stroke-width="1"/>'
            )
            cap = 3
            parts.append(
                f'<line x1="{x_lo:.2f}" y1="{cy - cap:.2f}" '
                f'x2="{x_lo:.2f}" y2="{cy + cap:.2f}" '
                f'stroke="{color}" stroke-width="1"/>'
            )
            parts.append(
                f'<line x1="{x_hi:.2f}" y1="{cy - cap:.2f}" '
                f'x2="{x_hi:.2f}" y2="{cy + cap:.2f}" '
                f'stroke="{color}" stroke-width="1"/>'
            )


def _draw_fill_between(parts, elem, sx, sy, clip_id):
    """Draw a filled region between y1 and y2."""
    xd = elem['x']
    y1 = elem['y1']
    y2 = elem['y2']
    color = elem['color']
    alpha = elem.get('alpha', 0.5)

    if not xd:
        return

    # Build polygon: forward along y1, then backward along y2
    points_fwd = [f'{sx(xd[i]):.2f},{sy(y1[i]):.2f}' for i in range(len(xd))]
    points_bwd = [f'{sx(xd[i]):.2f},{sy(y2[i]):.2f}' for i in range(len(xd) - 1, -1, -1)]
    all_points = ' '.join(points_fwd + points_bwd)

    parts.append(
        f'<polygon points="{all_points}" fill="{color}" '
        f'fill-opacity="{alpha}" stroke="none" clip-path="url(#{clip_id})"/>'
    )


def _draw_fill_betweenx(parts, elem, sx, sy, clip_id):
    """Draw a filled region between x1 and x2 (horizontal)."""
    yd = elem['y']
    x1 = elem['x1']
    x2 = elem['x2']
    color = elem['color']
    alpha = elem.get('alpha', 0.5)

    if not yd:
        return

    points_fwd = [f'{sx(x1[i]):.2f},{sy(yd[i]):.2f}' for i in range(len(yd))]
    points_bwd = [f'{sx(x2[i]):.2f},{sy(yd[i]):.2f}' for i in range(len(yd) - 1, -1, -1)]
    all_points = ' '.join(points_fwd + points_bwd)

    parts.append(
        f'<polygon points="{all_points}" fill="{color}" '
        f'fill-opacity="{alpha}" stroke="none" clip-path="url(#{clip_id})"/>'
    )


def _draw_axhline(parts, elem, sx, sy, plot_x, plot_w):
    """Draw a horizontal line spanning the plot area."""
    y_vals = elem.get('y', [])
    if not y_vals:
        return
    y = y_vals[0]
    color = elem['color']
    lw = elem.get('linewidth', 1.0)
    ls = elem.get('linestyle', '-')
    dash = _svg_dash(ls)

    py = sy(y)
    parts.append(
        f'<line x1="{plot_x:.2f}" y1="{py:.2f}" '
        f'x2="{plot_x + plot_w:.2f}" y2="{py:.2f}" '
        f'stroke="{color}" stroke-width="{lw}"{dash}/>'
    )


def _draw_axvline(parts, elem, sx, sy, plot_y, plot_h):
    """Draw a vertical line spanning the plot area."""
    x_vals = elem.get('x', [])
    if not x_vals:
        return
    x = x_vals[0]
    color = elem['color']
    lw = elem.get('linewidth', 1.0)
    ls = elem.get('linestyle', '-')
    dash = _svg_dash(ls)

    px = sx(x)
    parts.append(
        f'<line x1="{px:.2f}" y1="{plot_y:.2f}" '
        f'x2="{px:.2f}" y2="{plot_y + plot_h:.2f}" '
        f'stroke="{color}" stroke-width="{lw}"{dash}/>'
    )


def _draw_text(parts, elem, sx, sy):
    """Draw text at a data position."""
    x_vals = elem.get('x', [])
    y_vals = elem.get('y', [])
    if not x_vals or not y_vals:
        return
    px = sx(x_vals[0])
    py = sy(y_vals[0])
    text = elem.get('s', '')
    fontsize = elem.get('fontsize', 11)
    color = elem.get('color', '#000')
    parts.append(
        f'<text x="{px:.2f}" y="{py:.2f}" '
        f'font-size="{fontsize}" fill="{color}">'
        f'{_esc(text)}</text>'
    )


def _svg_dash(ls):
    """Return SVG stroke-dasharray attribute string for a linestyle."""
    if ls == '--' or ls == 'dashed':
        return ' stroke-dasharray="6,3"'
    elif ls == ':' or ls == 'dotted':
        return ' stroke-dasharray="2,2"'
    elif ls == '-.' or ls == 'dashdot':
        return ' stroke-dasharray="6,2,2,2"'
    return ''


def _draw_legend(parts, ax, right_x, top_y):
    """Draw a legend box in the top-right corner."""
    items = [(e.get('color', '#000'), e.get('label')) for e in ax._elements if e.get('label')]
    if not items:
        return
    lw = 120
    lh = len(items) * 20 + 10
    lx = right_x - lw
    ly = top_y
    parts.append(
        f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" '
        f'fill="white" stroke="#999" stroke-width="0.5"/>'
    )
    for i, (color, label) in enumerate(items):
        iy = ly + 15 + i * 20
        parts.append(
            f'<line x1="{lx + 5}" y1="{iy}" x2="{lx + 25}" y2="{iy}" '
            f'stroke="{color}" stroke-width="2"/>'
        )
        parts.append(
            f'<text x="{lx + 30}" y="{iy + 4}" font-size="11" fill="#333">'
            f'{_esc(label or "")}</text>'
        )


# ------------------------------------------------------------------
# Axis helpers
# ------------------------------------------------------------------

def _data_range(ax):
    """Compute min/max across all elements."""
    xs, ys = [], []
    for e in ax._elements:
        etype = e.get('type', '')

        if etype == 'bar':
            xs.extend(e.get('x', []))
            ys.extend(e.get('height', []))
            ys.append(0)  # bars start from 0
        elif etype == 'barh':
            ys.extend(e.get('y', []))
            xs.extend(e.get('width', []))
            xs.append(0)  # horizontal bars start from 0
        elif etype == 'fill_between':
            xs.extend(e.get('x', []))
            ys.extend(e.get('y1', []))
            ys.extend(e.get('y2', []))
        elif etype == 'fill_betweenx':
            ys.extend(e.get('y', []))
            xs.extend(e.get('x1', []))
            xs.extend(e.get('x2', []))
        elif etype == 'errorbar':
            x_vals = e.get('x', [])
            y_vals = e.get('y', [])
            xs.extend(x_vals)
            ys.extend(y_vals)
            # Expand range by error bars
            yerr = e.get('yerr')
            if yerr:
                for i, yv in enumerate(y_vals):
                    err = yerr[i] if i < len(yerr) else yerr[-1]
                    ys.append(yv + err)
                    ys.append(yv - err)
            xerr = e.get('xerr')
            if xerr:
                for i, xv in enumerate(x_vals):
                    err = xerr[i] if i < len(xerr) else xerr[-1]
                    xs.append(xv + err)
                    xs.append(xv - err)
        elif etype == 'axhline':
            # Only contributes to y range
            ys.extend(e.get('y', []))
        elif etype == 'axvline':
            # Only contributes to x range
            xs.extend(e.get('x', []))
        elif etype in ('text', 'annotate'):
            # Text/annotate positions are ignored for data range calculation
            pass
        else:
            # Generic fallback: line, scatter, etc.
            xs.extend(e.get('x', []))
            ys.extend(e.get('y', []))

    if not xs:
        xs = [0, 1]
    if not ys:
        ys = [0, 1]
    return min(xs), max(xs), min(ys), max(ys)


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
