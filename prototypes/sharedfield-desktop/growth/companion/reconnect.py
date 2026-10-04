"""Bounded reconnect timing; a successful connection never replays a task."""


class ReconnectSchedule:
    def __init__(self):
        self.attempts = 0
        self.next_at = None

    def due(self, now, *, exited, deadline):
        if not exited:
            self.next_at = None
            return False
        if self.attempts >= 3 or now >= deadline:
            return False
        if self.next_at is None:
            self.next_at = now + (2, 10, 30)[self.attempts]
        if now < self.next_at:
            return False
        self.attempts += 1
        self.next_at = None
        return True
