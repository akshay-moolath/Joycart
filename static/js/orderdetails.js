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
    let itemHtml = `
        <div style="margin-bottom:10px; padding:10px; border:1px solid #ddd; border-radius:6px">
            <img src="${item.thumbnail}" width="100" alt="${item.title}">
            <p><b>${item.title}</b></p>
            <p><b>Price:</b> ₹${item.price}</p>
            <p><b>Qty:</b> ${item.quantity}</p>
            <p><b>Subtotal:</b> ₹${item.subtotal}</p>
            <p><b>Item Status:</b> ${item.status}</p>
            
    `;

    if (["PLACED", "ACCEPTED"].includes(item.status)) {
        itemHtml += `
            <button onclick="cancelItem(${item.item_id})">
                Cancel Item
            </button>
        `;
    }

    itemHtml += `</div>`;

    container.innerHTML += itemHtml;
});
const cancellableStatuses = ["PLACED", "ACCEPTED"];

const canCancelOrder = order.items.every(
    item => cancellableStatuses.includes(item.status)
);

if (canCancelOrder && order.status !== "CANCELLED") {
    container.innerHTML += `
        <hr>
        <button onclick="cancelOrder(${order.id})">
            Cancel Order
        </button><br><br>
        <a href="/">Home</a>
    `;
} else {
    container.innerHTML += `<a href="/">Home</a>`;
}

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
async function cancelItem(itemId) {
    const confirmCancel = confirm("Are you sure you want to cancel this item?");
    if (!confirmCancel) return;

    const res = await fetch(`/api/orders/item/${itemId}/cancel`, {
        method: "POST",
    });

    if (!res.ok) {
        const errorData = await res.json();
        alert(errorData.detail || "Unable to cancel item");
        return;
    }

    alert("Item cancelled successfully");
    window.location.reload();
}


loadOrder();