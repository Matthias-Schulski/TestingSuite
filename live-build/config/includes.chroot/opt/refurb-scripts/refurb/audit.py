import xml.etree.ElementTree as ET
from typing import List, Tuple

from .utils import run_cmd, ts
from .xmlio import write_xml, new_root


def _lshw_xml() -> str:
    code, out, err = run_cmd(["lshw", "-xml"])
    if code != 0:
        return f"<error time='{ts()}'>lshw failed: {err}</error>"
    return out


def _dmidecode() -> str:
    code, out, err = run_cmd(["dmidecode"])
    if code != 0:
        return f"dmidecode failed: {err}"
    return out


def _list_disks() -> List[str]:
    code, out, _ = run_cmd(["bash", "-lc", "lsblk -nd -o NAME,TYPE | awk '$2==\"disk\"{print $1}'"])
    if code != 0:
        return []
    return [f"/dev/{n.strip()}" for n in out.strip().splitlines() if n.strip()]


def _smartctl(dev: str) -> Tuple[bool, str]:
    code, out, err = run_cmd(["smartctl", "-a", dev])
    ok = code == 0 or code == 4
    return ok, out if out else err


def gather_audit() -> ET.Element:
    root = new_root("audit", {"time": ts()})
    lshw_raw = _lshw_xml()
    try:
        lshw_el = ET.fromstring(lshw_raw)
    except ET.ParseError:
        lshw_el = ET.Element("lshw_raw")
        lshw_el.text = lshw_raw
    root.append(lshw_el)

    dmi_el = ET.SubElement(root, "dmidecode")
    dmi_el.text = _dmidecode()

    disks_el = ET.SubElement(root, "disks")
    for dev in _list_disks():
        ok, txt = _smartctl(dev)
        d = ET.SubElement(disks_el, "disk", {"device": dev, "smart_ok": str(ok).lower()})
        d.text = txt

    bat_el = ET.SubElement(root, "battery")
    code, out, _ = run_cmd(["bash", "-lc", "upower -e | grep -i battery || true"]) 
    bat_paths = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
    for bp in bat_paths:
        code, bout, _ = run_cmd(["upower", "-i", bp])
        b = ET.SubElement(bat_el, "upower", {"path": bp})
        b.text = bout

    return root


def save_audit(path: str) -> None:
    root = gather_audit()
    write_xml(path, root)
