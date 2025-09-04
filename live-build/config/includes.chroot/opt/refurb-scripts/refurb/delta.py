import xml.etree.ElementTree as ET
from typing import List


def _summarize_lshw(root: ET.Element) -> List[str]:
    summary: List[str] = []
    for node in root.findall(".//node"):
        cls = node.get("class") or ""
        prod = (node.findtext("product") or "").strip()
        size = node.find("size")
        sizev = size.text.strip() if size is not None and size.text else ""
        if cls in {"processor", "memory", "display", "network", "storage", "disk"}:
            summary.append(f"{cls}:{prod}:{sizev}")
    return sorted(set(summary))


def diff_audits(old_xml: ET.Element, new_xml: ET.Element) -> List[str]:
    old_lshw = old_xml.find("list") or old_xml.find("lshw") or old_xml
    new_lshw = new_xml.find("list") or new_xml.find("lshw") or new_xml
    old_summary = _summarize_lshw(old_lshw)
    new_summary = _summarize_lshw(new_lshw)
    removed = [f"[-] {s}" for s in old_summary if s not in new_summary]
    added = [f"[+] {s}" for s in new_summary if s not in old_summary]
    return removed + added
