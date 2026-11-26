import app, os, threading, re
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse
SHOP=os.getenv('DHARMA_SHOP_URL','http://localhost:8000').rstrip('/')
VERIFY=os.getenv('DHARMA_VERIFY_URL','http://localhost:8001').rstrip('/')
app.BASE=VERIFY
stories={1:('The Maroon Heritage','Silk','Dharmavaram',['Select silk yarn and document its supplier batch.','Prepare maroon warp and contrasting gold-toned border yarn.','Set the loom for the traditional border and body.','Handweave the body and decorative border; record loom sessions.','Inspect weave consistency, dimensions and finishing.','Attach the serialized passport and record artisan remuneration.']),16:('Cotton for a New Generation','Cotton','Mangalagiri',['Select cotton yarn suitable for breathable shirting.','Develop a sage and ivory stripe design with the artisan.','Prepare warp and weave the striped fabric.','Check shrinkage and cut an oversized shirt pattern.','Stitch, finish and inspect seams and measurements.','Attach the passport linking fabric and garment production.']),25:('A Second Life for Silk','Silk offcuts','Dharmavaram',['Collect documented silk offcuts from garment production.','Sort by colour, condition and usable dimensions.','Design a coordinated three-colour accessory set.','Cut strips and stitch fabric tubes around elastic.','Inspect seams, elasticity and finish.','Package the set and link it to source fabric batches.'])}
colors={1:'#792c42',16:'#78917d',25:'#b98a9e'}
def design(i):
 c=colors[i]; shape={1:'<path d="M80 20H205L235 110 215 265H65L95 110Z" fill="url(#fabric)"/><path d="M85 24L210 260M70 250H220" stroke="#d8b46a" stroke-width="12"/>',16:'<path d="M105 45L60 60 25 120 75 150 95 115V260H225V115L245 150 295 120 260 60 215 45 185 30 160 65 135 30Z" fill="url(#fabric)"/><path d="M160 65V260" stroke="#f5e8d0" stroke-width="3"/>',25:''.join(f'<circle cx="{x}" cy="{y}" r="45" fill="none" stroke="{col}" stroke-width="25" stroke-dasharray="9 2"/>' for x,y,col in [(105,90,c),(215,90,'#d6ad65'),(160,205,'#748e79')])}[i]
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 300" role="img" aria-label="Product concept sketch"><defs><pattern id="fabric" width="12" height="12" patternUnits="userSpaceOnUse"><rect width="12" height="12" fill="{c}"/><path d="M0 2H12M2 0V12" stroke="#fff" opacity=".2"/></pattern></defs><rect width="320" height="300" rx="12" fill="#f0e8d8"/>{shape}</svg>'
def scene(i,j):
 c=colors[i]; motifs=['<circle cx="105" cy="75" r="32"/><circle cx="190" cy="75" r="32"/><path d="M75 75H220M105 45V105M190 45V105"/>','<rect x="55" y="30" width="210" height="100"/><path d="M70 40V120M95 40V120M120 40V120M145 40V120M170 40V120M195 40V120M220 40V120M245 40V120"/>','<path d="M45 130V25H275V130M45 55H275M45 110H275M75 55V110M100 55V110M125 55V110M150 55V110M175 55V110M200 55V110M225 55V110M250 55V110"/>','<path d="M50 30H270V125H50Z M65 45L255 110M65 70L200 120M120 35L255 80"/>','<rect x="65" y="30" width="190" height="100"/><path d="M95 80L130 105 220 48"/>','<rect x="95" y="25" width="130" height="110" rx="8"/><path d="M115 50H205M115 70H205M115 90H180M115 110H195"/>']
 return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 160"><rect width="320" height="160" fill="#f0e8d8"/><g fill="none" stroke="{c}" stroke-width="5" stroke-linejoin="round">{motifs[j]}</g></svg>'
original=app.page
def page(title,body):
 body=re.sub(r'href="(/(?:passport|qr)/[^" ]+)"',lambda m:f'href="{VERIFY}{m[1]}"',body)
 return original(title,body)
app.page=page
class Site(app.Handler):
 def do_GET(self):
  path=urlparse(self.path).path; shop=self.server.server_port==8000
  if path.startswith('/media/'):
   name=path.split('/')[-1]
   if name not in ['1.mp4','16.mp4','25.mp4']: return self.send('Not found',404)
   return self.send((Path(__file__).parent/'media'/name).read_bytes(),kind='video/mp4')
  if path.startswith('/buy/') and shop:
   try:
    i=int(path.split('/')[-1]); assert 1<=i<=len(app.items)
   except (ValueError,AssertionError): return self.send('Not found',404)
   name,cat,price,material,origin=app.items[i-1]; uid=f'DH-{i:05}'
   with app.db() as c:
    unit=c.execute('SELECT status FROM units WHERE id=?',(uid,)).fetchone(); sold=c.execute('SELECT 1 FROM orders WHERE unit=?',(uid,)).fetchone()
   action=f'<form method="post" action="/order"><input type="hidden" name="id" value="{uid}"><button>Place demo order</button></form>' if unit['status']=='reviewed' and not sold else '<p>Demo ordering unavailable until internal review, or unit already sold.</p>'
   return self.send(page('Where to buy',f'<h1>{app.e(name)}</h1><section><h2>Where to buy</h2><p>Dharma online shop · ₹{price:,} (illustrative)</p>{action}<p>Proposed sourcing cluster: {app.e(origin)}, Andhra Pradesh. Physical retailer not confirmed.</p><a href="{VERIFY}/passport/{uid}">Check passport</a></section>'))
  if path.startswith('/design/'):
   try: i=int(path.split('/')[-1]); return self.send(design(i),kind='image/svg+xml')
   except (ValueError,KeyError):return self.send('Not found',404)
  if path=='/stories' and shop:
   return self.send(page('Stories','<h1>Behind the Loom</h1><p>Illustrated production plans, not documented artisan histories.</p><div class="grid">'+''.join(f'<article><img src="/design/{i}"><h2>{t[0]}</h2><a class="button" href="/story/{i}">Explore six stages</a></article>' for i,t in stories.items())+'</div>'))
  if path.startswith('/story/') and shop:
   try:i=int(path.split('/')[-1]); title,material,origin,steps=stories[i]
   except (ValueError,KeyError):return self.send('Not found',404)
   return self.send(page(title,f'<h1>{title}</h1><p>{origin} · {material} · proposed production journey</p><section><h2>Watch the journey</h2><video controls playsinline preload="metadata" width="640" style="max-width:100%" src="/media/{i}.mp4"></video><p>24-second silent illustrated animation. Not actual artisan footage.</p></section><img width="300" src="/design/{i}"><div class="grid">'+''.join(f'<article>{scene(i,j)}<h2>Stage {j+1}</h2><p>{app.e(s)}</p><small>Evidence and artisan interview pending</small></article>' for j,s in enumerate(steps))+f'</div><a class="button" href="{VERIFY}/passport/DH-{i:05}">Verify product</a> <a class="button" href="/buy/{i}">Where to buy</a>'))
  if shop and (path.startswith(('/passport/','/qr/')) or path in ['/verify','/lookup','/admin']):return self.redirect(VERIFY+self.path)
  if not shop and (path=='/stories' or path.startswith('/story/')):return self.redirect(SHOP+self.path)
  if not shop and path=='/':return self.redirect('/verify')
  return super().do_GET()
 def send(self,body,status=200,kind='text/html; charset=utf-8'):
  if isinstance(body,str) and kind.startswith('text/html'):
   shop=self.server.server_port==8000
   nav=f'<nav><a href="{SHOP}/">Shop</a><a href="{SHOP}/stories">Stories</a><a href="{VERIFY}/verify">Verify</a><a href="{VERIFY}/impact">Impact</a><a href="{VERIFY}/admin">Admin</a></nav>'
   body=re.sub(r'<nav>.*?</nav>',nav,body)
   if shop and urlparse(self.path).path=='/':
    for i in stories:
     name=app.e(app.items[i-1][0]); body=body.replace(f'<div class="fabric"></div><h2>{name}</h2>',f'<img src="/design/{i}" alt="Concept design"><h2>{name}</h2><p><a href="/story/{i}">Read storyboard</a></p>')
   if shop and urlparse(self.path).path=='/':
    body=re.sub(r'(href="[^" ]*/passport/DH-(\d+)"[^>]*>View passport</a>)',lambda m:m[1]+f' <a class="button" href="/buy/{int(m[2])}">Where to buy</a>',body)
   if not shop:
    match=re.fullmatch(r'/passport/DH-(\d+)',urlparse(self.path).path)
    if match and 1<=int(match[1])<=len(app.items):
     body=body.replace('</main>',f'<p><a class="button" href="{SHOP}/buy/{int(match[1])}">Where to buy</a></p></main>')
    if match and int(match[1]) in stories:
     i=int(match[1]);body=body.replace('</main>',f'<p><a class="button" href="{SHOP}/story/{i}">Full visual storyboard</a></p></main>')
  return super().send(body,status,kind)
if __name__=='__main__':
 app.init(); print('Admin token:',app.ADMIN,flush=True); print(SHOP,VERIFY,flush=True)
 a=ThreadingHTTPServer(('127.0.0.1',8000),Site); b=ThreadingHTTPServer(('127.0.0.1',8001),Site); threading.Thread(target=a.serve_forever,daemon=True).start(); b.serve_forever()
