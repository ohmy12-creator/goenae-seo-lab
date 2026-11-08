import os,sqlite3,csv,io,datetime,requests,hmac,hashlib,base64,time
from flask import Flask,request,redirect,render_template_string,Response,abort
from werkzeug.security import check_password_hash
A=Flask(__name__); DB=os.getenv('GOENAE_DB','goenae.db')

@A.before_request
def require_login():
    # Fail closed: never expose account data or API-triggering endpoints without credentials.
    user=os.getenv('GOENAE_APP_USER')
    pw_hash=os.getenv('GOENAE_APP_PASSWORD_HASH')
    if not user or not pw_hash:
        return Response('관리자 인증이 설정되지 않았습니다. 서버 환경변수를 확인하세요.',status=503)
    auth=request.authorization
    if not auth or not (hmac.compare_digest(auth.username or '',user) and check_password_hash(pw_hash,auth.password or '')):
        return Response('로그인이 필요합니다.',status=401,headers={'WWW-Authenticate':'Basic realm="goenae SEO LAB"'})

@A.after_request
def security_headers(resp):
    resp.headers['X-Content-Type-Options']='nosniff'
    resp.headers['X-Frame-Options']='DENY'
    resp.headers['Referrer-Policy']='no-referrer'
    resp.headers['Cache-Control']='no-store'
    resp.headers['Content-Security-Policy']="default-src 'self'; style-src 'unsafe-inline'"
    return resp

def conn():
 c=sqlite3.connect(DB,timeout=15);c.row_factory=sqlite3.Row;c.execute('CREATE TABLE IF NOT EXISTS keywords (keyword TEXT PRIMARY KEY, pc INTEGER, mobile INTEGER, category TEXT, notes TEXT, updated TEXT)');c.execute('CREATE TABLE IF NOT EXISTS ranks (keyword TEXT, rank INTEGER, checked TEXT, source TEXT, PRIMARY KEY(keyword,checked))');c.commit();return c
STYLE='''<style>*{box-sizing:border-box}body{margin:0;background:#f7f4f0;color:#302820;font:15px system-ui,-apple-system,sans-serif}header{background:#49352e;color:#fff;padding:24px max(20px,calc((100% - 1100px)/2))}header h1{margin:0;font-size:27px}header p{opacity:.8;margin:7px 0 0}.wrap{max-width:1100px;margin:25px auto;padding:0 15px}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.card,section{background:#fff;border:1px solid #e5ddd6;border-radius:14px;padding:20px;margin-bottom:15px}.card strong{display:block;font-size:26px;margin:8px 0}.muted{color:#776a60;font-size:13px}h2{font-size:18px;margin:0 0 15px}input,select,textarea{padding:11px;border:1px solid #d8cfc8;border-radius:8px;max-width:100%;font:inherit}button{background:#49352e;color:white;border:0;border-radius:8px;padding:11px 16px;cursor:pointer}form{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:10px 0}table{border-collapse:collapse;width:100%;min-width:650px}th,td{text-align:left;padding:12px;border-bottom:1px solid #eee}th{background:#f7f4f0} .scroll{overflow:auto}.tag{border-radius:20px;background:#f1e7d7;padding:5px 9px;font-size:12px}.alert{background:#fff5df;border:1px solid #ebd7a3;padding:13px;border-radius:10px;margin-bottom:15px}@media(max-width:700px){.cards{grid-template-columns:1fr}header{padding:22px}section{padding:15px}input{width:100%}}</style>'''
HTML='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>goenaé SEO LAB</title>'''+STYLE+'''</head><body><header><h1>goenaé SEO LAB</h1><p>펴나네 브라 · 키워드 검색량 및 자연검색 순위 관리</p></header><main class="wrap"><div class="alert"><b>데이터 상태:</b> 검색광고 API 연결 전에는 실제 검색량을 표시하지 않습니다. 자연검색 순위는 검증된 측정값만 입력하세요. 검색광고 API 데이터와 쇼핑 순위는 서로 다릅니다.</div><div class="cards"><div class="card"><span class="muted">등록 키워드</span><strong>{{ count }}</strong></div><div class="card"><span class="muted">검색량 확인된 키워드</span><strong>{{ measured }}</strong></div><div class="card"><span class="muted">최근 순위 기록</span><strong>{{ ranked }}</strong></div></div><section><h2>키워드 추가</h2><form method="post" action="/keyword"><input name="keyword" required placeholder="예: 처짐방지브라"><select name="category"><option>조사 전</option><option>상품명 후보</option><option>속성 후보</option><option>태그 후보</option><option>제외</option></select><input name="notes" placeholder="제품 적합성 메모"><button>추가</button></form><p class="muted">월간 검색량은 네이버 검색광고 API 연결 또는 출처가 확인된 CSV 업로드로 입력합니다.</p><form method="post" action="/csv" enctype="multipart/form-data"><input type="file" name="file" accept=".csv" required><button>검색량 CSV 업로드</button></form><p class="muted">CSV 열 이름: keyword, pc, mobile (선택: category, notes). UTF-8 인코딩 권장.</p></section><section><h2>검색광고 API로 검색량 조회</h2><form method="post" action="/api"><button>등록 키워드 조회 실행</button></form><p class="muted">서버 환경변수 NAVER_AD_API_KEY, NAVER_AD_SECRET_KEY, NAVER_AD_CUSTOMER_ID가 있어야 동작합니다. 비밀키를 이 웹페이지나 채팅에 입력하지 마세요.</p>{% if message %}<p class="alert">{{message}}</p>{% endif %}</section><section><h2>키워드 목록</h2><div class="scroll"><table><thead><tr><th>키워드</th><th>PC 월간</th><th>모바일 월간</th><th>합계</th><th>분류</th><th>최근 순위</th><th>순위 입력</th></tr></thead><tbody>{% for k in rows %}<tr><td><b>{{k['keyword']}}</b><div class="muted">{{k['notes'] or ''}}</div></td><td>{{ k['pc'] if k['pc'] is not none else '미확인' }}</td><td>{{ k['mobile'] if k['mobile'] is not none else '미확인' }}</td><td>{{ (k['pc']+k['mobile']) if k['pc'] is not none and k['mobile'] is not none else '미확인' }}</td><td><span class="tag">{{k['category']}}</span></td><td>{{ k['rank'] if k['rank'] is not none else '미측정' }}</td><td><form method="post" action="/rank"><input type="hidden" name="keyword" value="{{k['keyword']}}"><input type="number" name="rank" min="1" placeholder="순위" style="width:90px" required><button>기록</button></form></td></tr>{% endfor %}</tbody></table></div></section><section><h2>순위 변화 기록</h2><div class="scroll"><table><thead><tr><th>측정 시각</th><th>키워드</th><th>순위</th><th>측정 방식</th></tr></thead><tbody>{% for r in history %}<tr><td>{{r['checked']}}</td><td>{{r['keyword']}}</td><td>{{r['rank']}}</td><td>{{r['source']}}</td></tr>{% endfor %}</tbody></table></div><form action="/export"><button>전체 데이터 CSV 내보내기</button></form></section><p class="muted">이 앱은 로컬/자체 호스팅용 1차 버전입니다. 외부 공개 배포 전 인증·HTTPS·백업을 구성해야 합니다.</p></main></body></html>'''
@A.get('/')
def home():
 c=conn();rows=c.execute('SELECT k.*, (SELECT rank FROM ranks r WHERE r.keyword=k.keyword ORDER BY checked DESC LIMIT 1) rank FROM keywords k ORDER BY COALESCE(k.mobile,-1) DESC,k.keyword').fetchall();history=c.execute('SELECT * FROM ranks ORDER BY checked DESC LIMIT 30').fetchall();message=request.args.get('msg','');return render_template_string(HTML,rows=rows,history=history,count=len(rows),measured=sum(x['mobile'] is not None for x in rows),ranked=len(history),message=message)
@A.post('/keyword')
def add():
 k=request.form.get('keyword','').strip()[:100];c=conn();
 if k:c.execute('INSERT INTO keywords(keyword,category,notes,updated) VALUES(?,?,?,?) ON CONFLICT(keyword) DO UPDATE SET category=excluded.category,notes=excluded.notes', (k,request.form.get('category','조사 전'),request.form.get('notes',''),datetime.date.today().isoformat()));c.commit()
 return redirect('/')
@A.post('/rank')
def rank():
 k=request.form.get('keyword','');raw=request.form.get('rank','0');r=int(raw) if raw.isdigit() else 0
 if r>0:
  c=conn();c.execute('INSERT OR REPLACE INTO ranks VALUES(?,?,?,?)',(k,r,datetime.datetime.now().isoformat(timespec='seconds'),'수동 입력 / 미검증'));c.commit()
 return redirect('/')
@A.post('/csv')
def csvup():
 f=request.files.get('file');
 if not f:return redirect('/?msg=CSV 파일을 선택하세요')
 if request.content_length and request.content_length>2_000_000:return Response('CSV 파일은 2MB 이하만 지원합니다.',status=413)
 try:
  data=f.read().decode('utf-8-sig');reader=csv.DictReader(io.StringIO(data));c=conn();n=0
  for row in reader:
   k=(row.get('keyword') or '').strip()
   if not k:continue
   pc=int(row['pc']) if (row.get('pc') or '').strip().isdigit() else None;mobile=int(row['mobile']) if (row.get('mobile') or '').strip().isdigit() else None
   c.execute('INSERT INTO keywords(keyword,pc,mobile,category,notes,updated) VALUES(?,?,?,?,?,?) ON CONFLICT(keyword) DO UPDATE SET pc=excluded.pc,mobile=excluded.mobile,updated=excluded.updated',(k,pc,mobile,row.get('category') or '조사 전',row.get('notes') or '',datetime.date.today().isoformat()));n+=1
  c.commit();return redirect('/?msg='+str(n)+'개 키워드 가져옴')
 except Exception as e:return redirect('/?msg=CSV 형식을 확인하세요')
@A.post('/api')
def api():
 key=os.getenv('NAVER_AD_API_KEY');secret=os.getenv('NAVER_AD_SECRET_KEY');customer=os.getenv('NAVER_AD_CUSTOMER_ID')
 if not all((key,secret,customer)):return redirect('/?msg=API 인증정보가 서버에 설정되지 않았습니다')
 c=conn();keywords=[r['keyword'] for r in c.execute('SELECT keyword FROM keywords').fetchall()]
 if not keywords:return redirect('/?msg=먼저 키워드를 추가하세요')
 try:
  count=0
  for i in range(0,len(keywords),5):
   ts=str(int(time.time()*1000));method='GET';uri='/keywordstool';sig=base64.b64encode(hmac.new(secret.encode(),f'{ts}.{method}.{uri}'.encode(),hashlib.sha256).digest()).decode()
   res=requests.get('https://api.searchad.naver.com'+uri,params={'hintKeywords':','.join(keywords[i:i+5]),'showDetail':'1'},headers={'X-Timestamp':ts,'X-API-KEY':key,'X-Customer':customer,'X-Signature':sig},timeout=15);res.raise_for_status()
   for x in res.json().get('keywordList',[]):
    kw=x.get('relKeyword','');pc=x.get('monthlyPcQcCnt');mo=x.get('monthlyMobileQcCnt');pc=int(pc) if isinstance(pc,int) or str(pc).isdigit() else None;mo=int(mo) if isinstance(mo,int) or str(mo).isdigit() else None
    if kw in keywords:
     c.execute('UPDATE keywords SET pc=?,mobile=?,updated=? WHERE keyword=?',(pc,mo,datetime.date.today().isoformat(),kw));count+=1
  c.commit();return redirect('/?msg='+str(count)+'개 키워드 검색량 업데이트')
 except requests.HTTPError as e:return redirect('/?msg=API 응답 오류: '+str(e.response.status_code))
 except Exception:return redirect('/?msg=API 요청에 실패했습니다. 서버 설정과 네트워크를 확인하세요')
@A.get('/export')
def export():
 c=conn();out=io.StringIO();w=csv.writer(out);w.writerow(['keyword','pc','mobile','category','notes','updated']);w.writerows(c.execute('SELECT keyword,pc,mobile,category,notes,updated FROM keywords'));return Response('\ufeff'+out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment;filename=goenae_keywords.csv'})
def initialize():
 c=conn()
 for k in ['처짐방지브라','빅사이즈브라','편한브라','넓은어깨끈브라','풀컵브라','노와이어브라','보정브라']:
  c.execute('INSERT OR IGNORE INTO keywords(keyword,category,notes,updated) VALUES(?,?,?,?)',(k,'조사 전','제품 적합성 확인 필요',datetime.date.today().isoformat()))
 c.commit();c.close()

initialize()
if __name__=='__main__':
 A.run(host='127.0.0.1',port=int(os.getenv('PORT','5000')),debug=False)
