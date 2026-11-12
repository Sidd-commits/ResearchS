"""
Environment detection utilities for ResearchS.
Safely detects memory-constrained cloud environments (e.g., Render Free Tier 512MB RAM)
versus high-performance local environments with GPU/adequate RAM.
"""

from __future__ import annotations
import os
import sys
import logging

logger = logging.getLogger("researchs.utils.env")

def is_constrained_environment() -> bool:
    """
    Detects if running in a memory-constrained container (e.g. Render 512MB Free Tier).
    In constrained cloud environments, lightweight semantic abstraction and RAG pipelines
    are utilized to prevent Linux OOM SIGKILL (exit code 137).
    """
    # 0. Override flag for developers who want to force heavy transformer loading
    if os.getenv("FORCE_HEAVY_MODELS", "").lower() == "true":
        return False

    # 1. Direct Render environment variables
    render_env_keys = [
        "RENDER",
        "RENDER_SERVICE_ID",
        "RENDER_INSTANCE_ID",
        "RENDER_SERVICE_NAME",
        "RENDER_GIT_COMMIT",
        "ON_RENDER",
    ]
    if any(os.getenv(k) for k in render_env_keys):
        return True

    # 2. Render filesystem indicator (Python interpreter or root dir in /opt/render)
    if os.path.exists("/opt/render") or "/opt/render" in sys.executable or "/opt/render" in os.getenv("PATH", ""):
        return True

    # 3. Linux container cgroup memory limits (checks actual 512MB limit)
    for cgroup_file in [
        "/sys/fs/cgroup/memory.max",
        "/sys/fs/cgroup/memory/memory.limit_in_bytes",
    ]:
        try:
            if os.path.exists(cgroup_file):
                raw = open(cgroup_file, "r").read().strip()
                if raw and raw != "max":
                    limit = int(raw)
                    # If limit is set and under 2GB (2 * 1024 * 1024 * 1024 bytes)
                    if 0 < limit < 2 * 1024 * 1024 * 1024:
                        return True
        except Exception:
            pass

    # 4. Any cloud web container running on Linux with a PORT set
    if sys.platform.startswith("linux") and bool(os.getenv("PORT")):
        return True

    # 5. Host memory check using psutil:
    # If total system RAM < 4GB or currently available RAM < 1.5GB, activate constrained mode
    # to safeguard against Windows OS Error 1455 / Linux OOM SIGKILL (exit code 137).
    try:
        import psutil
        vm = psutil.virtual_memory()
        avail_gb = vm.available / (1024 ** 3)
        total_gb = vm.total / (1024 ** 3)
        if total_gb < 4.0 or avail_gb < 1.5:
            return True
    except Exception:
        pass

    return False
