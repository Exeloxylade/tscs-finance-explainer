/* tscs-finance-explainer runtime: the TSCS look in one file.
 * A 2D documentary motion-graphics world driven by a voice clock, rendered by
 * HyperFrames (pure function of t, no timers). Everything here is keyed to a cue.
 *
 * window.TSCS API:
 *   TSCS.init({root, W, H})                 read the voice timing, size the stage
 *   TSCS.cue(id [,word])                     voice time of a segment / word
 *   TSCS.ramp(t,a,b)  TSCS.ease(x)           0..1 smoothstep helpers
 *   TSCS.contour(svg)                        draw the faint topographic background lines
 *   TSCS.title(el, t, cueOn [,cueOff])       fade a top-left title in/out
 *   TSCS.barChart(cfg)   -> {draw(t)}        bars that grow on a cue, with value labels
 *   TSCS.lineChart(cfg)  -> {draw(t)}        a line that draws left-to-right to a dot
 *   TSCS.chip(el, t, cueOn [,cueOff])        a small red/black callout chip pop-in
 *   TSCS.card(el, t, cueOn [,cueOff])        a framed footage/photo card slide+fade in
 *   TSCS.captions(host, segs)  -> render(t)  karaoke lower captions (prebuilt)
 * Palette lives in CSS vars; JS reads them so one place controls the look.
 */
(function () {
  const TSCS = {};
  let TIMING = [];

  TSCS.PAL = {
    bg: "#f3f1ec", ink: "#141414", sub: "#6b6b6b",
    red: "#8d1b2d", redText: "#a8203a", line: "#c9c4ba", grid: "#ddd8cf",
  };

  TSCS.init = function (opts) {
    TIMING = (window.__TIMING && window.__TIMING.segments) || [];
    return TIMING;
  };
  TSCS.seg = (id) => TIMING.find((s) => s.id === id);
  TSCS.cue = function (id, word) {
    const s = TSCS.seg(id); if (!s) return 0;
    if (word == null) return s.start;
    if (typeof word === "number") return s.words[word] ? s.words[word].start : s.start;
    const key = String(word).toLowerCase().replace(/[^a-z0-9]/g, "");
    const w = s.words.find((x) => x.w.toLowerCase().replace(/[^a-z0-9]/g, "") === key);
    return w ? w.start : s.start;
  };

  TSCS.ease = (x) => (x <= 0 ? 0 : x >= 1 ? 1 : x * x * (3 - 2 * x));
  TSCS.ramp = (t, a, b) => (b <= a ? (t >= b ? 1 : 0) : TSCS.ease((t - a) / (b - a)));

  // deterministic rng for the contour lines (never Math.random at render)
  TSCS.seeded = function (seed) {
    let s = seed >>> 0;
    return function () { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
  };

  // faint topographic contour background, drawn once into an <svg>
  TSCS.contour = function (svg, W, H, seed) {
    const r = TSCS.seeded(seed || 7);
    const NS = "http://www.w3.org/2000/svg";
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    const n = 26;
    for (let i = 0; i < n; i++) {
      const cx = W * (0.15 + r() * 0.7), cy = H * (0.1 + r() * 0.8);
      const rad = 60 + i * 42 + r() * 30;
      const path = document.createElementNS(NS, "path");
      let d = "";
      const pts = 40;
      for (let k = 0; k <= pts; k++) {
        const a = (k / pts) * Math.PI * 2;
        const wob = 1 + 0.12 * Math.sin(a * 3 + i) + 0.08 * Math.cos(a * 5 + i * 2);
        const x = cx + Math.cos(a) * rad * wob * 1.3;
        const y = cy + Math.sin(a) * rad * wob;
        d += (k === 0 ? "M" : "L") + x.toFixed(1) + " " + y.toFixed(1);
      }
      path.setAttribute("d", d + "Z");
      path.setAttribute("fill", "none");
      path.setAttribute("stroke", TSCS.PAL.grid);
      path.setAttribute("stroke-width", "1.4");
      path.setAttribute("opacity", "0.55");
      svg.appendChild(path);
    }
  };

  TSCS.title = function (el, t, cueOn, cueOff) {
    const a = TSCS.ramp(t, cueOn, cueOn + 0.4);
    const out = cueOff != null ? TSCS.ramp(t, cueOff, cueOff + 0.4) : 0;
    const o = a * (1 - out);
    el.style.opacity = o.toFixed(3);
    el.style.transform = `translateY(${((1 - a) * 14).toFixed(1)}px)`;
  };

  TSCS.chip = function (el, t, cueOn, cueOff) {
    const a = TSCS.ramp(t, cueOn, cueOn + 0.28);
    const out = cueOff != null ? TSCS.ramp(t, cueOff, cueOff + 0.3) : 0;
    const o = a * (1 - out);
    el.style.opacity = o.toFixed(3);
    const s = 0.85 + 0.15 * a;
    el.style.transform = `scale(${s.toFixed(3)})`;
  };

  TSCS.card = function (el, t, cueOn, cueOff) {
    const a = TSCS.ramp(t, cueOn, cueOn + 0.5);
    const out = cueOff != null ? TSCS.ramp(t, cueOff, cueOff + 0.4) : 0;
    const o = a * (1 - out);
    el.style.opacity = o.toFixed(3);
    el.style.transform = `translateX(${((1 - a) * 40).toFixed(1)}px) rotate(${(-1.5 * a).toFixed(2)}deg)`;
  };

  // bar chart: cfg {svg, x, y, w, h, bars:[{label,value,color,chipAt}], max, cueOn, span}
  TSCS.barChart = function (cfg) {
    const NS = "http://www.w3.org/2000/svg";
    const g = document.createElementNS(NS, "g");
    cfg.svg.appendChild(g);
    const baseY = cfg.y + cfg.h;
    const bw = cfg.w / (cfg.bars.length * 1.6);
    const gap = bw * 0.6;
    const made = cfg.bars.map((b, i) => {
      const bx = cfg.x + gap + i * (bw + gap);
      const rect = document.createElementNS(NS, "rect");
      rect.setAttribute("x", bx); rect.setAttribute("width", bw);
      rect.setAttribute("fill", b.color || TSCS.PAL.red);
      g.appendChild(rect);
      const val = document.createElementNS(NS, "text");
      val.setAttribute("x", bx + bw / 2); val.setAttribute("text-anchor", "middle");
      val.setAttribute("fill", TSCS.PAL.ink); val.setAttribute("font-weight", "800");
      val.setAttribute("font-size", "30"); val.textContent = b.value_label || "";
      g.appendChild(val);
      const lab = document.createElementNS(NS, "text");
      lab.setAttribute("x", bx + bw / 2); lab.setAttribute("y", baseY + 34);
      lab.setAttribute("text-anchor", "middle"); lab.setAttribute("fill", TSCS.PAL.sub);
      lab.setAttribute("font-size", "22"); lab.textContent = b.label || "";
      g.appendChild(lab);
      return { b, rect, val, lab, bx, bw };
    });
    return {
      draw(t) {
        made.forEach((m, i) => {
          const on = TSCS.ramp(t, cfg.cueOn + i * (cfg.stagger || 0.5),
                               cfg.cueOn + i * (cfg.stagger || 0.5) + (cfg.span || 0.7));
          const hh = cfg.h * (m.b.value / cfg.max) * on;
          m.rect.setAttribute("y", (baseY - hh).toFixed(1));
          m.rect.setAttribute("height", Math.max(0, hh).toFixed(1));
          m.val.setAttribute("y", (baseY - hh - 12).toFixed(1));
          m.val.setAttribute("opacity", on.toFixed(2));
          m.lab.setAttribute("opacity", on.toFixed(2));
        });
      },
    };
  };

  // line chart: cfg {svg, x, y, w, h, pts:[0..1 y values], color, cueOn, span, dot}
  TSCS.lineChart = function (cfg) {
    const NS = "http://www.w3.org/2000/svg";
    const g = document.createElementNS(NS, "g");
    cfg.svg.appendChild(g);
    const n = cfg.pts.length;
    const px = (i) => cfg.x + (i / (n - 1)) * cfg.w;
    const py = (v) => cfg.y + cfg.h - v * cfg.h;
    const path = document.createElementNS(NS, "path");
    path.setAttribute("fill", "none");
    path.setAttribute("stroke", cfg.color || TSCS.PAL.red);
    path.setAttribute("stroke-width", "3.5");
    path.setAttribute("stroke-linecap", "round");
    g.appendChild(path);
    const dot = document.createElementNS(NS, "circle");
    dot.setAttribute("r", "7"); dot.setAttribute("fill", cfg.color || TSCS.PAL.red);
    g.appendChild(dot);
    // precompute total length by walking points
    return {
      draw(t) {
        const prog = TSCS.ramp(t, cfg.cueOn, cfg.cueOn + (cfg.span || 2.2));
        const lastI = prog * (n - 1);
        const whole = Math.floor(lastI);
        let d = "M" + px(0).toFixed(1) + " " + py(cfg.pts[0]).toFixed(1);
        for (let i = 1; i <= whole; i++) d += "L" + px(i).toFixed(1) + " " + py(cfg.pts[i]).toFixed(1);
        let dx = px(whole), dy = py(cfg.pts[whole]);
        if (whole < n - 1) {
          const f = lastI - whole;
          dx = px(whole) + (px(whole + 1) - px(whole)) * f;
          dy = py(cfg.pts[whole]) + (py(cfg.pts[whole + 1]) - py(cfg.pts[whole])) * f;
          d += "L" + dx.toFixed(1) + " " + dy.toFixed(1);
        }
        path.setAttribute("d", d);
        dot.setAttribute("cx", dx.toFixed(1)); dot.setAttribute("cy", dy.toFixed(1));
        dot.setAttribute("opacity", prog > 0.02 ? "1" : "0");
        if (cfg.dot) { cfg.dot.style.left = dx + "px"; cfg.dot.style.top = dy + "px";
          cfg.dot.style.opacity = prog > 0.9 ? "1" : "0"; }
      },
    };
  };

  // karaoke captions, prebuilt once, class-toggled per frame (HyperFrames-safe)
  TSCS.captions = function (host, segs) {
    const lines = [];
    for (const s of segs) {
      for (const ln of s.lines) {
        const div = document.createElement("div");
        div.className = "tcap"; div.style.display = "none";
        const spans = ln.words.map((w) => {
          const sp = document.createElement("span");
          sp.className = "tw"; sp.textContent = w.w;
          div.appendChild(sp); div.appendChild(document.createTextNode(" "));
          return sp;
        });
        host.appendChild(div);
        lines.push({ start: ln.start, end: ln.end, words: ln.words, div, spans });
      }
    }
    return function render(t) {
      let active = null;
      for (const ln of lines) if (t >= ln.start - 0.12 && t <= ln.end + 0.5) active = ln;
      for (const ln of lines) ln.div.style.display = ln === active ? "block" : "none";
      if (!active) return;
      active.words.forEach((w, i) => {
        const sp = active.spans[i]; if (!sp) return;
        sp.classList.toggle("on", t >= w.start - 0.05);
        sp.classList.toggle("now", t >= w.start - 0.03 && t <= w.end + 0.05);
      });
    };
  };

  // ---- dual line chart: two lines on one axis (e.g. banks down, index up) ----
  // cfg {svg, x, y, w, h, lineA:{pts,color,label}, lineB:{...}, cueOn, span}
  TSCS.dualLine = function (cfg) {
    const NS = "http://www.w3.org/2000/svg";
    const g = document.createElementNS(NS, "g"); cfg.svg.appendChild(g);
    // axis baseline + faint gridlines
    for (let i = 0; i <= 4; i++) {
      const gy = cfg.y + (i / 4) * cfg.h;
      const l = document.createElementNS(NS, "line");
      l.setAttribute("x1", cfg.x); l.setAttribute("x2", cfg.x + cfg.w);
      l.setAttribute("y1", gy); l.setAttribute("y2", gy);
      l.setAttribute("stroke", TSCS.PAL.grid); l.setAttribute("stroke-width", "1");
      g.appendChild(l);
    }
    function mkLine(spec) {
      const n = spec.pts.length;
      const px = (i) => cfg.x + (i / (n - 1)) * cfg.w;
      const py = (v) => cfg.y + cfg.h - v * cfg.h;
      const path = document.createElementNS(NS, "path");
      path.setAttribute("fill", "none"); path.setAttribute("stroke", spec.color);
      path.setAttribute("stroke-width", spec.width || "3.5");
      path.setAttribute("stroke-linecap", "round"); path.setAttribute("stroke-linejoin", "round");
      g.appendChild(path);
      const dot = document.createElementNS(NS, "circle");
      dot.setAttribute("r", "7"); dot.setAttribute("fill", spec.color); g.appendChild(dot);
      const lab = document.createElementNS(NS, "text");
      lab.setAttribute("fill", spec.color); lab.setAttribute("font-weight", "800");
      lab.setAttribute("font-size", "26"); lab.textContent = spec.label || ""; g.appendChild(lab);
      return { spec, path, dot, lab, px, py, n };
    }
    const A = mkLine(cfg.lineA), B = mkLine(cfg.lineB);
    function drawOne(m, prog) {
      const lastI = prog * (m.n - 1), whole = Math.floor(lastI);
      let d = "M" + m.px(0).toFixed(1) + " " + m.py(m.spec.pts[0]).toFixed(1);
      for (let i = 1; i <= whole; i++) d += "L" + m.px(i).toFixed(1) + " " + m.py(m.spec.pts[i]).toFixed(1);
      let dx = m.px(whole), dy = m.py(m.spec.pts[whole]);
      if (whole < m.n - 1) { const f = lastI - whole;
        dx = m.px(whole) + (m.px(whole + 1) - m.px(whole)) * f;
        dy = m.py(m.spec.pts[whole]) + (m.py(m.spec.pts[whole + 1]) - m.py(m.spec.pts[whole])) * f;
        d += "L" + dx.toFixed(1) + " " + dy.toFixed(1); }
      m.path.setAttribute("d", d);
      m.dot.setAttribute("cx", dx.toFixed(1)); m.dot.setAttribute("cy", dy.toFixed(1));
      m.dot.setAttribute("opacity", prog > 0.02 ? "1" : "0");
      m.lab.setAttribute("x", (dx + 14).toFixed(1)); m.lab.setAttribute("y", (dy + 6).toFixed(1));
      m.lab.setAttribute("opacity", prog > 0.85 ? "1" : "0");
    }
    return { draw(t) {
      const prog = TSCS.ramp(t, cfg.cueOn, cfg.cueOn + (cfg.span || 2.4));
      drawOne(A, prog); drawOne(B, prog);
    } };
  };

  // ---- counting dot grid: a block of dots fills + a big number counts up ----
  // cfg {host, cols, rows, from, to, numEl, cueOn, span}  host is a positioned DIV
  TSCS.dotGridCount = function (cfg) {
    const total = cfg.cols * cfg.rows;
    const dots = [];
    cfg.host.style.display = "grid";
    cfg.host.style.gridTemplateColumns = `repeat(${cfg.cols}, 1fr)`;
    cfg.host.style.gap = (cfg.gap || 6) + "px";
    for (let i = 0; i < total; i++) {
      const d = document.createElement("div");
      d.style.width = d.style.height = (cfg.size || 10) + "px";
      d.style.borderRadius = "2px"; d.style.background = TSCS.PAL.red; d.style.opacity = "0";
      cfg.host.appendChild(d); dots.push(d);
    }
    return { draw(t) {
      const prog = TSCS.ramp(t, cfg.cueOn, cfg.cueOn + (cfg.span || 3));
      const lit = Math.round(prog * total);
      for (let i = 0; i < total; i++) dots[i].style.opacity = i < lit ? "0.92" : "0.08";
      if (cfg.numEl) cfg.numEl.textContent = Math.round(cfg.from + (cfg.to - cfg.from) * prog).toLocaleString();
    } };
  };

  // ---- tiers ladder: developed / emerging / frontier rows, one highlighted ----
  // cfg {host, rows:[{label,note,hot}], cueOn, stagger}  host positioned DIV
  TSCS.tiers = function (cfg) {
    const made = cfg.rows.map((r) => {
      const row = document.createElement("div");
      row.style.cssText = "display:flex;align-items:center;gap:18px;margin:10px 0;padding:16px 22px;"
        + "border-radius:8px;opacity:0;background:" + (r.hot ? TSCS.PAL.red : "#e9e5de")
        + ";color:" + (r.hot ? "#fff" : TSCS.PAL.ink) + ";";
      const lab = document.createElement("div");
      lab.style.cssText = "font-size:34px;font-weight:800;"; lab.textContent = r.label;
      const note = document.createElement("div");
      note.style.cssText = "font-size:22px;opacity:0.8;"; note.textContent = r.note || "";
      row.appendChild(lab); row.appendChild(note); cfg.host.appendChild(row);
      return row;
    });
    return { draw(t) {
      made.forEach((row, i) => {
        const on = TSCS.ramp(t, cfg.cueOn + i * (cfg.stagger || 0.5),
                             cfg.cueOn + i * (cfg.stagger || 0.5) + 0.4);
        row.style.opacity = on.toFixed(3);
        row.style.transform = `translateX(${((1 - on) * 30).toFixed(1)}px)`;
      });
    } };
  };

  // ---- generic staged reveal: fade a list of DOM els in one after another ----
  TSCS.stage = function (els, t, cueOn, stagger, dur) {
    els.forEach((el, i) => {
      const a = TSCS.ramp(t, cueOn + i * (stagger || 0.4), cueOn + i * (stagger || 0.4) + (dur || 0.4));
      el.style.opacity = a.toFixed(3);
      el.style.transform = `translateY(${((1 - a) * 16).toFixed(1)}px)`;
    });
  };

  window.TSCS = TSCS;
})();
