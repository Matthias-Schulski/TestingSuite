from __future__ import annotations

import os
import sys
import time
import xml.etree.ElementTree as ET

from .config import load_config
from .utils import clear_screen, ask, pause, print_box, ensure_dir
from .smb import mount_share, ensure_device_folder
from .xmlio import write_xml, XmlLogger
from . import audit as audit_mod
from . import delta as delta_mod
from . import stress as stress_mod
from . import interactive as inter


def sanity_check(audit_root: ET.Element) -> bool:
    mem_nodes = audit_root.findall(".//node[@class='memory']")
    disk_nodes = audit_root.findall(".//node[@class='disk']")
    ok_mem = len(mem_nodes) > 0
    ok_disk = len(disk_nodes) > 0
    if not ok_mem:
        print("Sanity check failed: no memory detected.")
        return False
    if not ok_disk:
        print("Sanity check: no storage detected. Confirm to continue.")
        ans = ask("Type 'YES' to continue without storage: ")
        if ans.strip().upper() != "YES":
            return False
    return True


def phase_identification(cfg):
    clear_screen()
    print("Refurb Testomgeving - Initialisatie")
    device_id = ""
    while not device_id:
        device_id = ask("Voer uniek ID in: ").strip()
    print("Mounting SMB share...")
    ok, msg = mount_share(
        cfg["REFURB_SMB_URL"],
        cfg["REFURB_MOUNTPOINT"],
        cfg.get("REFURB_SMB_USER", ""),
        cfg.get("REFURB_SMB_PASS", ""),
        cfg.get("REFURB_SMB_DOMAIN", ""),
    )
    if not ok:
        print(f"Kon SMB share niet mounten: {msg}")
        sys.exit(1)
    base_path = ensure_device_folder(cfg["REFURB_MOUNTPOINT"], device_id)
    return device_id, base_path


def phase_delta(base_path: str) -> str:
    baseline = os.path.join(base_path, "audit_baseline.xml")
    new_audit_path = os.path.join(base_path, "audit_current.xml")
    print("Uitvoeren hardware-audit...")
    audit_mod.save_audit(new_audit_path)
    if not os.path.exists(baseline):
        return "new"
    try:
        old_xml = ET.parse(baseline).getroot()
        new_xml = ET.parse(new_audit_path).getroot()
        changes = delta_mod.diff_audits(old_xml, new_xml)
    except Exception:
        changes = ["Kon audits niet vergelijken (parse-fout)"]
    print_box("Wijzigingen sinds laatste audit", changes or ["Geen wijzigingen gedetecteerd."])
    print("Kies een optie:\n1) Alleen gewijzigde onderdelen testen\n2) Volledige hertest\n3) Wijzigingen accepteren")
    choice = ask("Keuze [1/2/3]: ").strip() or "2"
    if choice == "1":
        return "partial"
    if choice == "3":
        os.replace(new_audit_path, baseline)
        return "accepted"
    return "full"


def phase_automated(base_path: str, fast: bool) -> bool:
    audit_path = os.path.join(base_path, "audit_baseline.xml")
    print("Uitvoeren hardware-audit en sanity check...")
    audit_mod.save_audit(audit_path)
    try:
        audit_root = ET.parse(audit_path).getroot()
    except Exception:
        print("Kon audit niet parsen.")
        return False
    if not sanity_check(audit_root):
        return False

    auto_log_path = os.path.join(base_path, "auto_test.xml")
    auto_logger = XmlLogger(auto_log_path, root_tag="auto_tests")

    cpu_duration = 600 if not fast else 10
    mem_mb = 2048 if not fast else 64
    mem_duration = 300 if not fast else 20

    ok_cpu = stress_mod.cpu_stress(cpu_duration, auto_logger)
    ok_mem = stress_mod.mem_test(mem_mb, mem_duration, auto_logger)
    ok_storage = stress_mod.storage_tests(auto_logger)
    ok_battery = stress_mod.battery_health(auto_logger)

    overall = ok_cpu and ok_mem and ok_storage and ok_battery
    print_box("Samenvatting automatische tests", [
        f"CPU: {'GESLAAGD' if ok_cpu else 'GEFAALD'}",
        f"RAM: {'GESLAAGD' if ok_mem else 'GEFAALD'}",
        f"Opslag: {'GESLAAGD' if ok_storage else 'GEFAALD'}",
        f"Batterij: {'GESLAAGD' if ok_battery else 'GEFAALD'}",
        f"Totaal: {'GESLAAGD' if overall else 'GEFAALD'}",
    ])
    return overall


def phase_morning_hand_off(base_path: str) -> str:
    print("[ENTER] verder naar interactieve tests, [R] hertest selectie, [A] afbreken")
    ch = ask("").strip().upper()
    if ch == "R":
        return "retest"
    if ch == "A":
        return "abort"
    return "continue"


def phase_interactive(base_path: str) -> None:
    os.environ.setdefault("DISPLAY", ":0")
    inter_log_path = os.path.join(base_path, "interactive_test.xml")
    inter_logger = XmlLogger(inter_log_path, root_tag="interactive_tests")

    inter.test_video_ports(inter_logger)
    inter.test_usb_ports(inter_logger)
    inter.test_audio(inter_logger)
    inter.laptop_screen_test(inter_logger)
    inter.keyboard_tester(inter_logger)
    inter.wifi_bluetooth_test(inter_logger)
    inter.sdcard_test(inter_logger)
    inter.webcam_test(inter_logger)
    inter.physical_inspection(inter_logger)


def phase_final(base_path: str) -> None:
    notes = ask("Voer eventuele opmerkingen in en druk op Enter: ")
    status = ask("Geef de finale status (standaard: 'Klaar voor installatie'): ").strip() or "Klaar voor installatie"
    root = ET.Element("summary")
    ET.SubElement(root, "notes").text = notes
    ET.SubElement(root, "status").text = status
    write_xml(os.path.join(base_path, "summary.xml"), root)
    print("Voltooid. Systeem zal over 30 seconden afsluiten...")
    try:
        time.sleep(30)
        os.system("shutdown -h now")
    except Exception:
        pass


def main():
    cfg = load_config()
    device_id, base_path = phase_identification(cfg)
    state = "new" if not os.path.exists(os.path.join(base_path, "audit_baseline.xml")) else "existing"
    if state == "existing":
        action = phase_delta(base_path)
        if action == "accepted":
            print("Wijzigingen geaccepteerd. Ga verder met testen.")
    fast = cfg.get("REFURB_FAST", "0") == "1"
    ok = phase_automated(base_path, fast)
    handoff = phase_morning_hand_off(base_path)
    if handoff == "abort":
        print("Afgebroken op verzoek technicus.")
        return 1
    phase_interactive(base_path)
    phase_final(base_path)
    return 0

