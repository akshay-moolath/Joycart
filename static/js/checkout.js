const orderId = window.location.pathname.split("/").pop();

async function getOrder() {
    const token = localStorage.getItem("access_token");
    if (!token) {
        window.location.href = "/login";
        return;
    }

    const res = await fetch(`/api/orders/${orderId}`, {
        headers: {
            "Authorization": "Bearer " + token
        }
    });

    const order = await res.json();
    const container = document.getElementById("items");
    container.innerHTML = `
        <p><b>Order ID:</b> ${order.id}</p>
        <p><b>Status:</b> ${order.status}</p>
        <p><b>Total:</b> ₹${order.amount}</p>
        <hr>
    `;
}


getOrder();

document.getElementById("pay-btn").addEventListener("click", async () => {
    const res = await fetch(`/api/payments?order_id=${orderId}`, {
        method: "POST"
    });


    if (!res.ok) {
        const errorData = await res.json();
        const errorType = errorData.detail;
        if (errorType === "Already Paid") {
        alert("Already Paid");
    }
    else{
        alert("Order Not Found");}
        
    return;
    }
    alert("Payment successful");
    window.location.href = `/payment-success/${orderId}`;
});

