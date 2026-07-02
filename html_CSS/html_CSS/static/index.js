const pricePerUnit = 800;
const quantityInput = document.querySelector('input[name="quantity"]');
const form = document.querySelector('form');

// 動態顯示總價
const totalPriceDisplay = document.createElement('p');
totalPriceDisplay.classList.add("total-price");
totalPriceDisplay.textContent = `總價：${pricePerUnit} 元`;
form.appendChild(totalPriceDisplay);

// 當數量改變時更新總價
quantityInput.addEventListener('input', () => {
    let qty = parseInt(quantityInput.value) || 0;
    totalPriceDisplay.textContent = `總價：${pricePerUnit * qty} 元`;
});

// 提交前確認
form.addEventListener('submit', (e) => {
    let qty = parseInt(quantityInput.value) || 0;
    let confirmOrder = confirm(`確定下單嗎？\n總價：${pricePerUnit * qty} 元`);
    if (!confirmOrder) {
        e.preventDefault();
    }
});