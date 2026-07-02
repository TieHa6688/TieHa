from flask import Flask, request, send_from_directory, jsonify
import json
import os
import re
import uuid
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

ORDER_FILE = os.path.join(BASE_DIR, 'orders.json')
REVENUE_FILE = os.path.join(BASE_DIR, 'merchant_revenue.json')
PRICE_PER_UNIT = 800

# 收款帳戶（請改成你自己的銀行資料）
MERCHANT_ACCOUNT = {
    "bank": "國泰世華銀行",
    "account_number": "0138123456789",
    "account_name": "王小明",
}

# 客服自動回覆關鍵字
FAQ_REPLIES = {
    "運費": "全台宅配免運費，下單後 3～5 個工作天送達。",
    "配送": "全台宅配免運費，下單後 3～5 個工作天送達。",
    "退貨": "收到商品 7 天內，未開封可申請退貨，請聯絡客服協助處理。",
    "退款": "退貨審核通過後，款項將於 7 個工作天內退回原匯款帳戶。",
    "付款": f"請匯款至 {MERCHANT_ACCOUNT['bank']} 帳號 {MERCHANT_ACCOUNT['account_number']}（{MERCHANT_ACCOUNT['account_name']}），並在備註填寫訂單編號。",
    "匯款": f"請匯款至 {MERCHANT_ACCOUNT['bank']} 帳號 {MERCHANT_ACCOUNT['account_number']}（{MERCHANT_ACCOUNT['account_name']}），並在備註填寫訂單編號。",
    "價格": f"洗面乳每瓶 {PRICE_PER_UNIT} 元，購買越多總價依數量計算。",
    "成分": "本產品含胺基酸系界面活性劑，溫和不刺激，適合一般及混合性肌膚。",
    "客服": "您好！我是自動客服，可詢問：運費、付款、退貨、價格、成分等問題。",
    "你好": "您好！歡迎光臨洗面乳商店，有什麼可以幫您的嗎？",
    "您好": "您好！歡迎光臨洗面乳商店，有什麼可以幫您的嗎？",
}

DEFAULT_REPLY = "感謝您的訊息！您可以詢問：運費、付款方式、退貨、價格、成分，或點選下方快捷問題。"


def validate_phone(phone):
    cleaned = re.sub(r'[\s\-]', '', phone.strip())
    if re.match(r'^09\d{8}$', cleaned):
        return True, cleaned
    if re.match(r'^0\d{8,9}$', cleaned):
        return True, cleaned
    return False, "電話格式錯誤，請輸入手機 09xxxxxxxx 或正確市話"


def validate_address(address):
    addr = address.strip()
    if len(addr) < 10:
        return False, "地址太短，請填寫完整配送地址"
    if not re.search(r'[縣市]', addr):
        return False, "地址需包含縣或市（例：台北市、新北市、台中市）"
    if not re.search(r'[路街道巷弄號樓]', addr):
        return False, "地址需包含路/街/巷/弄/號等詳細資訊"
    return True, addr


def load_orders():
    if not os.path.exists(ORDER_FILE):
        return []
    with open(ORDER_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_orders(orders):
    with open(ORDER_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=4)


def add_merchant_revenue(amount, order_id):
    revenue = {"total": 0, "orders": []}
    if os.path.exists(REVENUE_FILE):
        with open(REVENUE_FILE, 'r', encoding='utf-8') as f:
            try:
                revenue = json.load(f)
            except json.JSONDecodeError:
                pass

    revenue["total"] = revenue.get("total", 0) + amount
    revenue["orders"].append({
        "order_id": order_id,
        "amount": amount,
        "paid_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

    with open(REVENUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(revenue, f, ensure_ascii=False, indent=4)


def error_page(message):
    return f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
      <meta charset="UTF-8">
      <title>下單失敗</title>
      <link rel="stylesheet" href="/style.css">
    </head>
    <body>
      <div class="container">
        <h2 class="error-title">❌ 下單失敗</h2>
        <p class="error-message">{message}</p>
        <a href="/" class="back-link">返回首頁重新填寫</a>
      </div>
    </body>
    </html>
    """, 400


def get_auto_reply(message):
    text = message.strip()
    for keyword, reply in FAQ_REPLIES.items():
        if keyword in text:
            return reply
    return DEFAULT_REPLY


@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'haha.html')


@app.route('/style.css')
def style_css():
    return send_from_directory(BASE_DIR, 'style.css')


@app.route('/index.js')
def index_js():
    return send_from_directory(BASE_DIR, 'index.js')


@app.route('/734088491_1768729317884247_3017759108073552811_n.jpg')
def product_image():
    return send_from_directory(BASE_DIR, '734088491_1768729317884247_3017759108073552811_n.jpg')


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get('message', '')
    return jsonify({"reply": get_auto_reply(message)})


@app.route('/order', methods=['POST'])
def handle_order():
    name = (request.form.get('name') or '').strip()
    phone = (request.form.get('phone') or '').strip()
    address = (request.form.get('address') or '').strip()
    quantity = request.form.get('quantity')

    if not all([name, phone, address, quantity]):
        return error_page("資料填寫不完整，請確認所有欄位都已填寫。")

    phone_ok, phone_result = validate_phone(phone)
    if not phone_ok:
        return error_page(phone_result)

    address_ok, address_result = validate_address(address)
    if not address_ok:
        return error_page(address_result)

    try:
        qty = int(quantity)
        if qty < 1:
            raise ValueError
    except ValueError:
        return error_page("數量必須為 1 以上的整數。")

    total_price = qty * PRICE_PER_UNIT
    order_id = uuid.uuid4().hex[:8].upper()

    order_data = {
        "order_id": order_id,
        "name": name,
        "phone": phone_result,
        "address": address_result,
        "quantity": qty,
        "total_price": total_price,
        "status": "awaiting_payment",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    orders = load_orders()
    orders.append(order_data)
    save_orders(orders)

    # 記錄待收款項（消費者匯款後即入帳）
    add_merchant_revenue(total_price, order_id)

    bank = MERCHANT_ACCOUNT
    return f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
      <meta charset="UTF-8">
      <title>下單成功</title>
      <link rel="stylesheet" href="/style.css">
    </head>
    <body>
      <div class="container success-page">
        <h2 class="success-title">🎉 下單成功！</h2>
        <p>訂單編號：<b>{order_id}</b></p>
        <p>收件人：{name}（{phone_result}）</p>
        <p>寄送地址：<b>{address_result}</b></p>
        <p>數量：{qty} 瓶</p>
        <p>訂單總金額：<span class="total-price">{total_price} 元</span></p>

        <div class="payment-box">
          <h3>💰 請完成匯款</h3>
          <p>請將款項匯至以下帳戶，我們收到款項後會立即安排出貨：</p>
          <ul class="payment-info">
            <li>銀行：{bank['bank']}</li>
            <li>帳號：{bank['account_number']}</li>
            <li>戶名：{bank['account_name']}</li>
            <li>匯款金額：<b>{total_price} 元</b></li>
            <li>備註請填：<b>{order_id}</b></li>
          </ul>
        </div>

        <a href="/" class="back-link">返回首頁</a>
      </div>
    </body>
    </html>
    """


if __name__ == '__main__':
    app.run(debug=True)
