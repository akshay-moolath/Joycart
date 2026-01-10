document.addEventListener("click", function (e) {
  const btn = e.target.closest("button[data-loading]");
  if (!btn) return;

  btn.disabled = true;
  const originalText = btn.innerText;
  btn.innerText = "Please wait...";

  setTimeout(() => {
    btn.disabled = false;
    btn.innerText = originalText;
  }, 1200);
});

const currentPath = window.location.pathname;
document.querySelectorAll(".nav-link").forEach(link => {
  if (link.getAttribute("href") === currentPath) {
    link.classList.add("active");
  }
});
