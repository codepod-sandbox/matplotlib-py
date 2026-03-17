"""matplotlib.artist --- base class for all visual objects."""


class Artist:
    """Base class for objects that render into a Figure."""

    zorder = 0

    def __init__(self):
        self._visible = True
        self._alpha = None
        self._label = ''
        self._zorder = self.__class__.zorder
        self._clip_on = True
        self.figure = None
        self.axes = None
        self._stale = True

    def get_visible(self):
        return self._visible

    def set_visible(self, b):
        self._visible = b

    def get_clip_on(self):
        return self._clip_on

    def set_clip_on(self, b):
        self._clip_on = bool(b)

    def get_alpha(self):
        return self._alpha

    def set_alpha(self, alpha):
        self._alpha = alpha

    def get_label(self):
        return self._label

    def set_label(self, s):
        self._label = str(s) if s is not None else '_nolegend_'

    def get_zorder(self):
        return self._zorder

    def set_zorder(self, level):
        self._zorder = level

    def remove(self):
        """Remove this artist from its axes."""
        if self.axes is not None:
            self.axes._remove_artist(self)

    def set(self, **kwargs):
        """Batch property setter."""
        for k, v in kwargs.items():
            setter = getattr(self, f'set_{k}', None)
            if setter:
                setter(v)
