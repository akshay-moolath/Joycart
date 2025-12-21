
async function loadProducts() {
    const res = await fetch("/api/products/page");
    const products = await res.json();

    const container = document.getElementById("products");

    let html = "";

products.forEach(p => {
    html += `
        <div class="card">
            <img src="${p.thumbnail}" alt="${p.title}">
            <h4>${p.title}</h4>
            <div class="price">₹${p.price}</div>
            <a href="/products/${p.id}">View</a>
        </div>
    `;
});

container.innerHTML = html;

}

loadProducts();
