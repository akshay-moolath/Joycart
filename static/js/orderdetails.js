async function loadOrder() {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/login";
        return;
    }
    const orderId = window.location.pathname.split("/").pop();

    const res = await fetch(`/api/orders/${orderId}`, {
        headers: {
            "Authorization": "Bearer " + token
        }
    });

    const order = await res.json();
    const container = document.getElementById("order");

    container.innerHTML = `
        <p><b>Order ID:</b> ${order.id}</p>
        <p><b>Status:</b> ${order.status}</p>
        <p><b>Total:</b> ₹${order.amount}</p>
        <hr>
    `;

    order.items.forEach(item => {
        container.innerHTML += `
            <div style="margin-bottom:10px">
                <p>${item.title}</p>
                <p>Price: ₹${item.price}</p>
                <p>Qty: ${item.quantity}</p>
                <p><b>Subtotal:</b> ₹${item.subtotal}</p>
            </div>
        `;
    });
if (order.status === "PENDING") {
        container.innerHTML += `
            <hr>
            <button onclick="goToCheckout(${order.id})">
                Proceed to Checkout
            </button>
        `;
    }
}

function goToCheckout(orderId) {
    window.location.href = `/checkout/${orderId}`;
}

loadOrder();