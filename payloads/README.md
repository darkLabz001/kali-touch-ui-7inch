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

## Domain OSINT

`domain_osint.py` looks up a domain's public DNS records (A, AAAA, MX, NS, TXT,
CAA), RDAP registration details, and names published in certificate-transparency
logs. It uses Python's standard library; no API key or package installation is
needed.

On the device, select **domain_osint.py**, enter `example.org` in **Arguments**,
and tap **RUN**. Or leave Arguments empty, tap RUN, then enter the domain in the
input field and tap **Send** when prompted. An HTTP/HTTPS URL is also accepted;
only its hostname is looked up.

```bash
python3 domain_osint.py example.org
python3 domain_osint.py example.org --no-ct
python3 domain_osint.py example.org --limit 10 --timeout 15
```

Text and JSON reports are saved beside the script in `reports/` (on the Pi:
`/home/kali/payloads/reports/`). JSON includes source URLs, collection time, full
returned DNS answers and matching certificate names, and individual service
errors. An unavailable service produces a partial report; if every lookup fails,
the script exits with code 1. `--output-dir` changes the report folder.

DNS comes from [Google Public DNS](https://developers.google.com/speed/public-dns/docs/doh/json),
registration from [RDAP.org and registry RDAP services](https://about.rdap.org/),
and certificate names from [crt.sh](https://crt.sh/). These services receive the
queried domain. Certificate names can be historical or wildcard entries and do
not establish that a host is currently live. RDAP expects the registered domain;
subdomains may have no registration record. Public service availability and rate
limits affect results.
