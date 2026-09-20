# Python payloads

Copy `hello.py` into `/home/kali/payloads/` on the device, then open
**Custom Tools → Python Payloads**. You can also use **Add .py file** in the UI,
including from another computer browsing to `http://<device-ip>:8080`.

Scripts run with Python 3 as the backend's user (`kali`), with the payloads folder
as their working directory. Python dependencies must already be installed for
that interpreter. The UI supports optional quoted command-line arguments, live
stdout/stderr, text input, exit codes, and stopping a script and its children.
One payload can run at a time. Navigating away does not stop it; reopen the same
script to view its output or stop it. The console retains the latest 32K characters.

The live folder is separate from this source directory and is preserved by app
updates. Change it with `TOUCHUI_PAYLOADS_DIR` in the backend environment if needed.
Discovery lists regular `.py` files directly in the folder. Uploads accept UTF-8
text up to 1 MiB and never replace an existing filename. Helper files or packages
can be copied into the live folder over SSH. Scripts are ordinary executable
Python code with the device user's permissions; only install scripts you trust.
