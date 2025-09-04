import os
from typing import Dict


def _load_file(path: str) -> Dict[str, str]:
    conf: Dict[str, str] = {}
    if not os.path.exists(path):
        return conf
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    conf[k.strip()] = v.strip()
    except Exception:
        pass
    return conf


def load_config() -> Dict[str, str]:
    env = {
        "REFURB_SMB_URL": os.getenv("REFURB_SMB_URL", "//SERVER/Refurbish"),
        "REFURB_SMB_USER": os.getenv("REFURB_SMB_USER", ""),
        "REFURB_SMB_PASS": os.getenv("REFURB_SMB_PASS", ""),
        "REFURB_SMB_DOMAIN": os.getenv("REFURB_SMB_DOMAIN", ""),
        "REFURB_MOUNTPOINT": os.getenv("REFURB_MOUNTPOINT", "/mnt/refurbish"),
        "REFURB_FAST": os.getenv("REFURB_FAST", "0"),
    }
    file_conf = _load_file("/etc/refurb.conf")
    cfg = {**env, **file_conf, **env}
    return cfg
