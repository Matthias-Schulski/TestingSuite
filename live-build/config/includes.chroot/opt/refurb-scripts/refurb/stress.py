import os
import time
import xml.etree.ElementTree as ET
from typing import List, Tuple

from .utils import run_cmd, ts


def _read_thermals() -> List[Tuple[str, int]]:
    temps: List[Tuple[str, int]] = []
    for tz in sorted(os.listdir("/sys/class/thermal")):
        if not tz.startswith("thermal_zone"):
            continue
        path = f"/sys/class/thermal/{tz}/temp"
        try:
            with open(path, "r") as f:
                t = int(f.read().strip())
            temps.append((tz, t))
        except Exception:
            pass
    return temps


def cpu_stress(duration_sec: int, logger) -> bool:
    start = time.time()
    logger.append("cpu_test", time=ts(), action="start")
    code, _, err = run_cmd(["stress-ng", "--cpu", "0", "--timeout", str(duration_sec), "--metrics-brief"])
    ok = code == 0
    temps = _read_thermals()
    temps_str = ", ".join([f"{n}:{t/1000:.1f}C" for n, t in temps])
    logger.append("cpu_test", time=ts(), action="end", ok=str(ok).lower(), temps=temps_str)
    return ok


def mem_test(max_mb: int, duration_sec: int, logger) -> bool:
    loops = max(1, duration_sec // 30)
    alloc_mb = max(32, max_mb)
    logger.append("mem_test", time=ts(), action="start", alloc_mb=str(alloc_mb), loops=str(loops))
    ok = True
    for i in range(loops):
        code, _, err = run_cmd(["bash", "-lc", f"memtester {alloc_mb}M 1"], timeout=duration_sec or None)
        if code != 0:
            ok = False
            break
    logger.append("mem_test", time=ts(), action="end", ok=str(ok).lower())
    return ok


def list_block_devices() -> List[str]:
    code, out, _ = run_cmd(["bash", "-lc", "lsblk -nd -o NAME,TYPE | awk '$2==\"disk\"{print $1}'"])
    if code != 0:
        return []
    return [f"/dev/{n.strip()}" for n in out.strip().splitlines() if n.strip()]


def storage_tests(logger) -> bool:
    ok_all = True
    for dev in list_block_devices():
        logger.append("storage_test", time=ts(), device=dev, action="smart_short_start")
        run_cmd(["smartctl", "-t", "short", dev])
        time.sleep(5)
        code, out, err = run_cmd(["smartctl", "-H", "-A", dev])
        ok = code == 0
        entry = logger.append("storage_test", time=ts(), device=dev, action="smart_health", ok=str(ok).lower())
        el = ET.SubElement(entry, "report")
        el.text = out or err
        ok_all = ok_all and ok
    return ok_all


def battery_health(logger) -> bool:
    code, out, _ = run_cmd(["bash", "-lc", "upower -e | grep -i battery || true"]) 
    bats = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
    if not bats:
        logger.append("battery", time=ts(), present="false")
        return True
    ok_all = True
    for bp in bats:
        code, bout, _ = run_cmd(["upower", "-i", bp])
        capacity = ""; energy_full = ""; energy_design = ""
        for ln in bout.splitlines():
            if "percentage:" in ln:
                capacity = ln.split(":", 1)[1].strip()
            if "energy-full:" in ln:
                energy_full = ln.split(":", 1)[1].strip()
            if "energy-full-design:" in ln:
                energy_design = ln.split(":", 1)[1].strip()
        logger.append("battery", time=ts(), path=bp, capacity=capacity, energy_full=energy_full, energy_design=energy_design)
        ok_all = ok_all and True
    return ok_all
