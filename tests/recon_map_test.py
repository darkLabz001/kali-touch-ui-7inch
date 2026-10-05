"""Mock wireless observations; verify associations and target preparation without radio writes."""
from navigation_test import ROOT, fixtures
from playwright.sync_api import sync_playwright, expect


def main():
    ap = {'bssid': 'AA:BB:CC:DD:EE:01', 'essid': '<Lab WiFi>', 'channel': '6', 'power': '-48', 'privacy': 'WPA2'}
    client = {'station': '12:34:56:78:90:AB', 'bssid': ap['bssid'].lower(), 'power': '-61', 'packets': '10'}
    loose = {'station': '12:34:56:78:90:CD', 'bssid': '(not associated)', 'power': '-70', 'probes': 'Lab'}
    data = {'aps': [ap], 'clients': [client, loose]}
    writes, errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
        for width, height in [(800, 480), (1024, 600), (480, 320)]:
            page = browser.new_page(viewport={'width': width, 'height': height}, has_touch=True)
            page.on('pageerror', lambda e: errors.append(str(e)))
            def route(r):
                path = r.request.url.split('http://127.0.0.1:8080/', 1)[1].split('?')[0]
                if path.startswith('api/'):
                    if r.request.method == 'POST': writes.append(path)
                    result = {}
                    if path == 'api/tools': result = fixtures()
                    elif path == 'api/recon/start': result = {'ok': False, 'msg': 'Connect a USB WiFi adapter.'}
                    elif path == 'api/recon/data': result = data
                    elif path == 'api/recon/state': result = {'running': True, 'iface': 'wlan1mon'}
                    elif path == 'api/recon/log': result = {'log': ''}
                    r.fulfill(json=result)
                else: r.fulfill(path=str(ROOT / 'web' / (path or 'index.html')))
            page.route('http://127.0.0.1:8080/**', route)
            page.goto('http://127.0.0.1:8080/')
            page.locator('#boot-splash').evaluate('(e)=>e.remove()')
            page.evaluate('showRecon()')
            page.get_by_role('button', name='▶ SCAN ON', exact=True).tap()
            expect(page.locator('#recon-error')).to_have_text('Connect a USB WiFi adapter.')
            page.wait_for_timeout(3200)
            expect(page.locator('#recon-error')).to_have_text('Connect a USB WiFi adapter.')
            writes.clear()
            page.get_by_role('button', name='NETWORK MAP', exact=True).tap()
            expect(page.locator('.recon-branch')).to_have_count(1)
            expect(page.locator('.recon-leaves button')).to_have_count(1)
            expect(page.locator('.recon-loose button')).to_have_count(1)
            page.locator('.recon-leaves button').tap()
            expect(page.locator('#re-target')).to_contain_text(client['station'])
            page.wait_for_timeout(3200)
            expect(page.locator('.recon-leaves button')).to_have_attribute('aria-pressed', 'true')
            page.get_by_role('button', name='View access point', exact=True).tap()
            expect(page.locator('[data-recon-tab=aps]')).to_have_class('chip on')
            expect(page.locator('#re-target')).to_contain_text('<Lab WiFi>')
            page.get_by_role('button', name='NETWORK MAP', exact=True).tap()
            page.locator('.recon-loose button').tap()
            expect(page.locator('#re-target')).to_contain_text('not observed')
            expect(page.get_by_role('button', name='Open target controls', exact=True)).to_have_count(0)
            page.locator('.recon-leaves button').tap()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            page.screenshot(path=f'/tmp/recon-map-{width}x{height}.png', full_page=True)
            page.get_by_role('button', name='Open target controls', exact=True).tap()
            expect(page.locator('#deauth-bssid')).to_have_value(ap['bssid'])
            expect(page.locator('#deauth-ch')).to_have_value('6')
            expect(page.locator('#deauth-client')).to_have_value(client['station'])
            assert page.evaluate('reconTimer === null && !reconPageOpen')
            assert not writes, writes
            page.locator('#btn-back').tap()
            page.close()
        assert not errors, errors
        browser.close()
    print('PASS: associations, unassociated clients, selection refresh, literal names, prepared targets, no radio writes, 3 touch layouts')


if __name__ == '__main__': main()
