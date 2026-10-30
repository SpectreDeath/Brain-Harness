"""Standalone interactive HTML brief template for Knowledge Graph visualization (Rule 51)."""

from __future__ import annotations

# Static template using string replacement tokens to avoid f-string brace escaping collisions.
HTML_TEMPLATE: str = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>__TITLE__</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0d1117; color: #c9d1d9; }
    header { padding: 14px 20px; background: #161b22; border-bottom: 1px solid #30363d; display: flex; justify-content: space-between; align-items: center; }
    h1 { font-size: 1.2rem; font-weight: 600; color: #f0f6fc; }
    .meta-time { font-size: 0.8rem; color: #8b949e; }
    .ribbon { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 10px; padding: 12px 20px; background: #090d13; border-bottom: 1px solid #30363d; }
    .card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 10px; }
    .card-label { font-size: 0.72rem; text-transform: uppercase; color: #8b949e; }
    .card-value { font-size: 1.3rem; font-weight: 700; color: #58a6ff; margin-top: 2px; }
    .card-sub { font-size: 0.72rem; color: #8b949e; margin-top: 2px; }
    .controls { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; padding: 8px 20px; background: #161b22; border-bottom: 1px solid #30363d; font-size: 0.82rem; }
    input, select, button { background: #0d1117; border: 1px solid #30363d; color: #c9d1d9; padding: 5px 8px; border-radius: 6px; font-size: 0.82rem; }
    button { cursor: pointer; background: #21262d; } button:hover { background: #30363d; }
    .main-view { display: flex; height: calc(100vh - 220px); position: relative; }
    canvas { flex: 1; display: block; background: #0d1117; cursor: grab; } canvas:active { cursor: grabbing; }
    #inspector { width: 330px; background: #161b22; border-left: 1px solid #30363d; padding: 14px; overflow-y: auto; font-size: 0.82rem; }
    .badge { display: inline-block; padding: 2px 5px; border-radius: 4px; font-size: 0.68rem; font-weight: 600; margin-right: 4px; }
    .b-ki { background: #1f6feb; color: #fff; } .b-skill { background: #8957e5; color: #fff; } .b-path { background: #238636; color: #fff; }
    .b-tag { background: #21262d; color: #8b949e; margin: 2px; display: inline-block; padding: 2px 5px; border-radius: 4px; font-size: 0.68rem; }
    .sec-title { font-size: 0.72rem; text-transform: uppercase; color: #8b949e; margin: 10px 0 4px 0; }
    .edge-row { padding: 3px 0; border-bottom: 1px solid #21262d; font-size: 0.73rem; display: flex; justify-content: space-between; }
    .overview-sec { padding: 16px 20px; background: #0d1117; border-top: 1px solid #30363d; }
    .mermaid { background: #161b22; padding: 14px; border-radius: 6px; border: 1px solid #30363d; overflow-x: auto; }
  </style>
</head>
<body>
  <header><h1>__TITLE__</h1><div class="meta-time">Generated: __TIMESTAMP__</div></header>
  <section class="ribbon">__SUMMARY_METRICS__</section>
  <section class="controls">
    <input type="text" id="search" placeholder="Search title, ID, tag..." style="width: 170px;" />
    <select id="domain-filter"><option value="ALL">All Domains</option></select>
    <select id="kind-filter"><option value="ALL">All Node Kinds</option><option value="ki">Knowledge Items (KI)</option><option value="skill">Skills</option><option value="path">Code Paths</option></select>
    <label><input type="checkbox" id="show-derived" checked /> Show Derived</label>
    <label>Min Conf: <span id="conf-val">0.0</span> <input type="range" id="conf-slider" min="0" max="1" step="0.05" value="0" style="width: 65px;" /></label>
    <label>Timeline: <span id="time-val">All</span> <input type="range" id="time-slider" min="0" max="100" value="100" style="width: 75px;" /><button id="play-btn" style="padding:1px 5px;margin-left:3px;">▶</button></label>
    <button id="reset-cam">Reset View</button>
  </section>
  <div class="main-view">
    <canvas id="graph-canvas"></canvas>
    <aside id="inspector"><div style="color: #8b949e; text-align: center; margin-top: 30px;">Select a node to inspect attributes and incident edges.</div></aside>
  </div>
  <section class="overview-sec"><h2 style="font-size: 0.95rem; color: #f0f6fc; margin-bottom: 8px;">Domain Topology Overview</h2><pre class="mermaid">__MERMAID_CODE__</pre></section>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <script>try { mermaid.initialize({ startOnLoad: true, theme: 'dark' }); } catch(e) {}</script>
  <script>
    const DATA = __JSON_PAYLOAD__;
    const canvas = document.getElementById("graph-canvas"), ctx = canvas.getContext("2d");
    const DOM_COLORS = { developer_experience: "#58a6ff", data_engineering: "#3fb950", security_and_forensics: "#f85149", agent_orchestration: "#bc8cff", kernel_and_ioc: "#d29922", general: "#8b949e" };
    let width = 0, height = 0, camX = 0, camY = 0, scale = 1, isDragging = false, dragStart = {x:0, y:0};
    let nodes = [], edges = [], nodeMap = {}, selectedNode = null, hoveredNode = null;
    let distinctDates = [], isPlaying = false, playInterval = null;
    function resize() { width = canvas.clientWidth; height = canvas.clientHeight; canvas.width = width * window.devicePixelRatio; canvas.height = height * window.devicePixelRatio; ctx.scale(window.devicePixelRatio, window.devicePixelRatio); }
    window.addEventListener("resize", () => { resize(); render(); });
    function init() {
      resize(); camX = width / 2; camY = height / 2; const domains = new Set();
      nodes = DATA.nodes.map((n, i) => { domains.add(n.domain); const angle = (i / DATA.nodes.length) * 2 * Math.PI, rad = 140 + Math.random() * 220; return { ...n, x: Math.cos(angle) * rad, y: Math.sin(angle) * rad, vx: 0, vy: 0 }; });
      nodeMap = {}; nodes.forEach(n => nodeMap[n.id] = n); edges = DATA.edges.filter(e => nodeMap[e.source] && nodeMap[e.target]);
      distinctDates = Array.from(new Set(nodes.map(n => n.created_at ? n.created_at.slice(0, 10) : "").filter(Boolean))).sort();
      const ts = document.getElementById("time-slider");
      if (distinctDates.length > 0) { ts.max = distinctDates.length - 1; ts.value = distinctDates.length - 1; }
      const domSel = document.getElementById("domain-filter");
      Array.from(domains).sort().forEach(d => { const opt = document.createElement("option"); opt.value = d; opt.textContent = d; domSel.appendChild(opt); });
      for (let s = 0; s < 60; s++) {
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const dx = nodes[j].x - nodes[i].x, dy = nodes[j].y - nodes[i].y, d = Math.hypot(dx, dy) || 1;
            if (d < 180) { const f = (180 - d) / d * 0.1; nodes[i].x -= dx * f; nodes[i].y -= dy * f; nodes[j].x += dx * f; nodes[j].y += dy * f; }
          }
        }
        edges.forEach(e => { const u = nodeMap[e.source], v = nodeMap[e.target], dx = v.x - u.x, dy = v.y - u.y, d = Math.hypot(dx, dy) || 1, f = (d - 45) * 0.01; u.x += dx / d * f; u.y += dy / d * f; v.x -= dx / d * f; v.y -= dy / d * f; });
      }
      setupEvents(); render();
    }
    function getFiltered() {
      const q = document.getElementById("search").value.toLowerCase(), dom = document.getElementById("domain-filter").value;
      const kind = document.getElementById("kind-filter").value, showDer = document.getElementById("show-derived").checked, minC = parseFloat(document.getElementById("conf-slider").value);
      const maxDateIdx = parseInt(document.getElementById("time-slider").value);
      const maxDate = (distinctDates.length > 0 && maxDateIdx < distinctDates.length - 1) ? distinctDates[maxDateIdx] : null;
      const matchN = new Set(nodes.filter(n => {
        if (dom !== "ALL" && n.domain !== dom) return false;
        if (kind !== "ALL" && n.node_kind !== kind) return false;
        if (maxDate && n.created_at && n.created_at.slice(0, 10) > maxDate) return false;
        if (q && !(n.label.toLowerCase().includes(q) || n.id.toLowerCase().includes(q) || n.tags.some(t => t.toLowerCase().includes(q)))) return false;
        return true;
      }).map(n => n.id));
      const matchE = edges.filter(e => matchN.has(e.source) && matchN.has(e.target) && (showDer || !e.derived) && e.confidence >= minC);
      return { matchN, matchE };
    }
    function render() {
      ctx.clearRect(0, 0, width, height); ctx.save(); ctx.translate(camX, camY); ctx.scale(scale, scale);
      const { matchN, matchE } = getFiltered();
      matchE.forEach(e => {
        const s = nodeMap[e.source], t = nodeMap[e.target]; ctx.beginPath();
        if (e.derived) ctx.setLineDash([4, 4]); else ctx.setLineDash([]);
        ctx.strokeStyle = (selectedNode && (s.id === selectedNode.id || t.id === selectedNode.id)) ? "#58a6ff" : (e.derived ? "rgba(139,148,158,0.25)" : "rgba(240,246,252,0.4)");
        ctx.lineWidth = (selectedNode && (s.id === selectedNode.id || t.id === selectedNode.id)) ? 2 : 1;
        ctx.moveTo(s.x, s.y); ctx.lineTo(t.x, t.y); ctx.stroke();
      });
      ctx.setLineDash([]);
      nodes.forEach(n => {
        if (!matchN.has(n.id)) return;
        const col = DOM_COLORS[n.domain] || "#8b949e", r = Math.max(5, Math.min(15, 5 + (n.retrieval_count || 0) * 1.5)), isSel = selectedNode && selectedNode.id === n.id;
        ctx.beginPath();
        if (n.node_kind === "ki") ctx.arc(n.x, n.y, r, 0, Math.PI * 2); else ctx.rect(n.x - r, n.y - r, r * 2, r * 2);
        ctx.fillStyle = col; ctx.fill(); ctx.strokeStyle = isSel ? "#ffffff" : "#30363d"; ctx.lineWidth = isSel ? 3 : 1.5; ctx.stroke();
        if (scale > 0.8 || isSel || (hoveredNode && hoveredNode.id === n.id)) {
          ctx.font = "10px sans-serif"; ctx.fillStyle = "#c9d1d9";
          ctx.fillText(n.label.length > 20 ? n.label.slice(0, 18) + "…" : n.label, n.x + r + 3, n.y + 3);
        }
      });
      ctx.restore();
    }
    function setupEvents() {
      canvas.addEventListener("mousedown", e => { isDragging = true; dragStart = { x: e.clientX - camX, y: e.clientY - camY }; });
      window.addEventListener("mouseup", () => isDragging = false);
      canvas.addEventListener("mousemove", e => {
        if (isDragging) { camX = e.clientX - dragStart.x; camY = e.clientY - dragStart.y; render(); return; }
        const r = canvas.getBoundingClientRect(), mx = (e.clientX - r.left - camX) / scale, my = (e.clientY - r.top - camY) / scale;
        const prev = hoveredNode; hoveredNode = nodes.find(n => Math.hypot(n.x - mx, n.y - my) <= 12) || null;
        canvas.style.cursor = hoveredNode ? "pointer" : "grab"; if (hoveredNode !== prev) render();
      });
      canvas.addEventListener("click", () => { if (hoveredNode) selectNode(hoveredNode); });
      canvas.addEventListener("wheel", e => { e.preventDefault(); scale = Math.min(4, Math.max(0.15, scale * (e.deltaY < 0 ? 1.15 : 0.87))); render(); }, { passive: false });
      ["search", "domain-filter", "kind-filter", "show-derived"].forEach(id => document.getElementById(id).addEventListener("input", render));
      document.getElementById("conf-slider").addEventListener("input", e => { document.getElementById("conf-val").textContent = e.target.value; render(); });
      document.getElementById("reset-cam").addEventListener("click", () => { camX = width / 2; camY = height / 2; scale = 1; render(); });
      const ts = document.getElementById("time-slider");
      ts.addEventListener("input", e => { const idx = parseInt(e.target.value); document.getElementById("time-val").textContent = (distinctDates.length > 0 && idx < distinctDates.length - 1) ? distinctDates[idx] : "All"; render(); });
      document.getElementById("play-btn").addEventListener("click", () => {
        isPlaying = !isPlaying; document.getElementById("play-btn").textContent = isPlaying ? "⏸" : "▶";
        if (isPlaying) {
          if (parseInt(ts.value) >= distinctDates.length - 1) ts.value = 0;
          playInterval = setInterval(() => {
            let v = parseInt(ts.value) + 1;
            if (v >= distinctDates.length) { clearInterval(playInterval); isPlaying = false; document.getElementById("play-btn").textContent = "▶"; return; }
            ts.value = v; document.getElementById("time-val").textContent = (v === distinctDates.length - 1) ? "All" : distinctDates[v]; render();
          }, 450);
        } else { clearInterval(playInterval); }
      });
    }
    function selectNode(n) {
      selectedNode = n;
      const bClass = n.node_kind === "ki" ? "b-ki" : (n.node_kind === "skill" ? "b-skill" : "b-path");
      const inc = edges.filter(e => e.source === n.id || e.target === n.id);
      let h = `<div style="font-size:1.05rem;font-weight:700;color:#f0f6fc;margin-bottom:6px;">${n.label}</div>`;
      h += `<div><span class="badge ${bClass}">${n.node_kind.toUpperCase()}</span><span class="badge" style="background:#21262d;color:#58a6ff;">${n.domain}</span><span class="badge" style="background:#21262d;color:#8b949e;">${n.status}</span></div>`;
      h += `<div class="sec-title">ID &amp; Timestamps</div><div style="font-family:monospace;font-size:0.75rem;color:#58a6ff;">${n.id}</div><div style="color:#8b949e;font-size:0.72rem;">Created: ${n.created_at || "N/A"}</div>`;
      if (n.source_target) h += `<div class="sec-title">Source Target</div><div style="font-family:monospace;font-size:0.72rem;word-break:break-all;">${n.source_target}</div>`;
      if (n.tags && n.tags.length) h += `<div class="sec-title">Tags</div><div>${n.tags.map(t => `<span class="b-tag">${t}</span>`).join("")}</div>`;
      h += `<div class="sec-title">Incident Edges (${inc.length})</div>`;
      if (!inc.length) h += `<div style="color:#8b949e;">No incident edges</div>`;
      inc.forEach(e => {
        const isOut = e.source === n.id, other = isOut ? e.target : e.source, dir = isOut ? "→" : "←";
        h += `<div class="edge-row"><span>${dir} <b>${e.type}</b> <a href="#" onclick="selectById('${other}');return false;" style="color:#58a6ff;text-decoration:none;">${other}</a></span><span>${(e.confidence*100).toFixed(0)}%</span></div>`;
      });
      document.getElementById("inspector").innerHTML = h; render();
    }
    window.selectById = function(id) { const n = nodeMap[id]; if (n) selectNode(n); };
    window.onload = init;
  </script>
</body>
</html>
"""
