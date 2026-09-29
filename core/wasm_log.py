"""Cross-platform logging for desktop pygame and pygbag/WASM.

In WASM (pygbag), messages go to the browser DevTools console via
``js.console.log``.  On desktop they go to stdout.
"""

from __future__ import annotations

try:
    import js as _js

    def browser_log(msg: str) -> None:
        """Log *msg* to the browser DevTools console (WASM) or stdout."""
        _js.console.log(str(msg))
except ImportError:

    def browser_log(msg: str) -> None:
        """Log *msg* to stdout (desktop fallback)."""
        print(msg, flush=True)


__all__ = ["browser_log"]
