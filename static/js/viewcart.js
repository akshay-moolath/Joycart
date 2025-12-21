async function loadCart() {
    const response = await fetch("/api/cart/view", {
    credentials: "include"
});
    const data = await response.json();

  

    const container = document.getElementById("cart-items");
    const totalEl = document.getElementById("cart-total");

    container.innerHTML = "";

    if (data.items.length === 0) {
        container.innerHTML = "<p>Your cart is empty.</p>";
        totalEl.innerText = "0";
        return;
    }

    let total = 0;

    data.items.forEach(item => {
        total += item.subtotal;

        container.innerHTML += `
            <div class="item">
                <img src="${item.thumbnail}" alt="">
                <div>
                    <h4>${item.title}</h4>
                    <p>Price: ₹ ${item.price}</p>
                    <p>Quantity:<button onclick="changeQty(${item.id}, ${item.quantity - 1})">−</button>
                                <span style="margin: 0 10px">${item.quantity}</span>
                                <button onclick="changeQty(${item.id}, ${item.quantity + 1})">+</button>
                                </p>
                    <p>Remove Item:<button onclick="removeItem(${item.id})">X</button></p>

                    <p><b>Subtotal:</b> ₹ ${item.subtotal}</p>
                </div>
            </div>
        `;
    });

    totalEl.innerText = total.toFixed(2);
}
async function changeQty(itemId, newQty) {
    if (newQty < 1) {
        alert("Quantity cannot be less than 1");
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
    

    const res = await fetch("/api/checkout", {
    method: "POST",
    credentials: "include"
});
    if (!res.ok) {
        alert("Checkout failed");
        return;
    }

    const data = await res.json();

    alert(
        `Order placed!\nOrder ID: ${data.order_id}\nAmount: ₹${data.amount}`
    );
}

document.addEventListener("DOMContentLoaded", loadCart);
