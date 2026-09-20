"""Exercise the actual kiosk lock with fake display/browser commands."""
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import unittest
ROOT=Path(__file__).resolve().parents[1]


class KioskLockTests(unittest.TestCase):
 def test_two_launchers_start_one_browser(self):
  with tempfile.TemporaryDirectory() as name:
   root=Path(name);bin=root/'bin';bin.mkdir();runtime=root/'runtime';runtime.mkdir()
   for cmd in ['curl','xset','xprop']:
    p=bin/cmd;p.write_text('#!/bin/sh\nexit 0\n');p.chmod(0o755)
   p=bin/'xdotool';p.write_text('#!/bin/sh\nexit 1\n');p.chmod(0o755)
   p=bin/'chromium';p.write_text('#!/usr/bin/python3\nimport os,time\nwith open(os.environ["TEST_BROWSER_LOG"],"a") as f:f.write(str(os.getpid())+"\\n")\ntime.sleep(30)\n');p.chmod(0o755)
   display=root/'display.sh';display.write_text('TOUCHUI_WIDTH=800\nTOUCHUI_HEIGHT=480\n')
   script=root/'kiosk.sh';script.write_text((ROOT/'scripts/kiosk.sh').read_text().replace('/opt/kali-touch-ui/scripts/display.sh',str(display)).replace('/etc/kali-touch-ui/kiosk.conf',str(root/'absent.conf')))
   log=root/'browser.log';env=dict(os.environ,PATH=str(bin)+':/usr/bin:/bin',XDG_RUNTIME_DIR=str(runtime),TEST_BROWSER_LOG=str(log))
   first=subprocess.Popen(['bash',str(script)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
   try:
    for _ in range(50):
     if log.exists():break
     time.sleep(.05)
    self.assertTrue(log.exists())
    second=subprocess.run(['bash',str(script)],env=env,timeout=3,capture_output=True)
    self.assertEqual(second.returncode,0);self.assertEqual(len(log.read_text().splitlines()),1)
   finally:
    os.killpg(first.pid,signal.SIGTERM);first.wait(timeout=5)

if __name__=='__main__':unittest.main()
