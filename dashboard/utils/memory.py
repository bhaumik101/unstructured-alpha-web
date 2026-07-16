"""
utils/memory.py — release freed memory back to the OS.

CPython frees objects promptly, but glibc's malloc often keeps the freed arenas
mapped to the process, so RSS (what Render measures for the 512MB OOM limit)
stays high even after a big DataFrame is gone. Calling malloc_trim(0) forces
glibc to return those arenas to the OS. Safe no-op on non-glibc platforms.

Call after a heavy, transient workload (multi-ticker scans, backtests) so the
peak doesn't leave a high-water mark that tips the next request over the limit.
"""

import gc


def release_memory() -> None:
    """Run a full GC, then hand freed heap back to the OS (best-effort)."""
    try:
        gc.collect()
    except Exception:
        pass
    try:
        import ctypes
        libc = ctypes.CDLL("libc.so.6")   # glibc on Render's Linux
        libc.malloc_trim(0)
    except Exception:
        pass  # non-glibc / non-Linux — gc.collect() above already ran
