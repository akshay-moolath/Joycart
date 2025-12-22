const orderId = window.location.pathname.split("/").pop();

async function getOrder() {
    const res = await fetch(`/api/orders/${orderId}`);

    if (res.status === 401) {
        
        window.location.href = "/login";
        return;
    }

    if (!res.ok) {
        alert("Order not found");
        return;
    }

    const order = await res.json();
    const container = document.getElementById("items");

    container.innerHTML = `
        <p><b>Order ID:</b> ${order.id}</p>
        <p><b>Status:</b> ${order.status}</p>
        <p><b>Total:</b> ₹${order.amount}</p>
        <hr>
    `;

    if (order.status === "PENDING") {
        container.innerHTML += `
            <button id="pay-btn">Pay Now</button>
        `;

        document
            .getElementById("pay-btn")
            .addEventListener("click", payNow);
    }
}

async function payNow() {
    const res = await fetch(`/payments?order_id=${orderId}`, {
        method: "POST"
    });

    if (res.status === 401) {
        window.location.href = "/login";
        return;
    }

    if (!res.ok) {
        const errorData = await res.json();
        alert(errorData.detail || "Payment failed");
        return;
    }

    window.location.href = `/payments/status/${orderId}`;
}

getOrder();
