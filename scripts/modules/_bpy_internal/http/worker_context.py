# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Select the background-worker transport supported by the host platform."""

from __future__ import annotations

import sys
from typing import Any, Protocol


class Connection(Protocol):
    def send(self, value: Any) -> None: ...
    def poll(self, timeout: float = 0.0) -> bool: ...
    def recv(self) -> Any: ...


class Worker(Protocol):
    def start(self) -> None: ...
    def is_alive(self) -> bool: ...


if sys.platform == 'ios':
    from threading import Event as EventClass

    from .thread_context import ThreadContext

    context = ThreadContext()
    worker_kind = 'thread'
else:
    import multiprocessing
    from multiprocessing.synchronize import Event as EventClass

    context = multiprocessing.get_context(method='spawn')
    worker_kind = 'process'


def start_worker(worker: Worker, cleanup_context_factory: Any) -> None:
    """Start a worker with the process-only main-module cleanup when needed."""
    if worker_kind == 'thread':
        worker.start()
        return

    with cleanup_context_factory():
        worker.start()
