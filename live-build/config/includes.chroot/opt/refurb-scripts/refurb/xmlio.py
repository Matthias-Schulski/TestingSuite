import os
import xml.etree.ElementTree as ET
from typing import Optional


def write_xml(path: str, root: ET.Element) -> None:
    tree = ET.ElementTree(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def new_root(tag: str, attrib: Optional[dict] = None) -> ET.Element:
    return ET.Element(tag, attrib=attrib or {})


class XmlLogger:
    def __init__(self, path: str, root_tag: str = "log") -> None:
        self.path = path
        self.root_tag = root_tag
        if os.path.exists(path):
            try:
                self.tree = ET.parse(path)
                self.root = self.tree.getroot()
            except Exception:
                self.root = ET.Element(root_tag)
                self.tree = ET.ElementTree(self.root)
        else:
            self.root = ET.Element(root_tag)
            self.tree = ET.ElementTree(self.root)

    def append(self, tag: str, **attrs) -> ET.Element:
        el = ET.SubElement(self.root, tag, {k: str(v) for k, v in attrs.items()})
        self._flush()
        return el

    def add_text(self, parent: ET.Element, tag: str, text: str) -> ET.Element:
        el = ET.SubElement(parent, tag)
        el.text = text
        self._flush()
        return el

    def _flush(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.tree.write(self.path, encoding="utf-8", xml_declaration=True)
