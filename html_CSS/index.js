const pricePerUnit = 800;
const quantityInput = document.querySelector('input[name="quantity"]');
const form = document.querySelector('#order-form');
const phoneInput = document.querySelector('input[name="phone"]');
const addressInput = document.querySelector('input[name="address"]');
const errorBox = document.querySelector('#form-errors');

// 動態顯示總價
const totalPriceDisplay = document.createElement('p');
totalPriceDisplay.classList.add('total-price');
totalPriceDisplay.textContent = `總價：${pricePerUnit} 元`;
form.appendChild(totalPriceDisplay);

quantityInput.addEventListener('input', () => {
    const qty = parseInt(quantityInput.value) || 0;
    totalPriceDisplay.textContent = `總價：${pricePerUnit * qty} 元`;
});

function validatePhone(phone) {
    const cleaned = phone.replace(/[\s\-]/g, '');
    if (/^09\d{8}$/.test(cleaned)) return '';
    if (/^0\d{8,9}$/.test(cleaned)) return '';
    return '電話格式錯誤，請輸入手機 09xxxxxxxx 或正確市話';
}

function validateAddress(address) {
    const addr = address.trim();
    if (addr.length < 10) return '地址太短，請填寫完整配送地址';
    if (!/[縣市]/.test(addr)) return '地址需包含縣或市（例：台北市、新北市）';
    if (!/[路街道巷弄號樓]/.test(addr)) return '地址需包含路/街/巷/弄/號等詳細資訊';
    return '';
}

function showErrors(messages) {
    if (messages.length === 0) {
        errorBox.hidden = true;
        errorBox.innerHTML = '';
        return;
    }
    errorBox.hidden = false;
    errorBox.innerHTML = messages.map(msg => `<p>${msg}</p>`).join('');
}

function validateForm() {
    const errors = [];
    const phoneErr = validatePhone(phoneInput.value);
    const addressErr = validateAddress(addressInput.value);
    if (phoneErr) errors.push(phoneErr);
    if (addressErr) errors.push(addressErr);
    showErrors(errors);
    return errors.length === 0;
}

phoneInput.addEventListener('blur', validateForm);
addressInput.addEventListener('blur', validateForm);

form.addEventListener('submit', (e) => {
    if (!validateForm()) {
        e.preventDefault();
        return;
    }

    const qty = parseInt(quantityInput.value) || 0;
    const confirmOrder = confirm(`確定下單嗎？\n總價：${pricePerUnit * qty} 元\n\n下單後請依指示匯款至指定帳戶。`);
    if (!confirmOrder) {
        e.preventDefault();
    }
});

// 客服選單
const chatToggle = document.querySelector('#chat-toggle');
const chatPanel = document.querySelector('#chat-panel');
const chatClose = document.querySelector('#chat-close');
const chatMessages = document.querySelector('#chat-messages');
const chatForm = document.querySelector('#chat-form');
const chatInput = document.querySelector('#chat-input');
const quickButtons = document.querySelectorAll('.chat-quick button');

function addMessage(text, type) {
    const div = document.createElement('div');
    div.className = `chat-msg ${type}`;
    div.textContent = text;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendChatMessage(message) {
    if (!message.trim()) return;

    addMessage(message, 'user');
    chatInput.value = '';

    try {
        const res = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message }),
        });
        const data = await res.json();
        addMessage(data.reply, 'bot');
    } catch {
        addMessage('連線失敗，請確認後端已啟動（python app.py）。', 'bot');
    }
}

chatToggle.addEventListener('click', () => {
    chatPanel.hidden = false;
});

chatClose.addEventListener('click', () => {
    chatPanel.hidden = true;
});

chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    sendChatMessage(chatInput.value);
});

quickButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        sendChatMessage(btn.dataset.question);
    });
});
