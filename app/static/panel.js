// Gráfico de peticiones por hora (SVG) con guía y tooltip al pasar el cursor o usar las flechas
(function () {
  const cont = document.getElementById("grafico");
  if (!cont) return;

  const datos = JSON.parse(cont.dataset.serie);
  const tip = cont.querySelector(".tooltip");
  const NS = "http://www.w3.org/2000/svg";
  const fmt = (n) => String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, " ");  // 16 842
  let geo = null;
  let actual = null;

  function el(tag, attrs, texto) {
    const n = document.createElementNS(NS, tag);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (texto !== undefined) n.textContent = texto;
    return n;
  }

  function dibujar() {
    cont.querySelector("svg")?.remove();
    const w = cont.clientWidth;
    const h = 240;
    const m = { t: 12, r: 12, b: 28, l: 48 };
    const max = Math.ceil(Math.max(...datos.map((d) => d.valor)) / 500) * 500;
    const x = (i) => m.l + (i / (datos.length - 1)) * (w - m.l - m.r);
    const y = (v) => m.t + (1 - v / max) * (h - m.t - m.b);

    const svg = el("svg", { width: w, height: h, viewBox: `0 0 ${w} ${h}`, "aria-hidden": "true" });

    for (let k = 0; k <= 4; k++) {
      const v = (max * k) / 4;
      svg.append(el("line", { x1: m.l, x2: w - m.r, y1: y(v), y2: y(v), class: k === 0 ? "g-base" : "g-rejilla" }));
      svg.append(el("text", { x: m.l - 10, y: y(v) + 4, class: "g-eje", "text-anchor": "end" }, fmt(v)));
    }
    datos.forEach((d, i) => {
      if (i % 6 === 0 || i === datos.length - 1) {
        const ancla = i === 0 ? "start" : i === datos.length - 1 ? "end" : "middle";
        svg.append(el("text", { x: x(i), y: h - 8, class: "g-eje", "text-anchor": ancla }, d.hora));
      }
    });

    const linea = "M" + datos.map((d, i) => `${x(i)},${y(d.valor)}`).join("L");
    svg.append(el("path", { d: `${linea}L${x(datos.length - 1)},${y(0)}L${x(0)},${y(0)}Z`, class: "g-area" }));
    svg.append(el("path", { d: linea, class: "g-linea" }));

    const guia = el("line", { y1: m.t, y2: h - m.b, class: "g-guia", visibility: "hidden" });
    const punto = el("circle", { r: 5, class: "g-punto", visibility: "hidden" });
    svg.append(guia, punto);

    cont.prepend(svg);
    geo = { x, y, m, w, guia, punto };
    if (actual !== null) mostrar(actual);
  }

  function mostrar(i) {
    actual = i;
    const d = datos[i];
    const px = geo.x(i);
    const py = geo.y(d.valor);
    geo.guia.setAttribute("x1", px);
    geo.guia.setAttribute("x2", px);
    geo.punto.setAttribute("cx", px);
    geo.punto.setAttribute("cy", py);
    geo.guia.setAttribute("visibility", "visible");
    geo.punto.setAttribute("visibility", "visible");

    tip.innerHTML = `<strong>${fmt(d.valor)}</strong> peticiones<span>${d.hora} a ${String((i + 1) % 24).padStart(2, "0")}:00</span>`;
    tip.hidden = false;
    const mitad = tip.offsetWidth / 2;
    tip.style.left = Math.min(Math.max(px, mitad), geo.w - mitad) + "px";
    tip.style.top = py + "px";
  }

  function ocultar() {
    actual = null;
    tip.hidden = true;
    if (!geo) return;
    geo.guia.setAttribute("visibility", "hidden");
    geo.punto.setAttribute("visibility", "hidden");
  }

  cont.addEventListener("pointermove", (e) => {
    const r = cont.getBoundingClientRect();
    const t = (e.clientX - r.left - geo.m.l) / (geo.w - geo.m.l - geo.m.r);
    mostrar(Math.min(datos.length - 1, Math.max(0, Math.round(t * (datos.length - 1)))));
  });
  cont.addEventListener("pointerleave", ocultar);
  cont.addEventListener("blur", ocultar);
  cont.addEventListener("focus", () => mostrar(actual ?? datos.length - 1));
  cont.addEventListener("keydown", (e) => {
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
    e.preventDefault();
    const paso = e.key === "ArrowLeft" ? -1 : 1;
    mostrar(Math.min(datos.length - 1, Math.max(0, (actual ?? datos.length - 1) + paso)));
  });

  new ResizeObserver(dibujar).observe(cont);
})();
