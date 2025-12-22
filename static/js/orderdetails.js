async function loadOrder() {
    const orderId = window.location.pathname.split("/").pop();

    const res = await fetch(`/api/orders/${orderId}`, {});

    const order = await res.json();
    const container = document.getElementById("order");

    container.innerHTML = `
        <p><b>Order ID:</b> ${order.id}</p>
        <p><b>Status:</b> ${order.status}</p>

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
            <button onclick="cancelOrder(${order.id})">
                Cancel
            </button>
        `;
    }
else if (order.status === "PAID") {
        container.innerHTML += `
            <hr>
            <p><b>Payment ID:</b> ${order.payment}</p>
            <button onclick="Refund(${order.id})">
                Request Refund
            </button>
            
        `;
    }
else if (order.status === "REFUNDED"){
        container.innerHTML += `
        <hr>
        <p><b>Refund ID:</b> ${order.payment}</p>
        `;
    }
}

function goToCheckout(orderId) {
    window.location.href = `/checkout/${orderId}`;
}
async function cancelOrder(orderId) {
    
    const confirmCancel = confirm("Are you sure you want to cancel this order?");
    if (!confirmCancel) return;

    const res = await fetch(`/api/orders/${orderId}/cancel`, {
        method: "POST",});

    if (!res.ok) {
        const errorData = await res.json();
        alert(errorData.detail || "Unable to cancel order");
        return;
    }

    alert("Order cancelled successfully");

    window.location.reload();

}
async function Refund(orderId) {
    const confirmCancel = confirm("Are you sure you want to request refund for this order?");
    if (!confirmCancel) return;

    const res = await fetch(`/api/orders/${orderId}/refund`, {
        method: "POST",});

    if (!res.ok) {
        const errorData = await res.json();
        alert(errorData.detail || "Unable to provide refund ");
        return;
    }

    alert("Successfully Refunded");

    window.location.reload();

}


loadOrder();