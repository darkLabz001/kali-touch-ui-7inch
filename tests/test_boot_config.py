import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('optimizer',ROOT/'tools/optimize_boot.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class BootConfigTests(unittest.TestCase):
 def test_only_simple_ethernet_on_wifi_is_eligible(self):
  main='source-directory /etc/network/interfaces.d\nauto lo\niface lo inet loopback\n'
  files={'eth0':'auto eth0\nallow-hotplug eth0\niface eth0 inet dhcp\n'}
  module.eligible(main,files,[{'dev':'wlan0'}])
  for a,b,c in [(main,files,[{'dev':'eth0'}]),(main,files,[]),(main,dict(files,wlan0='iface wlan0 inet dhcp'),[{'dev':'wlan0'}]),(main,{'eth0':'iface eth0 inet static'},[{'dev':'wlan0'}]),(main+'auto wlan0',files,[{'dev':'wlan0'}])]:
   with self.assertRaises(ValueError):module.eligible(a,b,c)
 def test_backend_does_not_wait_for_network(self):
  text=(ROOT/'scripts/kali-touchui.service').read_text()
  self.assertNotIn('network-online.target',text)
 def test_startup_does_not_fetch_or_reset_git(self):
  for name in ['kali-touch-session','kiosk.sh']:
   text=(ROOT/'scripts'/name).read_text();self.assertNotIn('git reset',text);self.assertNotIn('git fetch',text)

if __name__=='__main__':unittest.main()
