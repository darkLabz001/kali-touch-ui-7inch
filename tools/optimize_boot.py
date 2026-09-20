#!/usr/bin/env python3
"""Remove obsolete ifupdown Ethernet boot waits after verifying NetworkManager WiFi.
This never disconnects/reconfigures the active WiFi connection or reboots.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def command(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def eligible(main_text, files, routes):
    if not routes or any(not r.get('dev', '').startswith(('wlan', 'wl')) for r in routes):
        raise ValueError('The current default route must use WiFi; Ethernet changes refused.')
    expected = {'source-directory /etc/network/interfaces.d', 'auto lo', 'iface lo inet loopback'}
    main = {' '.join(l.split()) for l in main_text.splitlines() if l.strip() and not l.lstrip().startswith('#')}
    if not main <= expected:
        raise ValueError('Custom /etc/network/interfaces entries need manual review.')
    if set(files) != {'eth0'}:
        raise ValueError('Expected only the legacy eth0 file; custom interfaces need manual review.')
    allowed = {'auto eth0', 'allow-hotplug eth0', 'iface eth0 inet dhcp'}
    lines = {' '.join(l.split()) for l in files['eth0'].splitlines() if l.strip() and not l.lstrip().startswith('#')}
    if not lines <= allowed or 'iface eth0 inet dhcp' not in lines:
        raise ValueError('Custom Ethernet configuration found; refusing to change it.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');args=p.parse_args()
    root=Path('/etc/network/interfaces.d')
    files={f.name:f.read_text() for f in root.iterdir() if f.is_file()}
    routes=json.loads(command('ip','-j','route','show','default'))
    routes+=json.loads(command('ip','-j','-6','route','show','default'))
    eligible(Path('/etc/network/interfaces').read_text(),files,routes)
    # A connected cable can carry local traffic even without a default route.
    carrier=Path('/sys/class/net/eth0/carrier')
    try:
        connected=carrier.read_text().strip()=='1'
    except OSError:
        connected=True
    if connected:raise SystemExit('Ethernet carrier is present or unknown; refusing to change it.')
    if command('systemctl','is-active','NetworkManager')!='active':raise SystemExit('NetworkManager is not active.')
    for route in routes:
        state=command('nmcli','-g','GENERAL.STATE','device','show',route['dev'])
        if not state.startswith('100'):raise SystemExit('WiFi is not connected through NetworkManager.')
    print('Eligible: NetworkManager owns the active WiFi; eth0 is a legacy DHCP-only interface.')
    if not args.apply:
        print('Run with sudo and --apply to back up eth0 and disable its boot wait.');return
    if os.geteuid()!=0:raise SystemExit('Run --apply with sudo.')
    backup=Path('/var/backups/kali-touch-ui')/('network-'+time.strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True,mode=0o700)
    shutil.copy2(root/'eth0',backup/'eth0')
    (backup/'rollback.sh').write_text('#!/bin/sh\nset -e\ncp "$(dirname "$0")/eth0" /etc/network/interfaces.d/eth0\nsystemctl enable networking.service\nnmcli general reload conf\n')
    (backup/'rollback.sh').chmod(0o700)
    # Disable only future startup; the current session and WiFi remain active.
    command('systemctl','disable','networking.service')
    (root/'eth0').unlink()
    command('nmcli','general','reload','conf')
    print('Saved rollback:',backup/'rollback.sh')
    print('Legacy DHCP wait removed for the next boot. No reboot was issued.')


if __name__=='__main__':main()
