# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

from pathlib import Path
import sys
import threading
import time
import unittest


SCRIPTS_MODULES = Path(__file__).resolve().parents[3] / "scripts" / "modules"
sys.path.insert(0, str(SCRIPTS_MODULES))
from _bpy_internal.http.thread_context import ThreadContext  # noqa: E402


class ThreadContextTests(unittest.TestCase):
    def test_pipe_is_bidirectional(self) -> None:
        first, second = ThreadContext.Pipe()

        first.send("to-second")
        self.assertTrue(second.poll())
        self.assertEqual(second.recv(), "to-second")
        self.assertFalse(second.poll())

        second.send("to-first")
        self.assertTrue(first.poll())
        self.assertEqual(first.recv(), "to-first")

    def test_process_compatible_worker_and_event_use_threads(self) -> None:
        context = ThreadContext()
        completed = context.Event()
        worker = context.Process(target=completed.set, daemon=True)

        self.assertIsInstance(worker, threading.Thread)
        worker.start()
        worker.join(timeout=1.0)

        self.assertFalse(worker.is_alive())
        self.assertTrue(completed.is_set())

    def test_rejects_one_way_pipe(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplex"):
            ThreadContext.Pipe(duplex=False)

    def test_poll_timeout_preserves_received_value(self) -> None:
        first, second = ThreadContext.Pipe()

        sender = threading.Thread(target=lambda: (time.sleep(0.01), first.send("ready")))
        sender.start()
        self.assertTrue(second.poll(0.5))
        self.assertEqual(second.recv(), "ready")
        sender.join(timeout=1.0)


if __name__ == "__main__":
    unittest.main()
