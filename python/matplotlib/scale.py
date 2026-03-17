# Copyright (c) 2024 CodePod Contributors
# BSD 3-Clause License (see LICENSE at repository root)
"""matplotlib.scale — axis scale objects (LinearScale, LogScale, SymmetricalLogScale, FuncScale)."""

import math as _math

import numpy as np
import numpy.ma as ma


class ScaleBase:
    """Abstract base for axis scales."""

    def forward(self, values):
        """Transform data values to display space."""
        raise NotImplementedError

    def inverse(self, values):
        """Transform display space back to data values."""
        raise NotImplementedError


class LinearScale(ScaleBase):
    def forward(self, values):
        return np.asarray(values, dtype=float)

    def inverse(self, values):
        return np.asarray(values, dtype=float)


class LogScale(ScaleBase):
    def __init__(self, base=10.0, nonpositive='mask'):
        self.base = float(base)
        self._nonpositive = nonpositive

    def forward(self, values):
        arr = np.asarray(values, dtype=float)
        if self._nonpositive == 'mask':
            arr = ma.masked_where(arr <= 0, arr)
            return ma.log(arr) / _math.log(self.base)
        else:
            with np.errstate(divide='ignore', invalid='ignore'):
                return np.log(arr) / _math.log(self.base)

    def inverse(self, values):
        return self.base ** np.asarray(values, dtype=float)


class SymmetricalLogScale(ScaleBase):
    def __init__(self, base=10.0, linthresh=2.0, linscale=1.0):
        self.base = float(base)
        self.linthresh = float(linthresh)
        self.linscale = float(linscale)

    def _symlog(self, x):
        log_base = _math.log(self.base)
        sign = np.sign(x)
        abs_x = np.abs(x)
        inside = abs_x <= self.linthresh
        result = np.where(
            inside,
            x / self.linthresh * self.linscale,
            sign * (self.linscale + (np.log(abs_x / self.linthresh) / log_base)),
        )
        return result

    def _isymlog(self, y):
        sign = np.sign(y)
        abs_y = np.abs(y)
        inside = abs_y <= self.linscale
        result = np.where(
            inside,
            y * self.linthresh / self.linscale,
            sign * self.linthresh * (self.base ** (abs_y - self.linscale)),
        )
        return result

    def forward(self, values):
        return self._symlog(np.asarray(values, dtype=float))

    def inverse(self, values):
        return self._isymlog(np.asarray(values, dtype=float))


class FuncScale(ScaleBase):
    def __init__(self, forward, inverse):
        self._forward = forward
        self._inverse = inverse

    def forward(self, values):
        return self._forward(np.asarray(values, dtype=float))

    def inverse(self, values):
        return self._inverse(np.asarray(values, dtype=float))
