import threading
import time

import requests
import qrcode
import tkinter as tk
from tkinter import font as tkfont
from PIL import ImageTk

import app_config as cfg

POLL_TIMEOUT = 10   # seconds, HTTP request timeout
RETRY_DELAY = 5      # seconds to wait before retrying after an error
REFRESH_BUFFER = 2   # extra seconds after expiry before refetching, to avoid asking
                      # the server a hair too early and getting the old code back


class AttendanceQRApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Attendance QR — {cfg.DEPARTMENT_LABEL or cfg.DEVICE_ID}")
        self.root.geometry("420x560")
        self.root.configure(bg="#0f172a")
        self.root.minsize(360, 480)

        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._next_refresh_at = 0.0
        self._current_code = None

        self._build_ui()

        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

        self._tick()  # starts the 1s countdown UI updater
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- UI ----------
    def _build_ui(self):
        title_font = tkfont.Font(family="Segoe UI", size=16, weight="bold")
        code_font = tkfont.Font(family="Consolas", size=24, weight="bold")
        small_font = tkfont.Font(family="Segoe UI", size=10)

        header = tk.Label(
            self.root, text=cfg.DEPARTMENT_LABEL or "Attendance Code",
            font=title_font, fg="#e2e8f0", bg="#0f172a",
        )
        header.pack(pady=(18, 6))

        self.qr_label = tk.Label(self.root, bg="#0f172a")
        self.qr_label.pack(pady=10)

        self.code_var = tk.StringVar(value="—— —— —— —— ——")
        code_label = tk.Label(
            self.root, textvariable=self.code_var, font=code_font,
            fg="#38bdf8", bg="#0f172a",
        )
        code_label.pack(pady=(4, 2))

        self.status_var = tk.StringVar(value="Connecting…")
        tk.Label(
            self.root, textvariable=self.status_var, font=small_font,
            fg="#94a3b8", bg="#0f172a",
        ).pack(pady=(0, 4))

        self.countdown_var = tk.StringVar(value="")
        tk.Label(
            self.root, textvariable=self.countdown_var, font=small_font,
            fg="#64748b", bg="#0f172a",
        ).pack(pady=(0, 12))

        tk.Button(
            self.root, text="Refresh Now", command=self._manual_refresh,
            bg="#1e293b", fg="#e2e8f0", relief="flat", padx=12, pady=6,
            activebackground="#334155", activeforeground="#ffffff",
        ).pack(pady=(0, 10))

    # ---------- networking (background thread) ----------
    def _fetch_code(self):
        resp = requests.post(
            cfg.DEPT_CODE_URL,
            json={"device_id": cfg.DEVICE_ID, "device_password": cfg.DEVICE_PASSWORD},
            timeout=POLL_TIMEOUT,
        )
        if resp.status_code == 200:
            return resp.json(), None
        try:
            err = resp.json().get("error", f"HTTP {resp.status_code}")
        except Exception:
            err = f"HTTP {resp.status_code}"
        return None, err

    def _safe_fetch(self):
        try:
            return self._fetch_code()
        except requests.exceptions.RequestException as e:
            return None, f"network error: {e}"
        except Exception as e:
            return None, f"error: {e}"

    def _worker_loop(self):
        while not self._stop.is_set():
            data, err = self._safe_fetch()
            if data:
                self._apply_data(data)
                expires = int(data.get("expires_in_seconds", 600))
                wait_s = expires + REFRESH_BUFFER
            else:
                self._apply_error(err)
                wait_s = RETRY_DELAY

            with self._lock:
                self._next_refresh_at = time.time() + wait_s
            self._stop.wait(wait_s)

    def _manual_refresh(self):
        def run():
            data, err = self._safe_fetch()
            if data:
                self._apply_data(data)
                expires = int(data.get("expires_in_seconds", 600))
                with self._lock:
                    self._next_refresh_at = time.time() + expires + REFRESH_BUFFER
            else:
                self._apply_error(err)
        threading.Thread(target=run, daemon=True).start()

    # ---------- UI updates (scheduled onto main thread) ----------
    def _apply_data(self, data):
        code = data.get("code", "")
        dept = data.get("department", cfg.DEPARTMENT_LABEL)
        self._current_code = code

        def update():
            self.code_var.set(self._format_code(code))
            self.status_var.set(f"{dept} · live")
            self._render_qr(code)
        self.root.after(0, update)

    def _apply_error(self, err):
        def update():
            self.status_var.set(f"⚠ {err}")
        self.root.after(0, update)

    @staticmethod
    def _format_code(code):
        if not code:
            return "—— —— —— —— ——"
        return " ".join(code[i:i + 2] for i in range(0, len(code), 2))

    def _render_qr(self, code):
        content = cfg.QR_CONTENT_TEMPLATE.format(
            code=code, department=cfg.DEPARTMENT_LABEL or "", device_id=cfg.DEVICE_ID
        )
        qr = qrcode.QRCode(border=2, box_size=10)
        qr.add_data(content)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0f172a", back_color="#e2e8f0").convert("RGB")
        img = img.resize((280, 280))
        photo = ImageTk.PhotoImage(img)
        self.qr_label.configure(image=photo)
        self.qr_label.image = photo  # keep a reference, tkinter needs it

    def _tick(self):
        with self._lock:
            remaining = int(self._next_refresh_at - time.time())
        if remaining > 0 and self._current_code:
            m, s = divmod(remaining, 60)
            self.countdown_var.set(f"Next rotation in {m:02d}:{s:02d}")
        elif self._current_code:
            self.countdown_var.set("Refreshing…")
        self.root.after(1000, self._tick)

    def _on_close(self):
        self._stop.set()
        self.root.destroy()


def main():
    root = tk.Tk()
    AttendanceQRApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
