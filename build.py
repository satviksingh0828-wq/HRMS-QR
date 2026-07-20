"""
Build script — turns this project into a single executable with your
URL / department id / password baked in, so the .exe needs no .env file
on the machine it runs on.

Steps this performs:
1. Reads .env (DEPT_CODE_URL, DEVICE_ID, DEVICE_PASSWORD, ...)
2. Writes config_baked.py with those values hardcoded as Python literals
3. Runs PyInstaller with --onefile to produce a single executable
4. Deletes config_baked.py from the source tree afterwards (the values
   already got compiled into the .exe by that point — this just keeps
   your secrets out of the working directory / git status)

IMPORTANT — PyInstaller does not cross-compile:
  - Run this ON Windows to get an .exe
  - Run this ON macOS to get a macOS binary
  - Run this ON Linux to get a Linux binary
If you need a Windows .exe and only have Linux/macOS, build it on a
Windows machine or a Windows CI runner (e.g. GitHub Actions windows-latest).
"""
import os
import subprocess
import sys

from dotenv import load_dotenv

APP_NAME = "AttendanceQR"


def require(name):
    val = os.environ.get(name)
    if not val:
        sys.exit(f"Missing {name} in .env — copy .env.example to .env and fill it in.")
    return val


def write_baked_config():
    dept_url = require("DEPT_CODE_URL")
    device_id = require("DEVICE_ID")
    device_password = require("DEVICE_PASSWORD")
    dept_label = os.environ.get("DEPARTMENT_LABEL", "")
    qr_template = os.environ.get("QR_CONTENT_TEMPLATE", "{code}")

    with open("config_baked.py", "w", encoding="utf-8") as f:
        f.write("# AUTO-GENERATED at build time by build.py. Do not commit this file.\n")
        f.write(f"DEPT_CODE_URL = {dept_url!r}\n")
        f.write(f"DEVICE_ID = {device_id!r}\n")
        f.write(f"DEVICE_PASSWORD = {device_password!r}\n")
        f.write(f"DEPARTMENT_LABEL = {dept_label!r}\n")
        f.write(f"QR_CONTENT_TEMPLATE = {qr_template!r}\n")

    print("[ok] config_baked.py generated (credentials hardcoded into the build)")


def run_pyinstaller():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", APP_NAME,
        "--noconfirm",
        "main.py",
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)


def cleanup():
    if os.path.exists("config_baked.py"):
        os.remove("config_baked.py")
        print("[ok] config_baked.py removed from source tree (values remain embedded in the exe)")


def main():
    load_dotenv()
    write_baked_config()
    try:
        run_pyinstaller()
        print(f"\n[done] Build complete.")
        print(f"       Windows:      dist\\{APP_NAME}.exe")
        print(f"       macOS/Linux:  dist/{APP_NAME}")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
