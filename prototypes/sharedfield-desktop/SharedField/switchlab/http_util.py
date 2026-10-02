"""Bounded handling of rejected POST bodies before closing a loopback socket."""
class RejectBodyMixin:
    def _reject(self,status,data):
        # urllib may send headers and body separately. Closing with unread body
        # can reset the connection on Windows before the client receives 403.
        previous=self.connection.gettimeout()
        try:
            length=int(self.headers.get('Content-Length','0'))
            if 0<length<=256000:
                self.connection.settimeout(1)
                self.rfile.read(length)
        except (ValueError,OSError):
            pass
        finally:
            self.connection.settimeout(previous)
        self.close_connection=True
        return self._send(status,data)
