const pricePerUnit = 800;
const quantityInput = document.querySelector('input[name="quantity"]');
const form = document.querySelector('#order-form');
const phoneInput = document.querySelector('input[name="phone"]');
const addressInput = document.querySelector('input[name="address"]');
const errorBox = document.querySelector('#form-errors');
const totalDisplay = document.querySelector('#total-display');

quantityInput.addEventListener('input', () => {
  const qty = parseInt(quantityInput.value) || 0;
  totalDisplay.textContent = `總價：NT$ ${(pricePerUnit * (qty || 1)).toLocaleString()}`;
});

function validatePhone(phone) {
  const c = phone.replace(/[\s\-]/g, '');
  if (/^09\d{8}$/.test(c) || /^0\d{8,9}$/.test(c)) return '';
  return '電話格式錯誤，請輸入手機 09xxxxxxxx 或正確市話';
}

function validateAddress(addr) {
  addr = addr.trim();
  if (addr.length < 10) return '地址太短，請填寫完整配送地址';
  if (!/[縣市]/.test(addr)) return '地址需包含縣或市';
  if (!/[路街道巷弄號樓]/.test(addr)) return '地址需包含路/街/巷/弄/號';
  return '';
}

function showErrors(msgs) {
  if (!msgs.length) { errorBox.hidden = true; errorBox.innerHTML = ''; return; }
  errorBox.hidden = false;
  errorBox.innerHTML = msgs.map(m => `<p>${m}</p>`).join('');
}

function validateForm() {
  const errors = [validatePhone(phoneInput.value), validateAddress(addressInput.value)].filter(Boolean);
  showErrors(errors);
  return !errors.length;
}

phoneInput.addEventListener('blur', validateForm);
addressInput.addEventListener('blur', validateForm);

form.addEventListener('submit', (e) => {
  if (!validateForm()) e.preventDefault();
});

// ===== 查詢訂單 =====
async function queryOrder() {
  const id = document.querySelector('#query-input').value.trim().toUpperCase();
  const resultBox = document.querySelector('#query-result');
  if (!id) { resultBox.hidden = false; resultBox.innerHTML = '<p style="color:#e53935">請輸入訂單編號</p>'; return; }

  try {
    const res = await fetch(`/api/order/${id}`);
    const data = await res.json();
    if (!data.found) {
      resultBox.hidden = false;
      resultBox.innerHTML = '<p style="color:#e53935">查無此訂單，請確認編號是否正確</p>';
      return;
    }
    const o = data.order;
    const statusText = o.status === 'awaiting_payment'
      ? '<span class="status-waiting">待付款</span>'
      : '<span class="status-done">已完成</span>';
    resultBox.hidden = false;
    resultBox.innerHTML = `
      <div class="q-row"><span class="q-key">訂單編號</span><span class="q-val">${o.order_id}</span></div>
      <div class="q-row"><span class="q-key">收件人</span><span class="q-val">${o.name}</span></div>
      <div class="q-row"><span class="q-key">電話</span><span class="q-val">${o.phone}</span></div>
      <div class="q-row"><span class="q-key">地址</span><span class="q-val">${o.address}</span></div>
      <div class="q-row"><span class="q-key">數量</span><span class="q-val">${o.quantity} 瓶</span></div>
      <div class="q-row"><span class="q-key">金額</span><span class="q-val">NT$ ${o.total_price.toLocaleString()}</span></div>
      <div class="q-row"><span class="q-key">狀態</span><span class="q-val">${statusText}</span></div>
      <div class="q-row"><span class="q-key">下單時間</span><span class="q-val">${o.created_at}</span></div>
    `;
  } catch {
    resultBox.hidden = false;
    resultBox.innerHTML = '<p style="color:#e53935">查詢失敗，請稍後再試</p>';
  }
}

document.querySelector('#query-input').addEventListener('keydown', (e) => {
  if (e.key === 'Enter') queryOrder();
});

// ===== 客服（純前端）=====
const FAQ = {
  '運費': '全台宅配免運費，下單後 3～5 個工作天送達。',
  '配送': '全台宅配免運費，下單後 3～5 個工作天送達。',
  '退貨': '收到商品 7 天內，未開封可申請退貨，請聯絡客服協助處理。',
  '退款': '退貨審核通過後，款項將於 7 個工作天內退回原匯款帳戶。',
  '付款': '下單後依訂單頁面顯示的銀行帳號匯款，備註填訂單編號即可。',
  '匯款': '下單後依訂單頁面顯示的銀行帳號匯款，備註填訂單編號即可。',
  '價格': `每瓶 ${pricePerUnit} 元，多瓶依數量計算。`,
  '成分': '含胺基酸系界面活性劑，溫和不刺激，適合一般及混合性肌膚。',
  '你好': '您好！有什麼可以幫您的嗎？',
  '您好': '您好！有什麼可以幫您的嗎？',
};
const DEFAULT_REPLY = '可詢問：運費、付款、退貨、價格、成分，或點選下方快捷。';

function getReply(msg) {
  for (const [k, v] of Object.entries(FAQ)) if (msg.includes(k)) return v;
  return DEFAULT_REPLY;
}

const chatToggle = document.querySelector('#chat-toggle');
const chatPanel = document.querySelector('#chat-panel');
const chatClose = document.querySelector('#chat-close');
const chatMessages = document.querySelector('#chat-messages');
const chatForm = document.querySelector('#chat-form');
const chatInput = document.querySelector('#chat-input');

function addMsg(text, type) {
  const div = document.createElement('div');
  div.className = `chat-msg ${type}`;
  div.textContent = text;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendMsg(msg) {
  if (!msg.trim()) return;
  addMsg(msg, 'user');
  chatInput.value = '';
  setTimeout(() => addMsg(getReply(msg), 'bot'), 250);
}

chatToggle.addEventListener('click', () => { chatPanel.hidden = false; });
chatClose.addEventListener('click', () => { chatPanel.hidden = true; });
chatForm.addEventListener('submit', (e) => { e.preventDefault(); sendMsg(chatInput.value); });
document.querySelectorAll('.chat-quick button').forEach(btn => {
  btn.addEventListener('click', () => sendMsg(btn.dataset.question));
});
