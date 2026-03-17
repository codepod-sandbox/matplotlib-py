"""
matplotlib._pil_backend — render a Figure to PNG bytes via PIL.
"""

import io
from matplotlib.colors import to_rgb as _to_rgb_float
from matplotlib.backend_bases import RendererBase


def _to_rgb_255(color):
    """Convert a colour to an (r, g, b) int tuple (0-255) for PIL."""
    r, g, b = _to_rgb_float(color)
    return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


class RendererPIL(RendererBase):
    """PIL/Pillow renderer that draws onto an RGB image."""

    def __init__(self, width, height, dpi):
        super().__init__(width, height, dpi)
        from PIL import Image, ImageDraw
        self._img = Image.new('RGB', (width, height), (255, 255, 255))
        self._draw = ImageDraw.Draw(self._img)

    def draw_line(self, xdata, ydata, color, linewidth, linestyle):
        col = _to_rgb_255(color)
        lw = max(1, int(linewidth))
        for i in range(len(xdata) - 1):
            self._draw.line(
                [(int(xdata[i]), int(ydata[i])),
                 (int(xdata[i + 1]), int(ydata[i + 1]))],
                fill=col, width=lw
            )

    def draw_markers(self, xdata, ydata, color, size):
        col = _to_rgb_255(color)
        r = max(1, int(size))
        for i in range(len(xdata)):
            cx, cy = int(xdata[i]), int(ydata[i])
            self._draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=col)

    def draw_rect(self, x, y, width, height, stroke, fill):
        fill_col = _to_rgb_255(fill) if fill else None
        outline_col = _to_rgb_255(stroke) if stroke else None
        self._draw.rectangle(
            [(int(x), int(y)), (int(x + width), int(y + height))],
            fill=fill_col, outline=outline_col
        )

    def draw_circle(self, cx, cy, r, color):
        col = _to_rgb_255(color)
        self._draw.ellipse(
            [(int(cx - r), int(cy - r)), (int(cx + r), int(cy + r))],
            fill=col
        )

    def draw_wedge(self, cx, cy, r, start_angle, end_angle, color):
        import math
        col = _to_rgb_255(color)
        sweep = end_angle - start_angle
        if sweep >= 360:
            self.draw_circle(cx, cy, r, color)
            return
        # Approximate wedge as a filled polygon: center + arc points + center
        # Use enough segments for a smooth arc
        n_segments = max(8, int(abs(sweep) / 3))
        pts = [(int(cx), int(cy))]
        for i in range(n_segments + 1):
            angle_deg = start_angle + sweep * i / n_segments
            angle_rad = math.radians(angle_deg)
            # Negate y because screen y-axis is down
            x = cx + r * math.cos(angle_rad)
            y = cy - r * math.sin(angle_rad)
            pts.append((int(x), int(y)))
        pts.append((int(cx), int(cy)))
        # Draw filled polygon using lines (PIL in RustPython lacks polygon())
        for i in range(len(pts) - 1):
            self._draw.line([pts[i], pts[i + 1]], fill=col, width=1)
        # Fill using a simple scanline approach: draw radial lines from center
        for i in range(1, len(pts) - 1):
            self._draw.line([(int(cx), int(cy)), pts[i]], fill=col, width=1)

    def draw_polygon(self, points, color, alpha):
        col = _to_rgb_255(color)
        pts = [(int(x), int(y)) for x, y in points]
        if len(pts) >= 3:
            # PIL in RustPython lacks polygon(); approximate with lines
            for i in range(len(pts)):
                p1 = pts[i]
                p2 = pts[(i + 1) % len(pts)]
                self._draw.line([p1, p2], fill=col, width=1)

    def draw_text(self, x, y, text, fontsize, color, ha):
        col = _to_rgb_255(color)
        self._draw.text((int(x), int(y)), str(text), fill=col)

    def draw_arrow(self, x1, y1, x2, y2, arrowstyle, color, linewidth):
        """Draw arrow: line + arrowhead polygon."""
        import math
        col = _to_rgb_255(color)
        lw = max(1, int(linewidth))

        # Draw the shaft
        self._draw.line([(int(x1), int(y1)), (int(x2), int(y2))],
                        fill=col, width=lw)

        has_end = arrowstyle in ('->', '<->', 'fancy')
        has_start = arrowstyle in ('<-', '<->')

        head_len = max(8, lw * 4)
        head_w = max(4, lw * 2)

        def _arrowhead(tx, ty, fx, fy):
            """Draw a filled triangle arrowhead at (tx,ty) pointing away from (fx,fy)."""
            dx = tx - fx
            dy = ty - fy
            length = math.hypot(dx, dy)
            if length < 1e-6:
                return
            ux, uy = dx / length, dy / length
            px, py = -uy, ux  # perpendicular
            tip = (int(tx), int(ty))
            base1 = (int(tx - ux * head_len + px * head_w),
                     int(ty - uy * head_len + py * head_w))
            base2 = (int(tx - ux * head_len - px * head_w),
                     int(ty - uy * head_len - py * head_w))
            self._draw.line([tip, base1], fill=col, width=lw)
            self._draw.line([tip, base2], fill=col, width=lw)
            self._draw.line([base1, base2], fill=col, width=lw)

        if has_end:
            _arrowhead(x2, y2, x1, y1)
        if has_start:
            _arrowhead(x1, y1, x2, y2)

    def set_clip_rect(self, x, y, width, height):
        # PIL doesn't support clipping natively; store for potential future use
        self._clip = (x, y, width, height)

    def clear_clip(self):
        self._clip = None

    def get_result(self):
        buf = io.BytesIO()
        self._img.save(buf, format='PNG')
        return buf.getvalue()


