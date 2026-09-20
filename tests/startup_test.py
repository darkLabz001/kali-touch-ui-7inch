"""Splash plays once, follows actual readiness, and retries a late backend."""
from navigation_test import ROOT, fixtures
from playwright.sync_api import sync_playwright, expect


def main():
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  for handoff in (False,True):
   page=browser.new_page(viewport={'width':800,'height':480});attempts=0;pending=[];errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.add_init_script('window.EventSource=class {close(){}};')
   def route(r):
    nonlocal attempts
    path=r.request.url.split('http://touch.test',1)[1].split('?')[0]
    if path=='/api/tools':
     attempts+=1
     r.fulfill(status=503 if attempts==1 else 200,json={} if attempts==1 else fixtures())
    elif path=='/api/wordlists':pending.append(r) # Slow optional data must not delay Home.
    elif path.startswith('/api/'):r.fulfill(json={})
    else:r.fulfill(path=str(ROOT/'web'/('index.html' if path=='/' else path.lstrip('/'))))
   page.route('http://touch.test/**',route)
   page.goto('http://touch.test/'+('?splash=handoff' if handoff else ''))
   expect(page.locator('#ds-status')).to_contain_text('retrying')
   expect(page.locator('#boot-splash')).to_be_visible()
   expect(page.locator('.hub-card')).to_have_count(8,timeout=6000)
   expect(page.locator('#boot-splash')).to_have_count(0,timeout=1000)
   assert attempts==2 and pending
   for r in pending:r.fulfill(json={'wordlists':[]})
   assert not errors,errors
   page.close()
  browser.close()
 print('PASS: readiness-driven splash, handoff, late backend retry, wordlists do not block Home')

if __name__=='__main__':main()
