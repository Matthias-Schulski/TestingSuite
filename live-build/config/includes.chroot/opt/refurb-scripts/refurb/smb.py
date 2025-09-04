import os
import tempfile
from typing import Optional, Tuple

from .utils import run_cmd, ensure_dir


def mount_share(smb_url: str, mountpoint: str, username: str = "", password: str = "", domain: str = "") -> Tuple[bool, str]:
    if smb_url.startswith("local:"):
        ensure_dir(mountpoint)
        return True, "using local mountpoint"
    ensure_dir(mountpoint)
    opts = []
    cred_file: Optional[str] = None
    try:
        if username:
            fd, cred_file = tempfile.mkstemp(prefix="refurb-cred-", text=True)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(f"username={username}\n")
                f.write(f"password={password}\n")
                if domain:
                    f.write(f"domain={domain}\n")
            os.chmod(cred_file, 0o600)
            opts.append(f"credentials={cred_file}")
        else:
            # guest
            opts.append("guest")
        # Common options for stability
        opts.extend(["vers=3.0", "rw", "iocharset=utf8", "nofail"])
        cmd = [
            "mount", "-t", "cifs",
            smb_url,
            mountpoint,
            "-o", ",".join(opts),
        ]
        code, out, err = run_cmd(cmd)
        if code == 0:
            return True, out.strip() or "mounted"
        return False, err.strip() or out.strip()
    finally:
        if cred_file and os.path.exists(cred_file):
            try:
                os.remove(cred_file)
            except Exception:
                pass


def ensure_device_folder(mountpoint: str, device_id: str) -> str:
    path = os.path.join(mountpoint, f"ID-{device_id}")
    ensure_dir(path)
    return path
