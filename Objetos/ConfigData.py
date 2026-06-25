class ConfigData:
    def __init__(
        self,
        binWidth=None,
        binHeight=None,
        itemWidth=None,
        itemHeight=None
    ):
        self._binWidth = None
        self._binHeight = None
        self._itemWidth = None
        self._itemHeight = None

        if binWidth is not None:
            self.setBinWidth(binWidth)
        if binHeight is not None:
            self.setBinHeight(binHeight)
        if itemWidth is not None:
            self.setItemWidth(itemWidth)
        if itemHeight is not None:
            self.setItemHeight(itemHeight)

    # ---------- BIN WIDTH ----------
    def getBinWidth(self):
        return self._binWidth

    def setBinWidth(self, value):
        if value <= 0:
            raise ValueError("binWidth debe ser mayor que 0")
        self._binWidth = value

    # ---------- BIN HEIGHT ----------
    def getBinHeight(self):
        return self._binHeight

    def setBinHeight(self, value):
        if value <= 0:
            raise ValueError("binHeight debe ser mayor que 0")
        self._binHeight = value

    # ---------- ITEM WIDTH ----------
    def getItemWidth(self):
        return self._itemWidth

    def setItemWidth(self, value):
        if value <= 0:
            raise ValueError("itemWidth debe ser mayor que 0")
        self._itemWidth = value

    # ---------- ITEM HEIGHT ----------
    def getItemHeight(self):
        return self._itemHeight

    def setItemHeight(self, value):
        if value <= 0:
            raise ValueError("itemHeight debe ser mayor que 0")
        self._itemHeight = value

    # ---------- UTIL ----------
    def isComplete(self):
        return all([
            self._binWidth is not None,
            self._binHeight is not None,
            self._itemWidth is not None,
            self._itemHeight is not None
        ])

    def __str__(self):
        return (
            f"ConfigData("
            f"binWidth={self._binWidth}, "
            f"binHeight={self._binHeight}, "
            f"itemWidth={self._itemWidth}, "
            f"itemHeight={self._itemHeight})"
        )
