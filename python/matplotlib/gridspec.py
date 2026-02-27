"""matplotlib.gridspec --- GridSpec for advanced subplot layouts."""


class SubplotSpec:
    """Specification for the location of a subplot in a GridSpec."""

    def __init__(self, gridspec, rowspan, colspan):
        self._gridspec = gridspec
        self.rowspan = rowspan  # (start, stop)
        self.colspan = colspan  # (start, stop)

    def get_gridspec(self):
        return self._gridspec


class GridSpec:
    """A grid layout to place subplots within a figure.

    Usage::

        gs = GridSpec(2, 3)
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[0, 1:3])
        ax3 = fig.add_subplot(gs[1, :])
    """

    def __init__(self, nrows, ncols, **kwargs):
        self.nrows = nrows
        self.ncols = ncols

    def __getitem__(self, key):
        """Return a SubplotSpec for the given grid position.

        Supports integer indexing and slicing:
            gs[0, 0]     -> single cell
            gs[0, :]     -> full row
            gs[:, 0]     -> full column
            gs[0:2, 0:2] -> block
        """
        if not isinstance(key, tuple) or len(key) != 2:
            raise IndexError("GridSpec index must be a 2-tuple (row, col)")

        row_key, col_key = key

        # Normalize row
        if isinstance(row_key, int):
            rowspan = (row_key, row_key + 1)
        elif isinstance(row_key, slice):
            start = row_key.start if row_key.start is not None else 0
            stop = row_key.stop if row_key.stop is not None else self.nrows
            rowspan = (start, stop)
        else:
            raise IndexError(f"Invalid row index: {row_key}")

        # Normalize col
        if isinstance(col_key, int):
            colspan = (col_key, col_key + 1)
        elif isinstance(col_key, slice):
            start = col_key.start if col_key.start is not None else 0
            stop = col_key.stop if col_key.stop is not None else self.ncols
            colspan = (start, stop)
        else:
            raise IndexError(f"Invalid col index: {col_key}")

        return SubplotSpec(self, rowspan, colspan)
