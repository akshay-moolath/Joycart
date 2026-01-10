

document.addEventListener("DOMContentLoaded", async function () {
  const btn = document.getElementById("add-to-cart-btn");
  if (!btn) return;

  const productId = btn.dataset.productId;


  try {
    const res = await fetch(`/cart/exist/${productId}`, {
      credentials: "include"
    });

    if (res.ok) {
      const data = await res.json();

      if (data.in_cart) {
        btn.textContent = "Added ✓";
        btn.disabled = true;
        btn.classList.add("btn-outline");
      }
    }
  } catch (err) {
    console.error("Failed to check cart status");
  }

  btn.addEventListener("click", async function () {
    const formData = new FormData();
    formData.append("product_id", productId);
    formData.append("quantity", 1);

    const response = await fetch("/api/cart/add", {
      method: "POST",
      body: formData,
      credentials: "include"
    });

    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }

    if (response.ok) {

      window.location.reload();
    } else {
      const error = await response.json();
      alert(error.detail || "Something went wrong");
    }
  });
});
