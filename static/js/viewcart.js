async function loadCart() {
    const token = localStorage.getItem("access_token");

    if (!token) {
        window.location.replace("/login");
        return;
    }

    const response = await fetch("/api/cart/view", {
        headers: {
            "Authorization": "Bearer " + token
        }
    });

    if (!response.ok) {
        alert("Failed to load cart");
        return;
    }
    
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

    const token = localStorage.getItem("access_token");

    const res = await fetch(`/api/cart/item/${itemId}?quantity=${newQty}`, {
    method: "PATCH",
    headers: {
        "Authorization": "Bearer " + token
    }
});

    if (!res.ok) {
        alert("Failed to update quantity");
        return;
    }

    loadCart(); 
}
document.addEventListener("DOMContentLoaded", loadCart);
