#!/usr/bin/env python3

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
CONTEXT_HEADER = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_ContextIOS.hh"
CONTEXT_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_ContextIOS.mm"
SYSTEM_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_SystemIOS.mm"
WINDOW_HEADER = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.hh"
WINDOW_SOURCE = REPOSITORY / "intern" / "ghost" / "intern" / "GHOST_WindowIOS.mm"


class GhostPresentSchedulingTests(unittest.TestCase):
    def test_drawable_state_is_per_context_and_per_delegate_frame(self) -> None:
        header = CONTEXT_HEADER.read_text()
        source = CONTEXT_SOURCE.read_text()

        self.assertNotIn("prevDrawable", header + source)
        self.assertNotIn("current_drawable_presented", header + source)
        self.assertIn("bool drawable_presented_in_frame_ = false;", header)
        self.assertIn("drawable_presented_in_frame_ = false;", source)
        self.assertIn("if (drawable_presented_in_frame_)", source)

    def test_delegate_opens_a_frame_before_flushing_pending_present(self) -> None:
        source = SYSTEM_SOURCE.read_text()
        begin = source.index("current_active_window_->beginFrame();")
        pending = source.index("current_active_window_->hasDeferredSwapBuffers()")
        flush = source.index("current_active_window_->flushDeferredSwapBuffers();")

        self.assertLess(begin, pending)
        self.assertLess(pending, flush)
        self.assertNotIn("current_active_window_->needsDisplayUpdate();", source)

    def test_window_coalesces_present_requests(self) -> None:
        header = WINDOW_HEADER.read_text()
        source = WINDOW_SOURCE.read_text()

        self.assertIn("bool hasDeferredSwapBuffers() const", header)
        self.assertIn("bool deferred_swap_buffers_ = false;", header)
        self.assertNotIn("deferred_swap_buffers_count", header + source)
        self.assertIn("deferred_swap_buffers_ = true;", source)

        clear = source.index("deferred_swap_buffers_ = false;", source.index("flushDeferredSwapBuffers"))
        present = source.index("context->swapBufferRelease();", clear)
        self.assertLess(clear, present)


if __name__ == "__main__":
    unittest.main()
