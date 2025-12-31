async function loadOrder() {
    const orderId = window.location.pathname.split("/").pop();

    const res = await fetch(`/api/orders/${orderId}`, {});

    const order = await res.json();
    const container = document.getElementById("order");

    container.innerHTML = `
        <p><b>Order ID:</b> ${order.id}</p>
        <p><b>Order Status:</b> ${order.status}</p>
        <p><b>Total Amount :</b> ₹${order.amount}</p>
        <p><b>Payment Method :</b> ${order.payment
    ? `${order.payment.method}<br></br><b>Payment Status:</b> ${order.payment.status} <br></br><b>Payment ID:</b> ${
        order.payment.gateway_id ?? "N/A"
      }`
    : "Not applicable"
}</p>
        <hr>
        <h2>Order Items</h2>
    `;

    order.items.forEach(item => {
        container.innerHTML += `
            <div style="margin-bottom:10px">
                <p>${item.title}</p>
                <p><b>Price:</b> ₹${item.price}</p>
                <p><b>Qty:</b> ${item.quantity}</p>
                <p><b>Subtotal:</b> ₹${item.subtotal}</p>
            </div>
        `;
    });
if (order.status === "PLACED"|| order.status === "PAID") {
        container.innerHTML += `
            <hr>
            
            <button onclick="cancelOrder(${order.id})">
                Cancel Order
            </button><br></br>
        <a href="/">Home</a>
    `;
}
if (order.status === "CANCELLED") {
        container.innerHTML += `

        <a href="/">Home</a>
    `;
}
}
async function cancelOrder(orderId) {
    
    const confirmCancel = confirm("Are you sure you want to cancel this order?");
    if (!confirmCancel) return;

    const res = await fetch(`/api/orders/cancel/${orderId}`, {
        method: "POST",});

    if (!res.ok) {
        const errorData = await res.json();
        alert(errorData.detail || "Unable to cancel order");
        return;
    }

    alert("Order cancelled successfully");

    window.location.reload();

}


loadOrder();