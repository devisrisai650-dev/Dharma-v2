import sqlite3, os, io, secrets, html
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
import qrcode
DB=os.environ.get('DHARMA_DB','dharma.db')
ADMIN=os.environ.get('DHARMA_ADMIN_TOKEN') or secrets.token_urlsafe(24)
BASE=os.environ.get('DHARMA_BASE_URL','http://localhost:8000').rstrip('/')
items=[(f'{c} Pattu saree','Heritage',8000,'Silk','Dharmavaram') for c in ['Maroon','Bottle green','Mustard','Navy','Black']]+[(f'{c} soft silk saree','Daily',6500,'Silk','Dharmavaram') for c in ['Lavender','Peach','Sage']]+[(n,'Studio',4200,'Silk','Dharmavaram') for n in ['Pattu skirt co-ord','Pattu shirt co-ord','Pattu relaxed co-ord']]+[(n,'Daily',5500,'Silk','Dharmavaram') for n in ['Pre-pleated saree','Ready-to-wear saree']]+[(n,'Essentials',1200,'Cotton','Mangalagiri') for n in ['Striped stole','Classic stole']]+[(n,c,p,'Cotton',v) for n,c,p,v in [('Oversized shirt','Street',1499,'Mangalagiri'),('Patchwork bomber','Street',2999,'Chirala'),('Wide-leg trousers','Street',1899,'Mangalagiri'),('Midi dress','Studio',2299,'Venkatagiri'),('Tote bag','Essentials',699,'Chirala'),('Laptop sleeve','Essentials',999,'Mangalagiri'),('Cushion cover','Living',699,'Chirala'),('Table runner','Living',899,'Mangalagiri')]]+[('Pattu blazer','Studio',4499,'Silk','Dharmavaram'),('Pattu scrunchies','Essentials',249,'Silk','Dharmavaram')]
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init():
 with db() as c:
  c.executescript('CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY,name TEXT,category TEXT,price INTEGER,material TEXT,origin TEXT); CREATE TABLE IF NOT EXISTS units(id TEXT PRIMARY KEY,product INTEGER,status TEXT DEFAULT "pending",evidence TEXT DEFAULT "",payment INTEGER DEFAULT 0); CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY,unit TEXT UNIQUE,price INTEGER,welfare INTEGER); CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,unit TEXT,event TEXT,created TEXT DEFAULT CURRENT_TIMESTAMP);')
  for i,p in enumerate(items,1):
   c.execute('INSERT OR IGNORE INTO products VALUES(?,?,?,?,?,?)',(i,*p)); c.execute('INSERT OR IGNORE INTO units(id,product) VALUES(?,?)',(f'DH-{i:05}',i))
def e(s): return html.escape(str(s),quote=True)
def page(title,body):
 return f'''<!doctype html><html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} | Dharma</title><style>*{{box-sizing:border-box}}body{{margin:0;background:#f7f3e9;color:#203e33;font:16px system-ui}}header{{background:#193e32;color:#fff4da;padding:24px;text-align:center}}header b{{font:36px Georgia;letter-spacing:8px}}nav{{display:flex;justify-content:center;gap:20px;flex-wrap:wrap;margin-top:15px}}nav a{{color:white}}main{{max-width:1100px;margin:auto;padding:24px}}h1,h2{{font-family:Georgia}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:16px}}article,section{{background:white;border:1px solid #ded8c8;border-radius:12px;padding:18px;margin-bottom:12px}}.fabric{{height:90px;background:repeating-linear-gradient(45deg,#416e60 0 5px,#517e70 5px 8px);border-bottom:12px solid #c9a45f;border-radius:5px}}a{{color:#215a45}}button,.button{{background:#245743;color:white;border:0;border-radius:6px;padding:10px;display:inline-block;text-decoration:none;cursor:pointer}}input,select,textarea{{padding:10px;max-width:100%;margin:6px;border:1px solid #aaa;border-radius:5px}}small{{color:#59675e}}footer{{text-align:center;padding:20px}}img{{max-width:100%}}</style><header><b>DHARMA</b><div>From Loom to Life</div><nav><a href="/">Shop</a><a href="/verify">Verify</a><a href="/stories">Stories</a><a href="/impact">Impact</a><a href="/admin">Admin</a></nav></header><main>{body}</main><footer>Demonstration only · fictional records · no real payments or official certification</footer></html>'''
STORIES={1:'Preserving the craft of traditional silk weaving.',16:'Traditional cotton fabric meets contemporary streetwear.',25:'Giving silk offcuts a second life.'}
class Handler(BaseHTTPRequestHandler):
 def send(self,body,status=200,kind='text/html; charset=utf-8'):
  if isinstance(body,str): body=body.encode()
  self.send_response(status); self.send_header('Content-Type',kind); self.send_header('Content-Length',str(len(body))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(body)
 def do_GET(self):
  u=urlparse(self.path); q=parse_qs(u.query); path=u.path
  with db() as c:
   if path=='/':
    cat=q.get('category',[''])[0]; search=q.get('q',[''])[0]; rows=c.execute('SELECT * FROM products WHERE (?="" OR category=?) AND name LIKE ?',(cat,cat,'%'+search+'%')).fetchall(); body='<h1>Made by hands. Made for today.</h1><form><input name="q" placeholder="Search products" value="'+e(search)+'"><select name="category"><option value="">All collections</option>'+''.join(f'<option {"selected" if x==cat else ""}>{x}</option>' for x in ['Heritage','Daily','Street','Studio','Essentials','Living'])+'</select><button>Filter</button></form><div class="grid">'+''.join(f'<article><div class="fabric"></div><h2>{e(p["name"])}</h2><small>{e(p["origin"])} · {e(p["material"])}</small><p>₹{p["price"]:,}</p><a class="button" href="/passport/DH-{p["id"]:05}">View passport</a></article>' for p in rows)+'</div>'
   elif path=='/verify': body='<h1>Verify a product</h1><form action="/lookup"><input required name="id" placeholder="DH-00001"><button>Verify</button></form><p>Try DH-00001. A matching record alone does not prove physical authenticity.</p>'
   elif path=='/lookup': return self.redirect('/passport/'+q.get('id',[''])[0].strip().upper()) if q.get('id',[''])[0].strip().upper().isalnum() or q.get('id',[''])[0].strip().upper().startswith('DH-') else self.send(page('Invalid','Invalid ID'),400)
   elif path.startswith('/passport/') or path.startswith('/qr/'):
    uid=path.split('/')[-1]; p=c.execute('SELECT units.*,products.* FROM units JOIN products ON product=products.id WHERE units.id=?',(uid,)).fetchone()
    if not p:return self.send(page('Not found','<h1>No matching passport</h1>'),404)
    if path.startswith('/qr/'):
     b=io.BytesIO(); qrcode.make(BASE+'/passport/'+uid).save(b,format='PNG'); return self.send(b.getvalue(),kind='image/png')
    body=f'<h1>{e(p["name"])}</h1><section><h2>Digital product passport</h2><p>{e(uid)} · {e(p["status"])}</p><p>Origin: {e(p["origin"])} | Material: {e(p["material"])}</p><p>Proposed handloom fabric; official Handloom Mark: not validated. Silk Mark: {"not validated" if p["material"]=="Silk" else "not applicable"}.</p><p>Illustrative weaver payment: ₹{p["payment"]:,}</p><img width="160" src="/qr/{uid}" alt="Product QR"><p><a href="/qr/{uid}">Open QR label</a></p></section>'
    if p['product'] in STORIES: body+=f'<section><h2>Behind the loom</h2>{e(STORIES[p["product"]])} (editorial concept)</section>'
    if p['status']=='reviewed' and not c.execute('SELECT 1 FROM orders WHERE unit=?',(uid,)).fetchone():body+=f'<form method="post" action="/order"><input type="hidden" name="id" value="{uid}"><button>Place demo order · ₹{p["price"]}</button></form>'
   elif path=='/stories': body='<h1>Behind the loom</h1>'+''.join(f'<article><h2>{e(items[i-1][0])}</h2><p>{e(s)} Editorial concept; real interviews pending.</p><a href="/passport/DH-{i:05}">Passport</a></article>' for i,s in STORIES.items())
   elif path=='/impact':
    a=c.execute('SELECT COUNT(*),COALESCE(SUM(price),0),COALESCE(SUM(welfare),0) FROM orders').fetchone(); b=c.execute('SELECT SUM(payment) FROM units').fetchone()[0]; body=f'<h1>Demo impact ledger</h1><section>Orders: {a[0]}<p>Sales: ₹{a[1]}</p><p>Education allocation: ₹{a[2]}</p><p>Recorded artisan remuneration: ₹{b}</p></section>'
   elif path=='/admin':body='<h1>Internal review</h1><section><form method="post" action="/review"><label>Admin token <input type="password" name="token" required></label><br><label>Unit ID <input name="id" required placeholder="DH-00001"></label><br><label>Evidence reference <input name="evidence" required></label><br><label>Demo artisan payment <input name="payment" type="number" min="0" required></label><br><select name="status"><option>reviewed</option><option>pending</option><option>revoked</option></select><button>Save review</button></form><p>Internal review is not official certification.</p></section>'
   else:return self.send(page('Not found','Not found'),404)
  self.send(page('Dharma',body))
 def redirect(self,path):
  self.send_response(303);self.send_header('Location',path);self.end_headers()
 def do_POST(self):
  try:
   n=int(self.headers.get('Content-Length','0')); assert 0<n<16000; f={k:v[0] for k,v in parse_qs(self.rfile.read(n).decode()).items()}; uid=f['id']
   with db() as c:
    if self.path=='/review':
     if not secrets.compare_digest(f.get('token',''),ADMIN):return self.send(page('Denied','Invalid admin token'),403)
     assert f['status'] in ['reviewed','pending','revoked'] and f['evidence'].strip() and int(f['payment'])>=0
     assert c.execute('UPDATE units SET status=?,evidence=?,payment=? WHERE id=?',(f['status'],f['evidence'],int(f['payment']),uid)).rowcount==1
     c.execute('INSERT INTO audit(unit,event) VALUES(?,?)',(uid,f['status']))
    elif self.path=='/order':
     p=c.execute('SELECT price,name FROM products JOIN units ON products.id=units.product WHERE units.id=? AND status="reviewed"',(uid,)).fetchone(); assert p
     c.execute('INSERT INTO orders(unit,price,welfare) VALUES(?,?,?)',(uid,p['price'],100 if 'saree' in p['name'].lower() else 0))
    else: return self.send(page('Not found','Not found'),404)
   self.redirect('/passport/'+uid)
  except (ValueError,KeyError,AssertionError,sqlite3.IntegrityError):self.send(page('Invalid','Invalid request or unit already ordered.'),400)
if __name__=='__main__':
 init(); print('Admin token:',ADMIN,flush=True); print(BASE,flush=True); ThreadingHTTPServer(('127.0.0.1',8000),Handler).serve_forever()
