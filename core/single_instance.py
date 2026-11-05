from __future__ import annotations

import json
import os
from typing import Callable, List, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


_USER = os.environ.get("USERNAME") or os.environ.get("USER") or "default"
SERVER_NAME = f"rizpaq_single_instance_{_USER}"


class SingleInstance(QObject):


    command_received = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._server = None


        self._pending: List[list] = []


        self._receiver: Optional[Callable[[list], None]] = None


    def try_send_to_existing(self, args: list) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(SERVER_NAME)
        if not socket.waitForConnected(500):
            return False

        try:
            payload = json.dumps(list(args), ensure_ascii=False).encode("utf-8")
        except Exception:
            try:
                socket.disconnectFromServer()
            except Exception:
                pass
            return False

        ok = False
        try:
            written = socket.write(payload)
            if written == len(payload):


                if socket.waitForBytesWritten(1000):

                    if socket.bytesWritten() >= len(payload):
                        ok = True
        except Exception:
            ok = False
        finally:
            try:
                socket.disconnectFromServer()
            except Exception:
                pass

        return ok


    def connect_command_receiver(self, receiver: Callable[[list], None]) -> None:
        self._receiver = receiver


        pending = list(self._pending)
        self._pending.clear()
        for args in pending:
            self._call_receiver(args)

    def _call_receiver(self, args: list) -> None:
        receiver = self._receiver
        if receiver is None:
            return
        try:
            receiver(list(args))
        except Exception:
            pass

    def _deliver(self, args: list) -> None:
        if self._receiver is not None:
            self._call_receiver(args)
            return


        self._pending.append(list(args))


        try:
            self.command_received.emit(list(args))
        except Exception:
            pass

    def listen(self) -> bool:
        self._server = QLocalServer()
        if self._server.listen(SERVER_NAME):
            self._server.newConnection.connect(self._on_new_connection)
            return True


        try:
            QLocalServer.removeServer(SERVER_NAME)
        except Exception:
            pass
        self._server = QLocalServer()
        if not self._server.listen(SERVER_NAME):
            return False
        self._server.newConnection.connect(self._on_new_connection)
        return True

    def _on_new_connection(self):
        while self._server is not None and self._server.hasPendingConnections():
            conn = self._server.nextPendingConnection()
            if conn is None:
                continue
            try:
                if conn.waitForReadyRead(1000):
                    data = bytes(conn.readAll())
                    try:
                        args = json.loads(data.decode("utf-8"))
                        if isinstance(args, list):


                            self._deliver([str(a) for a in args])
                    except Exception:
                        pass
            finally:
                conn.disconnectFromServer()
