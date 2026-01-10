
async function loadCartCount() {
  try {
    const res = await fetch("/cart/count");

    if (!res.ok) return;

    const data = await res.json();
    const badge = document.getElementById("cart-count");

    if (!badge) return;

    if (data.count > 0) {
      badge.textContent = data.count;
      badge.hidden = false;
    } else {
      badge.hidden = true;
    }
  } catch (err) {
    console.error("Cart count error");
  }
}

document.addEventListener("DOMContentLoaded", loadCartCount);
