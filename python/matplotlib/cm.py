# Copyright (c) 2012- Matplotlib Development Team; All Rights Reserved
# Copyright (c) 2024 CodePod Contributors — BSD 3-Clause License
"""
matplotlib.cm — colormap registry, get_cmap(), and ScalarMappable.

Adapted from upstream matplotlib/cm.py (3.9.x).
"""

from matplotlib.colors import (
    Colormap, LinearSegmentedColormap, ListedColormap, Normalize,
)
import matplotlib._cm as _cm
import matplotlib._cm_listed as _cm_listed


class ColormapRegistry:
    """Dict-like registry of named Colormap objects.

    Pre-populated with all built-in colormaps at import time.
    Reversed (_r) variants are also included.
    """

    def __init__(self, cmaps):
        # cmaps: dict of name -> Colormap
        self._cmaps = dict(cmaps)

    def __getitem__(self, item):
        try:
            return self._cmaps[item]
        except KeyError:
            raise KeyError(f"Unknown colormap: {item!r}") from None

    def __iter__(self):
        return iter(self._cmaps)

    def __len__(self):
        return len(self._cmaps)

    def __contains__(self, item):
        return item in self._cmaps

    def register(self, cmap, *, name=None, force=False):
        """Register a colormap.

        Parameters
        ----------
        cmap : Colormap
        name : str, optional — defaults to cmap.name
        force : bool — if False, raises ValueError if name already exists
        """
        if name is None:
            name = cmap.name
        if not isinstance(cmap, Colormap):
            raise ValueError(f"register() requires a Colormap instance, got {type(cmap)}")
        if name in self._cmaps and not force:
            raise ValueError(
                f"A colormap named {name!r} is already registered. "
                "Use force=True to overwrite."
            )
        self._cmaps[name] = cmap

    def get_cmap(self, name=None, lut=None):
        """Look up a colormap by name (or return the default).

        Parameters
        ----------
        name : str, Colormap, or None
            None -> rcParams['image.cmap']; Colormap instance -> returned as-is.
        lut : int, optional
            If provided, resample the colormap to this many entries.

        Returns
        -------
        Colormap
        """
        if name is None:
            import matplotlib
            name = matplotlib.rcParams.get('image.cmap', 'viridis')

        if isinstance(name, Colormap):
            cmap = name
        elif isinstance(name, str):
            if name not in self._cmaps:
                raise ValueError(
                    f"Unknown colormap {name!r}. "
                    f"Use cm._colormaps to see available names."
                )
            cmap = self._cmaps[name]
        else:
            raise TypeError(f"get_cmap() expects str or Colormap, got {type(name)}")

        if lut is not None:
            import copy
            cmap = copy.copy(cmap)
            cmap.N = int(lut)
            if hasattr(cmap, '_lut'):
                del cmap._lut

        return cmap


def _compact_to_segmentdata(data):
    """Convert compact segment format [(x, (r,g,b)), ...] to segmentdata dict.

    Each point (x, (r, g, b)) maps to:
      red:   (x, r, r)
      green: (x, g, g)
      blue:  (x, b, b)
    """
    red   = [(pt[0], pt[1][0], pt[1][0]) for pt in data]
    green = [(pt[0], pt[1][1], pt[1][1]) for pt in data]
    blue  = [(pt[0], pt[1][2], pt[1][2]) for pt in data]
    return {'red': red, 'green': green, 'blue': blue}


def _build_registry():
    """Build the global colormap registry at import time."""
    cmaps = {}

    # 1. Colormaps from _cm.datad — multiple data formats:
    #   (a) dict with 'red'/'green'/'blue' keys -> LinearSegmentedColormap
    #   (b) dict with 'listed' key -> ListedColormap
    #   (c) tuple of (x, (r,g,b)) 2-tuples -> compact segment format -> LinearSegmentedColormap
    #   (d) tuple of (r,g,b) 3-tuples -> color list -> ListedColormap
    for name, data in _cm.datad.items():
        if isinstance(data, dict):
            if 'listed' in data:
                # Format (b): {'listed': [(r,g,b), ...]}
                cmap = ListedColormap(list(data['listed']), name=name)
            else:
                # Format (a): standard segmentdata dict
                cmap = LinearSegmentedColormap(name, data, N=256)
        elif isinstance(data, (tuple, list)) and len(data) > 0:
            first = data[0]
            if isinstance(first, (tuple, list)) and len(first) == 2 and isinstance(first[1], (tuple, list)):
                # Format (c): compact segment [(x, (r,g,b)), ...] -> convert to segmentdata
                segmentdata = _compact_to_segmentdata(data)
                cmap = LinearSegmentedColormap(name, segmentdata, N=256)
            else:
                # Format (d): color list [(r,g,b), ...]
                cmap = ListedColormap(list(data), name=name)
        else:
            continue
        cmaps[name] = cmap

    # 2. ListedColormaps from _cm_listed
    _listed_map = {
        'viridis':  '_viridis_data',
        'plasma':   '_plasma_data',
        'inferno':  '_inferno_data',
        'magma':    '_magma_data',
        'cividis':  '_cividis_data',
        'turbo':    '_turbo_data',
        'tab10':    '_tab10_data',
        'tab20':    '_tab20_data',
        'tab20b':   '_tab20b_data',
        'tab20c':   '_tab20c_data',
        'Set1':     '_Set1_data',
        'Set2':     '_Set2_data',
        'Set3':     '_Set3_data',
        'Paired':   '_Paired_data',
        'Accent':   '_Accent_data',
        'Dark2':    '_Dark2_data',
        'Pastel1':  '_Pastel1_data',
        'Pastel2':  '_Pastel2_data',
    }
    for cmap_name, attr in _listed_map.items():
        data = getattr(_cm_listed, attr, None)
        if data is not None:
            cmap = ListedColormap(data, name=cmap_name)
            cmaps[cmap_name] = cmap

    # 3. Add _r (reversed) variants for every registered colormap
    base_names = list(cmaps.keys())
    for name in base_names:
        r_name = name + '_r'
        if r_name not in cmaps:
            try:
                cmaps[r_name] = cmaps[name].reversed(name=r_name)
            except NotImplementedError:
                pass

    return ColormapRegistry(cmaps)


# Module-level registry — populated once at import time
_colormaps = _build_registry()


def get_cmap(name=None, lut=None):
    """Return a Colormap instance by name (or the default colormap).

    Parameters
    ----------
    name : str or Colormap or None
    lut : int, optional

    Returns
    -------
    Colormap
    """
    return _colormaps.get_cmap(name, lut)


class ScalarMappable:
    """Mixin for artists that map scalar data to colors.

    Adapted from upstream matplotlib/cm.py ScalarMappable.
    Event/callback infrastructure removed.
    """

    def __init__(self, norm=None, cmap=None):
        """
        Parameters
        ----------
        norm : Normalize or None
        cmap : str or Colormap or None — defaults to rcParams['image.cmap']
        """
        self._A = None
        self.set_cmap(cmap)
        self.set_norm(norm)

    def set_array(self, A):
        """Set the data array."""
        import numpy as np
        if A is not None:
            self._A = np.asarray(A, dtype=float)
        else:
            self._A = None

    def get_array(self):
        """Return the data array."""
        return self._A

    def set_cmap(self, cmap):
        """Set the colormap. Accepts name string or Colormap instance."""
        if cmap is None:
            import matplotlib
            cmap = matplotlib.rcParams.get('image.cmap', 'viridis')
        if isinstance(cmap, str):
            cmap = get_cmap(cmap)
        if not isinstance(cmap, Colormap):
            raise TypeError(f"cmap must be a Colormap or str, got {type(cmap)}")
        self._cmap = cmap

    def get_cmap(self):
        """Return the current Colormap."""
        return self._cmap

    def set_norm(self, norm):
        """Set the normalization. Accepts Normalize instance or None."""
        if norm is None:
            norm = Normalize()
        if not isinstance(norm, Normalize):
            raise TypeError(f"norm must be a Normalize instance or None, got {type(norm)}")
        self.norm = norm

    def get_norm(self):
        """Return the current Normalize instance."""
        return self.norm

    def get_clim(self):
        """Return (vmin, vmax)."""
        return self.norm.vmin, self.norm.vmax

    def set_clim(self, vmin=None, vmax=None):
        """Set vmin and vmax on the norm."""
        if vmin is not None:
            self.norm.vmin = float(vmin)
        if vmax is not None:
            self.norm.vmax = float(vmax)

    def autoscale(self):
        """Set vmin/vmax from the current data array."""
        import numpy as np
        if self._A is None:
            raise ValueError("autoscale() requires set_array() to be called first")
        flat = self._A.flatten().tolist()
        valid = [v for v in flat if not np.isnan(v)]
        if not valid:
            return
        self.norm.vmin = min(valid)
        self.norm.vmax = max(valid)

    def autoscale_None(self):
        """Set vmin/vmax only where not already set."""
        import numpy as np
        if self._A is None:
            return
        if self.norm.vmin is None or self.norm.vmax is None:
            flat = self._A.flatten().tolist()
            valid = [v for v in flat if not np.isnan(v)]
            if not valid:
                return
            if self.norm.vmin is None:
                self.norm.vmin = min(valid)
            if self.norm.vmax is None:
                self.norm.vmax = max(valid)

    def to_rgba(self, x, alpha=None, bytes=False, norm=True):
        """Map data array x to RGBA.

        Parameters
        ----------
        x : array-like
        alpha : float, optional
        bytes : bool
        norm : bool — if True, apply self.norm before mapping

        Returns
        -------
        ndarray of shape (*x.shape, 4), float64 or uint8
        """
        import numpy as np
        x = np.asarray(x, dtype=float)
        if norm:
            orig_shape = x.shape
            x_list = x.flatten().tolist()
            x_normed = self.norm(x_list)
            x = np.asarray(x_normed, dtype=float).reshape(orig_shape)
        return self._cmap(x, alpha=alpha, bytes=bytes)
