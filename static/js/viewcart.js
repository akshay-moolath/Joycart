async function loadCart() {
    const response = await fetch("/api/cart/view", {
        credentials: "include"
    });
    const data = await response.json();

    const container = document.getElementById("cart-items");
    const totalEl = document.getElementById("cart-total");
    const orderBtn = document.getElementById("order-btn");

    
    container.innerHTML = "";

    if (!data.items || data.items.length === 0) {
        container.innerHTML = "<p>Your cart is empty.</p>";
        totalEl.innerText = "0.00";
        orderBtn.disabled = true;
        return;
    }

    orderBtn.disabled = false;

   
    let itemsHtml = "";
    data.items.forEach(item => {
            itemsHtml += `
                        <div class="item">
                            <a href="/products/${item.product_id}">
                            <img src="${item.thumbnail}" alt="">
                            </a>

                            <div class="item-details">
                            <h4>${item.title}</h4>

                            <p>Price: ₹ ${item.price}</p>

                            <p>
                                Quantity:
                                <span class="qty-control">
                                <button onclick="changeQty(${item.id}, ${item.quantity - 1})">−</button>
                                <span>${item.quantity}</span>
                                <button onclick="changeQty(${item.id}, ${item.quantity + 1})">+</button>
                                </span>
                            </p>

                            <p><b>Subtotal:</b> ₹ ${item.subtotal}</p>
                            <button
                                class="link-btn danger remove-btn"
                                onclick="openRemoveConfirm(${item.id})"
                            >
                                REMOVE
                            </button>
                            </div>
                        </div>
                        `;
    });

    
    container.innerHTML = itemsHtml;

    
    totalEl.innerText = data.total.toFixed(2);
}
async function changeQty(itemId, newQty) {
    if (newQty < 1) {
    return;
    }

   
    const res = await fetch(`/api/cart/item/${itemId}?quantity=${newQty}`, {
    method: "PATCH",
    credentials: "include"
});

    if (!res.ok) {
        alert("Failed to update quantity");
        return;
    }

    loadCart(); 
}


async function removeItem(itemId) {

    

    const res = await fetch(`/api/cart/item/${itemId}`, {
    method: "DELETE",
    credentials: "include"
});

    if (!res.ok) {
        alert("Failed to delete item");
        return;
    }

    loadCart(); 
}
async function checkout() {
    

    const res = await fetch("/api/checkout/start", {
    method: "POST",
    credentials: "include"
});
    if (!res.ok) {
        alert("Placing Order Failed");
        return;
    }

    const data = await res.json();

    window.location.href = data.redirect_url;
}
let removeItemId = null;

function openRemoveConfirm(itemId) {
  removeItemId = itemId;
  document.getElementById("remove-confirm").classList.remove("hidden");
}

function closeRemoveConfirm() {
  removeItemId = null;
  document.getElementById("remove-confirm").classList.add("hidden");
}

document.addEventListener("DOMContentLoaded", () => {
  loadCart();

  const confirmBtn = document.getElementById("confirm-remove-btn");
  if (confirmBtn) {
    confirmBtn.addEventListener("click", () => {
      if (removeItemId) {
        removeItem(removeItemId);
        closeRemoveConfirm();
      }
    });
  }
});


