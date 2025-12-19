document.getElementById("pay-btn").addEventListener("click", async () => {
    const res = await fetch(`/api/payments?order_id=${orderId}`, {
        method: "POST"
    });

    if (!res.ok) {
        alert("Payment failed");
        return;
    }

    alert("Payment successful");
    window.location.href = "/orders";
});
