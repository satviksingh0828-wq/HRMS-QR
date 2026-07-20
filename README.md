# Attendance QR

A small desktop app (Python + Tkinter) that shows your department's rotating
attendance code as a QR code, polling:

```
POST /api/public/dept-code
{ "device_id": "...", "device_password": "..." }
```

It auto-refreshes on the server's own schedule (`expires_in_seconds`, ~10 min),
shows a live countdown, and has a manual "Refresh Now" button. Network errors
show inline and auto-retry every 5s.

## Files

```
attendance_qr_app/
├── main.py            # the app (UI + polling + QR rendering)
├── app_config.py       # loads config: baked-in (exe) or .env (dev)
├── build.py            # bakes .env values in, then runs PyInstaller
├── .env.example         # template — copy to .env
├── requirements.txt
└── .gitignore           # ignores .env, config_baked.py, build/, dist/
```

## 1. Run it in development (using .env)

```bash
cd attendance_qr_app
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
```

Edit `.env`:

```
DEPT_CODE_URL=https://your-server.example.com/api/public/dept-code
DEVICE_ID=8c2f0000-0000-0000-0000-000000000000
DEVICE_PASSWORD=a1b2c3d4e5f60718
DEPARTMENT_LABEL=Ops
QR_CONTENT_TEMPLATE={code}
```

Then run:

```bash
python main.py
```

`QR_CONTENT_TEMPLATE` controls what actually gets encoded in the QR image.
Default is just the raw code. If your scanner expects a URL instead, e.g.:

```
QR_CONTENT_TEMPLATE=https://your-server.example.com/attend?code={code}&dept={department}
```

## 2. Build the .exe (values get hardcoded in)

This is the part you asked about — how the credentials get baked into the exe
instead of shipping a `.env` file alongside it.

With your `.env` filled in and dependencies installed, just run:

```bash
python build.py
```

What it does, step by step:
1. Loads `.env`
2. Writes `config_baked.py` — a plain Python file with your URL / device id /
   password written in as literal strings
3. Runs PyInstaller (`--onefile --windowed`), which compiles `main.py` and
   everything it imports — including `config_baked.py` — into one executable.
   At this point the values are inside the compiled binary, not read from
   disk at runtime.
4. Deletes `config_baked.py` from your project folder afterward, so your
   source tree doesn't sit there with plaintext secrets in it (it's already
   baked into the exe by then — this step is just cleanup).

Output:
- Windows: `dist\AttendanceQR.exe`
- macOS/Linux: `dist/AttendanceQR`

That exe is now standalone — copy it to any machine and double-click it,
no `.env`, no Python install, no config screen needed.

### Important: build on the OS you're targeting

PyInstaller packages a binary for whatever OS it's *run on* — it does not
cross-compile. So:

- Want a Windows `.exe`? Run `python build.py` **on Windows**.
- Want a macOS app? Run it **on macOS**.
- Want a Linux binary? Run it **on Linux**.

If you only have a Linux/macOS machine but need a `.exe`, the easiest options
are: build on any Windows PC/VM you have access to, or use a free Windows CI
runner (e.g. a GitHub Actions workflow using `windows-latest` that runs the
same `pip install -r requirements.txt && python build.py` steps and uploads
`dist/AttendanceQR.exe` as an artifact).

## 3. Rotating credentials later

If the department password or URL ever changes, just update `.env` and
re-run `python build.py` to produce a fresh exe. There's no config UI in the
app on purpose — the whole point was "auto hardcode on build."

## Notes on the refresh logic

- On success, the app schedules its next fetch for
  `expires_in_seconds + 2s` from `rotated_at`, so it asks again just after
  the server has rotated rather than guessing a fixed interval.
- On failure (bad credentials, network drop, bad request), it shows the
  error inline and retries every 5 seconds until it succeeds.
- The countdown label and QR image update live without freezing the UI,
  since networking runs on a background thread.
