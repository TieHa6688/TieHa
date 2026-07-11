from flask import Flask, request, send_from_directory, jsonify
import json, os, re, uuid
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

ORDER_FILE = os.path.join(BASE_DIR, 'orders.json')
REVENUE_FILE = os.path.join(BASE_DIR, 'merchant_revenue.json')
PRICE_PER_UNIT = 800

MERCHANT_ACCOUNT = {
    "bank": "國泰世華銀行",
    "account_number": "0138123456789",
    "account_name": "王小明",
}

PAGE_STYLE = """
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif;
  background: #f7f7f5; color: #111; min-height: 100vh;
  display: flex; align-items: flex-start; justify-content: center;
  padding: 60px 16px 100px;
}
.card {
  background: #fff; border-radius: 18px; padding: 44px 40px;
  max-width: 500px; width: 100%; box-shadow: 0 4px 28px rgba(0,0,0,0.08);
}
.label { font-size: 11px; font-weight: 700; letter-spacing: 0.2em; text-transform: uppercase; color: #aaa; margin-bottom: 10px; }
h2 { font-size: 26px; font-weight: 800; margin-bottom: 28px; letter-spacing: -0.02em; }
.row { display: flex; justify-content: space-between; padding: 11px 0; border-bottom: 1px solid #f0f0f0; font-size: 15px; }
.row:last-of-type { border-bottom: none; }
.key { color: #aaa; }
.val { font-weight: 600; }
.amount { font-size: 32px; font-weight: 900; margin: 28px 0 8px; letter-spacing: -0.02em; }
.section-title { font-size: 11px; font-weight: 700; letter-spacing: 0.15em; text-transform: uppercase; color: #aaa; margin: 32px 0 14px; }
.bank-box { background: #f7f7f5; border-radius: 12px; padding: 18px 22px; }
.bank-box .row { border-bottom: 1px solid #eee; }
.highlight { font-weight: 800; font-size: 17px; }
.back-btn {
  display: block; width: 100%; margin-top: 32px; padding: 16px;
  background: #111; color: #fff; border: none; border-radius: 12px;
  font-size: 16px; font-weight: 700; text-align: center; text-decoration: none; cursor: pointer;
}
.back-btn:hover { background: #333; }
.error-label { color: #e53935; }
.msg { font-size: 16px; color: #666; margin: 16px 0 28px; line-height: 1.65; }
</style>
"""

def validate_phone(phone):
    c = re.sub(r'[\s\-]', '', phone.strip())
    if re.match(r'^09\d{8}$', c): return True, c
    if re.match(r'^0\d{8,9}$', c): return True, c
    return False, "電話格式錯誤，請輸入手機 09xxxxxxxx 或正確市話"

def validate_address(address):
    a = address.strip()
    if len(a) < 10: return False, "地址太短，請填寫完整配送地址"
    if not re.search(r'[縣市]', a): return False, "地址需包含縣或市"
    if not re.search(r'[路街道巷弄號樓]', a): return False, "地址需包含路/街/巷/弄/號"
    return True, a

def load_orders():
    if not os.path.exists(ORDER_FILE): return []
    with open(ORDER_FILE, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return []

def save_orders(orders):
    with open(ORDER_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=4)

def add_revenue(amount, order_id):
    rev = {"total": 0, "orders": []}
    if os.path.exists(REVENUE_FILE):
        with open(REVENUE_FILE, 'r', encoding='utf-8') as f:
            try: rev = json.load(f)
            except: pass
    rev["total"] = rev.get("total", 0) + amount
    rev["orders"].append({"order_id": order_id, "amount": amount, "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    with open(REVENUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(rev, f, ensure_ascii=False, indent=4)

def error_page(msg):
    return f"""<!DOCTYPE html><html lang="zh-TW"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>下單失敗</title>{PAGE_STYLE}</head><body>
<div class="card">
  <p class="label error-label">下單失敗</p>
  <h2>出了點問題</h2>
  <p class="msg">{msg}</p>
  <a href="/" class="back-btn">返回重新填寫</a>
</div></body></html>""", 400

@app.route('/')
def index(): return send_from_directory(BASE_DIR, 'haha.html')

@app.route('/style.css')
def style_css(): return send_from_directory(BASE_DIR, 'style.css')

@app.route('/index.js')
def index_js(): return send_from_directory(BASE_DIR, 'index.js')

@app.route('/734088491_1768729317884247_3017759108073552811_n.jpg')
def product_image(): return send_from_directory(BASE_DIR, '734088491_1768729317884247_3017759108073552811_n.jpg')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    return jsonify({"reply": "可詢問：運費、付款、退貨、價格、成分。"})

@app.route('/api/order/<order_id>', methods=['GET'])
def query_order(order_id):
    orders = load_orders()
    for o in orders:
        if o.get('order_id') == order_id.upper():
            return jsonify({"found": True, "order": o})
    return jsonify({"found": False})

@app.route('/order', methods=['POST'])
def handle_order():
    name = (request.form.get('name') or '').strip()
    phone = (request.form.get('phone') or '').strip()
    address = (request.form.get('address') or '').strip()
    quantity = request.form.get('quantity')

    if not all([name, phone, address, quantity]):
        return error_page("資料填寫不完整，請確認所有欄位都已填寫。")

    ok, phone_r = validate_phone(phone)
    if not ok: return error_page(phone_r)

    ok, addr_r = validate_address(address)
    if not ok: return error_page(addr_r)

    try:
        qty = int(quantity)
        if qty < 1: raise ValueError
    except ValueError:
        return error_page("數量必須為 1 以上的整數。")

    total = qty * PRICE_PER_UNIT
    oid = uuid.uuid4().hex[:8].upper()

    orders = load_orders()
    orders.append({
        "order_id": oid, "name": name, "phone": phone_r,
        "address": addr_r, "quantity": qty, "total_price": total,
        "status": "awaiting_payment",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    save_orders(orders)
    add_revenue(total, oid)

    b = MERCHANT_ACCOUNT
    return f"""<!DOCTYPE html><html lang="zh-TW"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>下單成功</title>{PAGE_STYLE}</head><body>
<div class="card">
  <p class="label">訂單確認</p>
  <h2>下單成功 🎉</h2>
  <div class="bank-box" style="margin-bottom:0">
    <div class="row"><span class="key">訂單編號</span><span class="val">{oid}</span></div>
    <div class="row"><span class="key">收件人</span><span class="val">{name}</span></div>
    <div class="row"><span class="key">電話</span><span class="val">{phone_r}</span></div>
    <div class="row"><span class="key">地址</span><span class="val">{addr_r}</span></div>
    <div class="row"><span class="key">數量</span><span class="val">{qty} 瓶</span></div>
  </div>
  <div class="amount">NT$ {total:,}</div>
  <p class="section-title">請匯款至以下帳戶</p>
  <div class="bank-box">
    <div class="row"><span class="key">銀行</span><span class="val">{b['bank']}</span></div>
    <div class="row"><span class="key">帳號</span><span class="val highlight">{b['account_number']}</span></div>
    <div class="row"><span class="key">戶名</span><span class="val">{b['account_name']}</span></div>
    <div class="row"><span class="key">金額</span><span class="val highlight">NT$ {total:,}</span></div>
    <div class="row"><span class="key">備註</span><span class="val highlight">{oid}</span></div>
  </div>
  <a href="/" class="back-btn">返回首頁</a>
</div></body></html>"""

if __name__ == '__main__':
    app.run(debug=True)
