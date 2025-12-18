
document.getElementById("add-to-cart-btn").addEventListener("click", async function () {
    const productId = this.dataset.productId;
    const quantity = document.getElementById("qty").value;

    const token = localStorage.getItem("access_token");

    if (!token) {
        alert("Please login first");
        window.location.href = "/login";
        return;
    }

    const response = await fetch("/api/cart/add", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token
        },
        body: JSON.stringify({
            product_id: Number(productId),
            quantity: Number(quantity)
        })
    });

    if (response.ok) {
        alert("Added to cart ✅");
    } else {
        const error = await response.json();
        alert(error.detail || "Something went wrong");
    }
});

