#!/usr/bin/env bash
# Install a screen edition onto an existing Kali system with a working display.
set -euo pipefail
APP=/opt/kali-touch-ui
SRC_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EDITION=7inch
if [ -f "$SRC_DIR/EDITION.json" ]; then
    EDITION=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["edition"])' "$SRC_DIR/EDITION.json")
fi
if [ "${1:-}" = --edition ]; then EDITION="${2:-}"; shift 2; fi
case "$EDITION" in 7inch|4inch|35inch) ;; *) echo 'Choose 7inch, 4inch or 35inch.' >&2; exit 1 ;; esac
[ "$#" = 0 ] || { echo 'Usage: sudo bash scripts/install.sh [--edition 7inch|4inch|35inch]' >&2; exit 1; }
[ "$(id -u)" = 0 ] || { echo 'Run with sudo.' >&2; exit 1; }
for tool in chromium python3 xdotool xrandr xprop xset curl flock; do
    command -v "$tool" >/dev/null || { echo "Missing dependency: $tool" >&2; exit 1; }
done
python3 -c 'import tkinter' || { echo 'Install python3-tk for the Social browser.' >&2; exit 1; }
# Keep the previous startup configuration outside the application checkout.
CONFIG_BACKUP="/var/backups/kali-touch-ui/startup-$(date +%Y%m%d-%H%M%S)"
install -d -m 0700 "$CONFIG_BACKUP"
python3 - "$CONFIG_BACKUP" <<'PYBACKUP'
from pathlib import Path
import shutil,sys
backup=Path(sys.argv[1])
for name in ['/etc/lightdm/lightdm.conf','/etc/lightdm/lightdm.conf.d/99-kali-touch.conf',
             '/etc/systemd/system/kali-touchui.service','/etc/systemd/system/touchui-entertainment.service',
             '/etc/kali-touch-ui/kiosk.conf','/etc/plymouth/plymouthd.conf',
             '/usr/local/bin/kali-touch-session','/usr/local/share/kali-touch/kiosk.sh',
             '/etc/xdg/autostart/kali-touch-kiosk.desktop',
             '/etc/xdg/autostart/kali-touch-kiosk.desktop.disabled',
             '/usr/share/xsessions/kali-touch.desktop']:
 p=Path(name)
 if p.is_file():
  target=backup/name.lstrip('/');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
theme=Path('/usr/share/plymouth/themes/darksec')
if theme.is_dir(): shutil.copytree(theme,backup/'usr/share/plymouth/themes/darksec',symlinks=True)
PYBACKUP
install -d -m 0755 "$APP" /etc/kali-touch-ui /usr/local/share/kali-touch
if [ "$SRC_DIR" != "$APP" ]; then
    if [ -f "$APP/backend/server.py" ]; then
        install -d -m 0700 /var/backups/kali-touch-ui
        BACKUP="/var/backups/kali-touch-ui/app-$(date +%Y%m%d-%H%M%S).tgz"
        ( umask 077; tar --exclude=.git -czf "$BACKUP" -C "$APP" . )
        echo "Backup: $BACKUP"
    fi
    cp -r "$SRC_DIR"/backend "$SRC_DIR"/web "$SRC_DIR"/scripts "$SRC_DIR"/plymouth "$SRC_DIR"/run.sh "$APP/"
fi
chmod +x "$APP/run.sh" "$APP/scripts/"*.sh "$APP/scripts/kali-touch-session"
install -d -o kali -g kali -m 0755 /home/kali/payloads
install -m 0644 "$APP/scripts/kali-touchui.service" /etc/systemd/system/
install -m 0644 "$APP/scripts/touchui-entertainment.service" /etc/systemd/system/
install -m 0755 "$APP/scripts/kali-touch-session" /usr/local/bin/kali-touch-session
install -m 0755 "$APP/scripts/kiosk.sh" /usr/local/share/kali-touch/kiosk.sh
install -m 0644 "$APP/scripts/kali-touch.desktop" /usr/share/xsessions/
# Use the dedicated session instead of launching another kiosk from XDG autostart.
if [ -f /etc/xdg/autostart/kali-touch-kiosk.desktop ]; then
    mv /etc/xdg/autostart/kali-touch-kiosk.desktop /etc/xdg/autostart/kali-touch-kiosk.desktop.disabled
fi
install -d /etc/lightdm/lightdm.conf.d
cat > /etc/lightdm/lightdm.conf.d/99-kali-touch.conf <<'CONF'
[Seat:*]
autologin-user=kali
autologin-user-timeout=0
autologin-session=kali-touch
display-setup-script=
CONF
# Existing main config has precedence over snippets. Only update our session keys.
python3 - <<'PY'
from pathlib import Path
p=Path('/etc/lightdm/lightdm.conf')
if p.exists():
 lines=p.read_text().splitlines();inside=False;out=[]
 for line in lines:
  if line.startswith('['): inside=line.strip() in ('[Seat:*]','[SeatDefaults]')
  if inside and line.split('=',1)[0].strip() in ('autologin-user','autologin-user-timeout','autologin-session'):
   key=line.split('=',1)[0].strip();line=key+'='+{'autologin-user':'kali','autologin-user-timeout':'0','autologin-session':'kali-touch'}[key]
  if inside and line.startswith('display-setup-script=') and 'kali-touch-rotate' in line:line='display-setup-script='
  out.append(line)
 p.write_text('\n'.join(out)+'\n')
PY
if command -v plymouth-set-default-theme >/dev/null; then
    install -d /usr/share/plymouth/themes/darksec
    install -m 0644 "$APP/plymouth/darksec/"*.png "$APP/plymouth/darksec/"*.script "$APP/plymouth/darksec/"*.plymouth /usr/share/plymouth/themes/darksec/
    plymouth-set-default-theme darksec
    update-initramfs -u -k "$(uname -r)"
    if grep -qw splash /proc/cmdline; then
        echo 'TOUCHUI_BOOT_SPLASH=system' > /etc/kali-touch-ui/kiosk.conf
    else
        echo 'TOUCHUI_BOOT_SPLASH=browser' > /etc/kali-touch-ui/kiosk.conf
    fi
else
    echo 'TOUCHUI_BOOT_SPLASH=browser' > /etc/kali-touch-ui/kiosk.conf
fi
printf 'TOUCHUI_EDITION=%s\n' "$EDITION" >> /etc/kali-touch-ui/kiosk.conf
systemctl daemon-reload
systemctl enable kali-touchui touchui-entertainment lightdm
# Start only missing services; preserve existing tool/browser sessions until reboot.
systemctl start kali-touchui touchui-entertainment
printf 'Installed. Reboot when ready to use the new Darksec startup.\n'
