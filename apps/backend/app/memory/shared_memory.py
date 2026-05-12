class SharedMemory:

    def __init__(self):

        self.events = []

    # ============================================
    # ADD EVENT
    # ============================================

    def add_event(self, text: str):

        self.events.append(text)

        # ограничиваем память

        if len(self.events) > 200:

            self.events = self.events[-200:]

    # ============================================
    # GET EVENTS
    # ============================================

    def get_recent_events(
        self,
        limit: int = 20
    ):

        return self.events[-limit:]


shared_memory = SharedMemory()