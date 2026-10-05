# Kali Touch UI — 7-inch, 4-inch and 3.5-inch editions

Touchscreen-first control frontend for **Kali Linux on a Raspberry Pi** with a **7″
800×480 DSI touchscreen**, with responsive support for 1024×600 landscape panels. Big touch targets, no keyboard needed, and
every action runs the real Kali tool under the hood and streams its output live.

Think of it as a launcher skin over your existing Kali tools: `nmap`, `masscan`,
`airodump-ng`, `hydra`, `sqlmap`, `nikto`, `enum4linux` … grouped into sections you
tap, with simple param fields and a live console.

The home screen groups tools by what you want to do:

| Group | Contents |
|---|---|
| Dashboard | Live traffic, system health and tracked sessions |
| Wireless | WiFite, WiFi apps and commands, Bluetooth |
| Network | Scanning, packet capture, utilities, Windows and SMB |
| OSINT | Domain OSINT, DNS research, theHarvester, file metadata |
| Web | Web tools and portal apps |
| Passwords | Login testing, hashes and wordlists |
| My Scripts | Your Python payload library |
| Entertainment | Offline games and social apps |

Tabs keep related tools together inside each group. Back returns to the group
and tab you came from. Settings and Terminal remain in the top bar.


## Architecture

- **Backend**: `backend/server.py` — Python **stdlib only** (no pip installs on the
  Pi). Serves the UI, maps tool → command, runs it with `sudo` when needed, and
  streams output to the browser over **Server-Sent Events (SSE)**.
  - Every user-supplied field is validated against `[A-Za-z0-9._:/:[]-]+`
    → command injection is rejected, not passed to a shell (no `sh -c` — commands
    are built token-by-token with `shlex.split`).
- **Frontend**: `web/` — single-page app, zero build step, touch-optimized (min
  target size ~46 px, big tap targets, no zoom scaling). Works in any browser,
  Chromium kiosk mode, or a "save to home screen" webapp.
- **Tool registry**: edit the `TOOLS` list at the top of `backend/server.py` to add
  tools/sections. Each entry is `(section, label, command_template, needs_root)`.

## Components

```
kali-touch-ui/
├── backend/server.py        # HTTP + SSE backend (stdlib only)
├── web/
│   ├── index.html
│   └── assets/
│       ├── style.css        # dark touch UI
│       └── app.js           # SPA: home → section → tool → live console
├── scripts/
│   ├── install.sh           # deploy to /opt, dedicated session, Plymouth
│   ├── kali-touchui.service # backend systemd service (starts on boot)
│   ├── kali-touch.desktop   # dedicated LightDM session
│   └── kiosk.sh             # waits for backend, opens Chromium fullscreen
├── run.sh                   # run in place (python3 + optional kiosk browser)
└── README.md
```

## 1. Flash Kali to the SD card

You already have the image at `../kali-image/kali-linux-2026.2-raspberry-pi-arm64.img.xz`.

```bash
# From your workstation — find the SD card FIRST (check dmesg, lsblk)
lsblk                        # confirm the device, e.g. /dev/sdX (do NOT guess)
xzcat kali-linux-2026.2-raspberry-pi-arm64.img.xz | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync
sync
```

> ⚠️ Double-check the device. `dd` to the wrong disk is irreversible.

### First-boot config

Re-mount the freshly-flashed card (or (un)plug it) and, if you want headless access:

```bash
# boot partition (FAT32), on your host:
mount /dev/sdX1 /mnt/boot
touch /mnt/boot/ssh                                   # enable SSH on boot
# if the Pi has no wired/known network, configure wireless in the rootfs too:
mount /dev/sdX2 /mnt/root
vi /mnt/root/etc/NetworkManager/system-connections/... # or use raspi-config later
```

Boot the Pi, then:

```bash
ssh kali@<pi-ip>            # default password: kali
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y chromium
```

## 2. Enable passwordless sudo for day-one automation

Most attack tools need root (`nmap -sS`, `masscan`, `airodump-ng`, `reaver` …). The
backend runs them via `sudo`, so give it a NOPASSWD entry (Kali's default already
allows this for the `kali` user in chroot-style setups, but be explicit):

```bash
echo "kali ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/kali-touchui
sudo chmod 440 /etc/sudoers.d/kali-touchui
```

## 3. Configure the 7-inch display

The verified device uses an **800×480 DSI touchscreen in landscape**. The kiosk
selects the attached DSI panel at its native resolution, makes it primary, and
maps its touch controller to that output. Legacy HDMI outputs are disabled during
the kiosk session so an old portrait configuration cannot enlarge the desktop.
The launcher sizes Chromium to the detected desktop instead of a fixed resolution.

Check the active display from the graphical session:

```bash
xrandr --current
xinput list
```

The expected output is a primary DSI display at `800x480+0+0`. For HDMI-only
installations, configure the display's native mode in the desktop first; the
kiosk uses the current desktop dimensions. The responsive layout also supports
1024×600 screens.

## 4. Install a screen edition

Download the matching application bundle from this repository's
[releases](https://github.com/darkLabz001/kali-touch-ui-7inch/releases).
These are **application bundles, not flashable SD-card images**. Start with Kali,
a working X11 display/touch driver, LightDM, and the `kali` user. The installer
requires Chromium, Python 3 with Tk, xdotool, xrandr, xprop, xset, curl and flock.
Onboard supplies the Social browser keyboard. It does not install panel drivers
or modify firmware overlays.

| Edition | Browser-tested screen sizes | Layout |
|---|---|---|
| `7inch` | 800×480, 1024×600 | Eight home groups; full touch keyboard |
| `4inch` | 800×480, 480×800 | Larger two-column home menu; scrolling pages |
| `35inch` | 480×320, 320×480 | Compact terminal and four-row landscape keyboard |

Physical size alone does not specify resolution or driver. The kiosk uses the
current display dimensions; configure HDMI/SPI display rotation and touch in
Kali before installing. The existing 7-inch DSI setup has been used on hardware,
but **this startup revision has not yet completed a hardware reboot test**.
The 4-inch and 3.5-inch editions have browser layout tests only. Release
candidates carry `hardware_verified: false` until that testing is complete.

Extract your downloaded archive, enter its directory and run:

```bash
sudo bash scripts/install.sh
# Or select an edition explicitly from a source checkout:
sudo bash scripts/install.sh --edition 35inch
```

The installer backs up existing application and startup configuration under
`/var/backups/kali-touch-ui/`, installs into `/opt/kali-touch-ui`, and selects a
single dedicated LightDM kiosk session. It disables the old duplicate XDG kiosk
autostart entry. It starts missing backend/helper services without restarting
active sessions. Reboot when ready to activate the new session and backend code.
Your `/home/kali/payloads`, Social login profile and screenshots remain outside
the application. Edition selection persists in `/etc/kali-touch-ui/kiosk.conf`.

### Darksec startup

The early Plymouth splash keeps the Darksec image and animated scanline. Its
refresh callback does not block boot. When system splash is configured, Chromium
hands off to the UI without replaying the browser boot animation. Installations
without Plymouth/splash retain the browser animation. Display setup runs once,
a process lock prevents duplicate kiosk owners, and the backend starts without
waiting for network-online. Home appears when its tools have loaded; optional
wordlists no longer delay it. A late backend retries automatically.

On the original device, the recorded baseline was **49.391 seconds to the system
startup target**, with the graphical session opening around **65 seconds**.
Legacy Ethernet DHCP took 28.574 seconds while WiFi was already managed by
NetworkManager. There is no measured after-change boot time yet.

The optional network optimizer is separate from installation. First inspect:

```bash
python3 tools/optimize_boot.py
```

It accepts only the known legacy DHCP-only `eth0` configuration, no Ethernet
carrier, and active NetworkManager WiFi default routes (including IPv6). It
refuses custom network configurations and Ethernet connections. If eligible:

```bash
sudo python3 tools/optimize_boot.py --apply
```

This backs up the Ethernet file, disables the legacy networking service for the
next boot, and reloads NetworkManager configuration. It does not disconnect WiFi
or reboot. Run the printed `rollback.sh` with sudo to restore that configuration.
Do not force eligibility checks on a different network setup.

To investigate boot timing after restarting:

```bash
systemd-analyze
systemd-analyze critical-chain graphical.target
systemctl status kali-touchui touchui-entertainment lightdm
```

To restore an earlier installation, restore the application archive and affected
startup configuration from the timestamped backup. Restore the earlier Plymouth
theme selection and run `sudo update-initramfs -u` before rebooting. To return to
a desktop, set LightDM's autologin session to an installed desktop from
`/usr/share/xsessions/` in both its main config and `99-kali-touch.conf`, or remove
the Kali Touch autologin settings and log in normally.

### Building the three release bundles

From a clean, committed checkout:

```bash
python3 tools/build_releases.py 0.3.0-rc1
(cd dist && sha256sum -c SHA256SUMS)
```

Each bundle includes an edition default and an `EDITION.json` identifying the
source commit, tested viewport sizes and hardware verification status. Only
tracked project files are packaged; local reports, browser sessions and device
backups are excluded. Separate release entries share one source repository.

## 5. Use it

1. Power on the Pi — the UI comes up fullscreen on the touchscreen automatically.
2. **Home** → tap a section → tap a tool.
3. Fill the fields that appear (URL / IP / BSSID / creds) — or leave them to use the
   stored defaults (e.g. reaver's BSSID).
4. **▶ RUN** starts the tool, **■ STOP** kills it, and output streams live below.
5. Back arrow returns to the section/home; hitting back also stops a running stream.

### Adding your own tools

Edit `TOOLS` in `backend/server.py`:

```python
("web", "Gobuster", "gobuster dir -u {target} -w /usr/share/wordlists/dirb/common.txt", False),
```

Supported placeholders: `{target}`, `{bssid}`, `{user}`, `{pass}`. The API discovers
which fields to render straight from the template. Restart the service to reload:
`sudo systemctl restart kali-touchui`.

## Security & legality

- **This is an attack surface on a stick.** Never run the UI's tools against networks
  you don't own / are not explicitly authorized to test.
- The backend binds `0.0.0.0:8080` with **no auth**, so anyone on your LAN can trigger
  tools. For field use, either restrict the Pi to a bring-your-own AP or add a
  reverse-proxy / firewall rule. Long term, add a token header check in `do_GET`/
  `do_POST` if it'll see untrusted networks.
- Commands are injection-safe (whitelist + `shlex.split`), but tools are powerful:
  `sudo` + NOPASSWD is the enabler, so treat the Pi like a root credential.

## Troubleshooting

| Symptom | Fix |
|---|---|
| UI not reachable | Is it a wifi client? `curl http://<ip>:8080/api/tools`. Check `systemctl status kali-touchui`. |
| Tool says "Unknown tool" | Section/label mismatch — restart service after editing `TOOLS`. |
| Tool missing → "command not found" | `sudo apt install <tool>`, it just wasn't in the registry check. |
| Touch offset / upside down | Double `display_rotate` is only video, not touch; calibrate touch separately (panel docs / `xinput-calibrator`). |
| `sudo` denies tool | Re-add the NOPASSWD entry from §2 (some upgrades rewrite sudoers). |
| Injection rejected | Fields accept only `[A-Za-z0-9._:/:[]-]` on purpose. Don't fight it — add a named param instead. |

## Detected 7-inch DSI display (800×480)

The kiosk now sources `scripts/display.sh` to select an attached DSI panel at
its native resolution, make it primary, and disable legacy HDMI outputs in the
kiosk session. It maps the DSI touch controller to that output and uses the actual
desktop dimensions for Chromium and the session background. This also handles
old 480×800 HDMI overrides without changing boot firmware configuration.

`web/assets/navigation.css` fits eight home groups into two rows at 800×480.
Long tool/settings pages scroll within the screen. `screen-fit.js` reserves the
actual touch keyboard height so input fields remain reachable.

On installations using `/usr/local/bin/kali-touch-session` or the fallback
`/usr/local/share/kali-touch/kiosk.sh`, update those installed copies alongside
`/opt/kali-touch-ui/scripts/`. Restart the graphical session to apply display
selection and browser sizing.

## Repository and Discord updates

This 7-inch edition lives at https://github.com/darkLabz001/kali-touch-ui-7inch.
Pushes are sent to Discord through a repository webhook configured under
**Settings → Webhooks**. The integration subscribes to `push` events across the
repository. Its private URL is stored in GitHub settings, never in source files.

To change the destination, edit the repository webhook using Discord's
[GitHub integration instructions](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks).
Push notifications report repository changes; they do not deploy updates to the Pi.

## User Python payloads

Open **My Scripts** to add and run your own Python scripts.
Copy `.py` files into `/home/kali/payloads` on the SD card, or choose **Add .py file**
in the UI. Refresh to discover files copied while the app is open.

Tap a script, optionally enter arguments, and press **RUN**. Output appears live;
**Send** supplies a line of input and **STOP** terminates the script and its child
processes. Scripts run as `kali`, with the payloads folder as their working folder.
The live folder is outside the application, so app updates preserve your scripts.
See [payloads/README.md](payloads/README.md) for details and a harmless example.

The included [`domain_osint.py`](payloads/domain_osint.py) payload collects public
DNS records, domain registration details, and certificate-transparency names.
Use `example.org` as its argument, or run it without arguments and enter a domain
with **Send**. It saves text and JSON reports in `/home/kali/payloads/reports/`.
See the [payload guide](payloads/README.md#domain-osint) for options and sources.

The included [`web_surface_mapper.py`](payloads/web_surface_mapper.py) payload
crawls a website, discovers JavaScript routes and forms, and checks common admin,
API and backup paths. Upload it through **My Scripts → Add .py file**, then use
the full target URL as its argument. It saves text and JSON reports and keeps
requests on the selected origin. See the
[Web Surface Mapper guide](payloads/README.md#web-surface-mapper) for limits and options.

## WiFite and the touch terminal

At 800×480, the terminal uses a compact layout with its input and control keys on
one row and the full keyboard below the output. The keyboard stays open while
using terminal controls; the keyboard button in the top bar shows or hides it.
Enter sends a response even when the input is empty, so prompts that ask you to
press Enter work. Ctrl+C and the arrow keys remain available beside the input.
Scroll up in the output to read earlier lines without new output pulling you
back to the bottom; scroll to the bottom to follow output again.

The browser regression check uses simulated terminal output and never launches
wireless operations:

```bash
python3 tests/terminal_layout_test.py  # requires Playwright and Chromium
```

## Menu navigation checks

`web/assets/navigation.js` groups the backend tool registry, terminal launchers,
and available custom apps into the same task categories. The existing runners
handle launches. The Domain OSINT shortcut appears when `domain_osint.py` is
installed in the payload library. Back navigation never relaunches a running tool.

```bash
python3 tests/navigation_test.py  # Playwright + Chromium; mocked tool operations
```

## Entertainment

Open **Entertainment → Games** for two offline games:

- **Snake**: swipe, use the large direction pad, or use arrow keys. Start, pause,
  resume and restart; your best score stays in this browser.
- **Memory Match**: find eight shuffled pairs, with move counting and a new-game
  button. Leaving either game stops its timers.

**Entertainment → Social** contains [Discord](https://discord.com/app),
[Reddit](https://www.reddit.com/) and [YouTube](https://www.youtube.com/).
Tap a card, then **Open** to launch its official site on the touchscreen. Internet
and any required account sign-in are handled by the website. A persistent top bar
provides **Back to Kali** and an Onboard **Keyboard** toggle. The separate browser
profile is stored in `~/.config/kali-touch-social`; signing in saves that session
on the device. Back closes that browser and restores the existing Kali window.

Social uses the separate `touchui-entertainment.service`, bound only to
`127.0.0.1:8082`. It accepts the three named sites only, from the local UI origin
on port 8080. It does not restart the main backend or run Kali tools. Chromium,
Python Tk, xdotool, xprop and Onboard must be installed in the graphical session.
The browser helper currently targets the device's X11 desktop.

For an existing installation, copy `backend/entertainment.py`, `backend/device.py`,
`scripts/social_browser.py` and the updated web assets, then install the service:

```bash
sudo install -m 0644 scripts/touchui-entertainment.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now touchui-entertainment
```

Games run without the helper or an Internet connection. Tests exercise full game
rounds and mock Social launches, so they never visit an account or send messages:

```bash
python3 tests/test_entertainment.py
python3 tests/entertainment_test.py  # Playwright + Chromium
```

## Live dashboard and quick controls

Open **Dashboard** on the home screen for receive/send traffic, CPU usage, memory,
storage, temperature, WiFi signal and tracked tool sessions. The graph builds a
60-second history from real interface byte counters, sampled about every two
seconds. It follows the default-route interface. There is no synthetic activity:
first samples show a dash, and a lost helper connection marks the view **STALE**.
Tracking covers terminal, Python payloads, Recon, capture and installed custom
app sessions; it does not claim to enumerate every Linux process.

**Swipe down from the top bar**, or tap **⌄**, to open quick controls:

- Brightness (10–100%, keeping the panel visible), volume and mute.
- WiFi settings, Home and Dashboard shortcuts.
- Keyboard show/hide for the current text field, preserving draft terminal input.
- Screenshot: closes the panel and saves the screen under
  `~/Pictures/KaliTouch/` on the device.
- Record screen / Stop recording: saves a silent MP4 under `~/Videos/KaliTouch/`.
  A red REC timer stays visible in the top bar; tap it to reopen the controls.
  Capture uses the full desktop at 15 fps, stops after two minutes or near 9 MiB,
  and finalizes the MP4 before enabling sharing. Requires FFmpeg with libx264,
  ffprobe, xrandr, and the active X11 desktop. At least 100 MiB free space is required.
- Send to Discord: uploads the latest finished recording only when tapped.
  Its filename and size appear below the buttons. Previously sent clips cannot
  be resent accidentally, and upload failures keep the local file for retry.

The device IP appears under **Settings → Device info**, rather than in the top
status line or Dashboard, so ordinary screen recordings do not show it there.
The recorder captures whatever you open, including Settings or terminal output.

To configure recording uploads, store the Discord webhook URL in
`~/.config/kali-touch-ui/discord-webhook` on the device, owned by the device user
with mode `0600`. The existing GitHub webhook URL is accepted: the recorder uses
its normal attachment endpoint without the `/github` suffix. The configuration
stays outside the source tree and is never returned to the browser. Do not put
the URL in this repository. Uploads use Discord's
[multipart webhook API](https://docs.discord.com/developers/resources/webhook#execute-webhook)
with delivery confirmation and mentions disabled. No recording is sent automatically.
Clips and the latest-recording metadata are private to the device user and
remain after restarting the helper service. The menu shares the latest completed
clip; earlier clips remain in `~/Videos/KaliTouch/`.

Swipe up on the panel heading, tap **Done**, or tap outside it to return.
Unavailable hardware controls are disabled. Brightness and audio changes apply
to the current device state; they are not startup presets. The audio control uses
PipeWire's current default output through `wpctl`.

Metrics and device controls share the existing local-only
`touchui-entertainment.service` on port 8082. They accept requests from the
local touchscreen UI on port 8080, with origin checks, bounded numeric inputs and
fixed commands. Brightness uses the existing passwordless sudo permission for
writing the detected backlight; no new sudoers rule is installed. Screenshot
files are private to the device user. No tool starts when opening the dashboard.
Remote browser visits retain the tool menus; hardware controls and detailed
metrics require opening the UI on the touchscreen.

The separate frontend files are `web/assets/dashboard.js` and `dashboard.css`.
Copy `backend/device.py`, `backend/recording.py`, and the updated `backend/entertainment.py` alongside them,
then restart only `touchui-entertainment` while the Social browser is closed.
The main Kali backend does not need to restart for this update.

```bash
python3 tests/test_device.py
python3 -m unittest discover -s tests -p test_recording.py
python3 tests/dashboard_test.py  # Playwright + Chromium; all controls mocked
```

## Recon network map and target actions

Open **Wireless → WiFi apps → Recon — PineAP**, start a scan, and select
**Network Map**. Branches connect observed access points to their associated
clients; these are radio observations, not physical locations or proof of a
current connection. Clients without an observed access point appear separately.
Band and security filters apply to access points in the map.

Tap a map node or a row in **Access Points** / **Clients** to view target actions.
**Copy address** copies its MAC address when browser clipboard access is available.
**View access point** opens a client's parent network. **Open target controls**
opens the existing Deauth Blaster with BSSID, channel, and optional client filled
in; opening the controls does not run it. Selection follows scan refreshes.
The map shows up to 40 access points and 12 clients per branch, with additional
observations available in the lists. Scanning requires a compatible wireless adapter.

```bash
python3 tests/recon_map_test.py  # Playwright + Chromium; mocked observations, no radio writes
```

## Update source

This edition checks and downloads updates from
`https://github.com/darkLabz001/kali-touch-ui-7inch.git`, branch `main`.
The update fetch uses that repository directly, even if an older installation's
`origin` still points at the original 4-inch repository. GitHub connection failures
are shown as failed checks. Updates restart both the backend and the local device
helper so dashboard controls load the updated code. An installation still running
the original repository needs a one-time migration before this updater fix applies.

Recon signal charts show the strongest three visible networks over a shared 60-second timeline. Tap a network label to isolate it; tap **Show strongest 3** to return. Missing or invalid signal readings leave gaps. Channel counts are shown as readable badges below the chart.

The default Recon **Live channels** view positions every observed network by its channel and signal strength, with separate 2.4 GHz / 5 GHz controls. Tap a marker or network card to select it and view client counts and target controls. Observations refresh every three seconds while Recon is open. **Signal history** remains available as a separate view.

## Update progress and failures

**Settings → OTA Update** shows checking, downloading, applying, verifying,
service setup, and restart stages. The download percentage comes from Git's
streamed output; the overall bar advances at completed stages. A successful start
is not treated as a successful update. Failures show their reason and offer Retry.
Status is stored under `~/.local/state/kali-touch-ui/update.json` on the device,
so restart completion and interrupted updates remain visible after reconnecting.
JavaScript validation requires Node.js (`sudo apt-get install nodejs`). Python
syntax checks do not write cache files into the installation. The updater installs
the device helper service before restarting it, including on older 4-inch installs.

WiFi status reports the connected radio independently of the USB scanning adapter.

### WiFi waterfall and arrivals

In Wireless → Recon, start a scan and select **Waterfall** to view 60 seconds of observed WiFi signal by channel. Both 2.4 and 5 GHz panels appear together by default; select a band to enlarge it; newer samples appear at the top, with stronger signals brighter. This uses access point observations refreshed every second, not spectrum energy or channel utilization. Observations older than 15 seconds leave gaps instead of appearing live.

**Device arrivals** establishes a baseline on the first scan snapshot, then highlights newly observed access points and clients. Tap an arrival to inspect it. Alerts are deduplicated for the scan session; restarting a scan resets the baseline. The feed retains the latest 30 arrivals and shows eight, with bounded scrolling on both screen sizes.
