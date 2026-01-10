document.getElementById("buy-btn").addEventListener("click", async function () {
    const productId = this.dataset.productId;
    const quantity = 1;

    const formData = new FormData();
    formData.append("product_id", productId);
    formData.append("quantity", quantity);

    const response = await fetch("/api/checkout/buy-now", {
        method: "POST",
        body: formData,
        credentials: "include"
    });

    if (response.status === 401) {
        window.location.href = "/login";
        return;
    }

    if (!response.ok) {
        const error = await response.json();
        alert(error.detail || "Buy now failed");
        return;
    }

    const data = await response.json();
    window.location.href = data.redirect_url;
});
