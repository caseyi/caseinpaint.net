/* Case In Paint: small progressive enhancements. Everything works without JS. */
document.documentElement.classList.add("js");

document.addEventListener("DOMContentLoaded", () => {
  // Mobile nav
  const toggle = document.querySelector(".nav-toggle");
  const nav = document.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", () => {
      const open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!open));
      nav.classList.toggle("open", !open);
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && nav.classList.contains("open")) { toggle.click(); toggle.focus(); }
    });
  }

  // Piece viewer: thumbnails swap the main image, main image opens the lightbox
  const viewer = document.querySelector("[data-viewer]");
  const box = document.querySelector("[data-lightbox]");
  if (viewer && box && typeof box.showModal === "function") {
    const mainLink = viewer.querySelector(".viewer-main");
    const mainImg = viewer.querySelector("[data-main]");
    const thumbs = [...viewer.querySelectorAll(".thumb")];
    const full = JSON.parse(box.querySelector("[data-lb-full]").textContent);
    const lbImg = box.querySelector("[data-lb-img]");
    const count = box.querySelector("[data-lb-count]");
    let index = 0;

    const select = (i) => {
      index = (i + full.length) % full.length;
      const t = thumbs[index];
      if (t) {
        mainImg.removeAttribute("srcset");
        mainImg.src = t.dataset.src;
        thumbs.forEach((b) => b.removeAttribute("aria-current"));
        t.setAttribute("aria-current", "true");
        mainLink.href = t.dataset.full;
      }
    };
    const show = (i) => {
      index = (i + full.length) % full.length;
      lbImg.src = full[index];
      count.textContent = full.length > 1 ? `${index + 1} / ${full.length}` : "";
    };

    thumbs.forEach((t, i) => t.addEventListener("click", () => select(i)));
    mainLink.addEventListener("click", (e) => { e.preventDefault(); show(index); box.showModal(); });
    box.querySelector("[data-close]").addEventListener("click", () => box.close());
    box.querySelectorAll("[data-step]").forEach((b) => b.addEventListener("click", () => show(index + Number(b.dataset.step))));
    box.addEventListener("click", (e) => { if (e.target === box) box.close(); });
    box.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight") show(index + 1);
      if (e.key === "ArrowLeft") show(index - 1);
    });
    box.addEventListener("close", () => select(index));
    let x0 = null;
    box.addEventListener("touchstart", (e) => { x0 = e.touches[0].clientX; }, { passive: true });
    box.addEventListener("touchend", (e) => {
      if (x0 === null) return;
      const dx = e.changedTouches[0].clientX - x0;
      if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1));
      x0 = null;
    });
  }

  // Inquiry form: timestamp for the spam check, and an error message after a failed send
  const form = document.querySelector("[data-inquiry]");
  if (form) {
    const ts = form.querySelector("[data-ts]");
    if (ts) ts.value = String(Math.floor(Date.now() / 1000));
    if (new URLSearchParams(location.search).has("error")) {
      form.querySelector("[data-form-error]").hidden = false;
    }
  }

  // Pause autoplaying video for people who prefer reduced motion
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    document.querySelectorAll("video[autoplay]").forEach((v) => { v.removeAttribute("autoplay"); v.pause(); v.setAttribute("controls", ""); });
  }
});
