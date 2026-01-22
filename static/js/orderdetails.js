

let cancelItemId = null;

document.addEventListener("DOMContentLoaded", () => {
  loadOrder();

  document
    .getElementById("close-cancel-btn")
    .addEventListener("click", closeCancelConfirm);

  document
    .getElementById("confirm-cancel-btn")
    .addEventListener("click", confirmCancel);
});

async function loadOrder() {
  const parts = window.location.pathname.split("/").filter(Boolean);
  const orderId = parts[1];
  const itemId = Number(parts[2]);

  const res = await fetch(`/api/orders/item/${itemId}`, {
    credentials: "include",
  });

  if (!res.ok) {
    alert("Failed to load order");
    return;
  }

    const data = await res.json();
    const item = data.item;

     
  document.getElementById("order-text").innerHTML = `
    <h4>${item.title}</h4>
    <p>Price: ₹${item.price}</p>
    <p>Quantity: ${item.quantity}</p>
    <p><strong>Total: ₹${item.subtotal}</strong></p>
    
  `;


  document.getElementById("order-thumb").innerHTML = `
    <a href = "/products/${item.product_id}"><img src="${item.thumbnail}" alt="${item.title}" loading="lazy">
</a>
  `;

    const order = data.order;
    const payment = data.payment;

  if (!item) {
    alert("Item not found");
    return;
  }




const statusClass = item.status.toLowerCase();

document.getElementById("order-status").innerHTML = `
  <div class="status-row">
    <span class="status-dot ${statusClass}"></span>
    Order ${item.status}
  </div>
`;

  const actions = document.getElementById("order-actions");
  actions.innerHTML = "";

  if (["PLACED", "CONFIRMED"].includes(item.status)) {
    actions.innerHTML = `
      <button class="btn btn-danger"
        onclick="openCancelConfirm(${item.item_id})">
        Cancel Order
      </button>
    `;
  }

if (item.status === "CANCELLED") {
  actions.innerHTML = `Refund Status : ${
    item.refund_status ?? "NO_REFUND_FOR_COD_ORDERS"
  }`;
}


  document.getElementById("delivery-box").innerHTML = `
    <p><b>${order.shipping_address.name}</b></p>
    <p>${order.shipping_address.address_line1}</p>
    <p>${order.shipping_address.city},
       ${order.shipping_address.state} -
       ${order.shipping_address.pincode}</p>
    <p>Phone: ${order.shipping_address.phone}</p>
  `;


  document.getElementById("payment-box").innerHTML = payment
    ? `
      <div class="price-row">
        <span>Payment Method</span>
        <span>${payment.method}</span>
      </div>
      <div class="price-row">
        <span>Status</span>
        <span>${payment.status}</span>
      </div>
      <div class="price-row total">
        <span>Total Paid</span>
        <span>₹${item.subtotal}</span>
      </div>
    `
    : `<p>Cash on Delivery</p>`;
}



function openCancelConfirm(itemId) {
  cancelItemId = itemId;
  document.getElementById("cancel-confirm-modal").classList.remove("hidden");
}

function closeCancelConfirm() {
  cancelItemId = null;
  document.getElementById("cancel-confirm-modal").classList.add("hidden");
}

async function confirmCancel() {
  if (!cancelItemId) return;

  const res = await fetch(`/api/orders/item/${cancelItemId}/cancel`, {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) {
    alert("Unable to cancel item");
    closeCancelConfirm();
    return;
  }

  window.location.reload();
}
