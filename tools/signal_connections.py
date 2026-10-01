"""Own signal subscriptions to long-lived QGIS objects as a single group."""


class SignalConnections:
    def __init__(self):
        self._connections = []

    def connect(self, signal, slot):
        signal.connect(slot)
        self._connections.append((signal, slot))

    def disconnect_all(self):
        """Disconnect once; allow cleanup after QGIS has deleted a sender."""
        while self._connections:
            signal, slot = self._connections.pop()
            try:
                signal.disconnect(slot)
            except (TypeError, RuntimeError):
                # Qt also disconnects automatically when a sender is destroyed.
                pass
