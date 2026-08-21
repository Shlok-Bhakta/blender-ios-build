# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Thread-backed subset of the multiprocessing context API used on iOS."""

from __future__ import annotations

import queue
import threading
from collections import deque
from typing import Any


class ThreadConnection:
    """One endpoint of an in-process, bidirectional message channel."""

    def __init__(self, incoming: queue.Queue[Any], outgoing: queue.Queue[Any]) -> None:
        self._incoming = incoming
        self._outgoing = outgoing
        self._pending: deque[Any] = deque()

    def send(self, value: Any) -> None:
        self._outgoing.put(value)

    def poll(self, timeout: float = 0.0) -> bool:
        if self._pending:
            return True
        try:
            value = self._incoming.get(timeout=timeout) if timeout > 0.0 else self._incoming.get_nowait()
        except queue.Empty:
            return False
        self._pending.append(value)
        return True

    def recv(self) -> Any:
        if self._pending:
            return self._pending.popleft()
        return self._incoming.get()


class ThreadContext:
    """Match the multiprocessing context operations used by BackgroundDownloader."""

    Event = threading.Event
    Process = threading.Thread

    @staticmethod
    def Pipe(*, duplex: bool = True) -> tuple[ThreadConnection, ThreadConnection]:
        if not duplex:
            raise ValueError("the Blender background downloader requires a duplex pipe")

        first_incoming: queue.Queue[Any] = queue.Queue()
        second_incoming: queue.Queue[Any] = queue.Queue()
        return (
            ThreadConnection(first_incoming, second_incoming),
            ThreadConnection(second_incoming, first_incoming),
        )
