import threading
import time
import tkinter as tk
from typing import List

from .utils import run_cmd, ts


def _prompt(msg: str) -> None:
    try:
        input(msg)
    except EOFError:
        pass


def test_video_ports(logger) -> None:
    logger.append("video_ports", time=ts(), action="start")
    code, out, _ = run_cmd(["bash", "-lc", "DISPLAY=:0 xrandr --query || true"]) 
    logger.append("video_ports", time=ts(), action="ports", output=(out.strip() or "n/a"))
    print("Video Ports Test: connect a display to each port and confirm signal.")
    _prompt("Press ENTER after validating all ports...")
    logger.append("video_ports", time=ts(), action="end")


def test_usb_ports(logger) -> None:
    logger.append("usb_ports", time=ts(), action="start")
    print("USB Ports Test: We will monitor udev for USB add/remove events.")
    print("Plug and unplug a USB device in each port.")
    print("Press Ctrl+C when finished or wait 20 seconds of inactivity.")

    def monitor():
        run_cmd(["bash", "-lc", "udevadm monitor --udev --subsystem-match=usb --property --env | head -n 1000"],)

    t = threading.Thread(target=monitor, daemon=True)
    t.start()
    try:
        time.sleep(20)
    except KeyboardInterrupt:
        pass
    logger.append("usb_ports", time=ts(), action="end")


def test_audio(logger) -> None:
    logger.append("audio", time=ts(), action="start")
    print("Audio Test: you'll hear white noise on speakers. Adjust volume.")
    run_cmd(["bash", "-lc", "speaker-test -t pink -l 1 || true"]) 
    _prompt("Did you hear audio on speakers/headphones? Press ENTER to continue...")
    logger.append("audio", time=ts(), action="end")


def _color_screen(color: str, seconds: int = 3) -> None:
    win = tk.Tk()
    win.title(f"Screen Test - {color}")
    win.attributes("-fullscreen", True)
    frame = tk.Frame(win, bg=color)
    frame.pack(fill=tk.BOTH, expand=True)
    win.update()
    win.after(seconds * 1000, win.destroy)
    win.mainloop()


def laptop_screen_test(logger) -> None:
    logger.append("laptop_screen", time=ts(), action="start")
    print("Internal Screen Test: watch for dead pixels/backlight bleed.")
    for c in ["red", "green", "blue", "white", "black"]:
        _color_screen(c)
    logger.append("laptop_screen", time=ts(), action="end")


def keyboard_tester(logger) -> None:
    logger.append("keyboard", time=ts(), action="start")
    pressed: List[str] = []

    def on_key(event):
        k = event.keysym
        if k not in pressed:
            pressed.append(k)
        lbl.config(text=f"Keys pressed: {', '.join(pressed)}")

    win = tk.Tk()
    win.title("Keyboard Tester - press all keys")
    win.geometry("800x400")
    lbl = tk.Label(win, text="Press keys. Close window when done.", font=("Arial", 16))
    lbl.pack(pady=40)
    win.bind("<Key>", on_key)
    win.mainloop()
    logger.append("keyboard", time=ts(), action="end", count=len(pressed))


def wifi_bluetooth_test(logger) -> None:
    logger.append("wireless", time=ts(), action="start")
    code, out, _ = run_cmd(["bash", "-lc", "iw dev | awk '$1==\"Interface\"{print $2}'"])
    ifaces = [ln.strip() for ln in out.splitlines() if ln.strip()]
    for iface in ifaces:
        code, so, _ = run_cmd(["bash", "-lc", f"iw dev {iface} scan | egrep 'SSID|signal' | head -n 40 || true"])
        logger.append("wifi", time=ts(), iface=iface, scan=(so.strip() or "n/a"))
    code, out, _ = run_cmd(["bash", "-lc", "which bluetoothctl >/dev/null 2>&1 && echo yes || echo no"])
    if out.strip() == "yes":
        code, bo, _ = run_cmd(["bash", "-lc", "bluetoothctl --timeout 10 scan on | sed -n '1,200p' || true"])
        logger.append("bluetooth", time=ts(), scan=bo.strip() or "n/a")
    else:
        logger.append("bluetooth", time=ts(), scan="unsupported")
    logger.append("wireless", time=ts(), action="end")


def webcam_test(logger) -> None:
    logger.append("webcam", time=ts(), action="start")
    run_cmd(["bash", "-lc", "fswebcam -r 640x480 -q /tmp/refurb-webcam.jpg || true"]) 
    _prompt("Webcam captured to /tmp/refurb-webcam.jpg if available. Press ENTER...")
    logger.append("webcam", time=ts(), action="end")


def sdcard_test(logger) -> None:
    logger.append("sdcard", time=ts(), action="start")
    print("Insert an SD card. We will detect a new block device.")
    run_cmd(["bash", "-lc", "udevadm monitor --udev --subsystem-match=block --property --env | head -n 100 || true"]) 
    logger.append("sdcard", time=ts(), action="end")


def physical_inspection(logger) -> None:
    logger.append("physical", time=ts(), action="start")
    questions = [
        "Behuizing vrij van scheuren? (y/n)",
        "Scharnieren stevig? (y/n)",
        "Alle schroeven aanwezig? (y/n)",
        "Poorten schoon en onbeschadigd? (y/n)",
    ]
    results = []
    for q in questions:
        ans = input(q + " ").strip().lower()
        results.append(f"{q} => {ans}")
    logger.append("physical", time=ts(), action="end", notes=" | ".join(results))
