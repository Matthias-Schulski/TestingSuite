import os
import subprocess
import time
from typing import List, Tuple, Optional


def clear_screen() -> None:
    try:
        subprocess.run(["clear"], check=False)
    except Exception:
        print("\033c", end="")


def run_cmd(cmd: List[str], timeout: Optional[int] = None) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        return p.returncode, p.stdout, p.stderr
    except Exception as e:
        return 1, "", str(e)


def run_shell(cmd: str, timeout: Optional[int] = None) -> Tuple[int, str, str]:
    return run_cmd(["bash", "-lc", cmd], timeout)


def ask(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:
        return ""


def pause(msg: str = "Press ENTER to continue...") -> None:
    try:
        input(msg)
    except EOFError:
        pass


def ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def print_box(title: str, lines: List[str]) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("-" * 60)
    for ln in lines:
        print(ln)
    print("=" * 60 + "\n")


def which(bin_name: str) -> Optional[str]:
    for p in os.getenv("PATH", "").split(":"):
        full = os.path.join(p, bin_name)
        if os.path.isfile(full) and os.access(full, os.X_OK):
            return full
    return None


def escalate_needed(bins: List[str]) -> List[str]:
    return [b for b in bins if which(b) is None]
