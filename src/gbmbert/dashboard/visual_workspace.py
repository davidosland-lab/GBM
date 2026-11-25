"""Relationship-first visual workspace for the Streamlit dashboard.

Research-use only. This view makes articles, entities, relations, curation
state, and artifact lineage visible in one place. It reuses the local graph
record JSONL contracts and never claims clinical validity.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gbmbert.dashboard.review_topics import (
    REVIEW_TOPICS,
    active_review_topic,
    get_review_topic,
)
from gbmbert.knowledge_graph.explorer import (
    DEFAULT_BASELINE_DATA,
    DEFAULT_SAMPLE_DATA,
    GraphExplorerService,
    graph_artifacts_from_index,
)
from gbmbert.knowledge_graph.schema import EvidenceTier, NodeLabel, RelationType

RESEARCH_WARNING = (
    "Research-use only. Not medical advice. Not intended for diagnosis, "
    "treatment selection, or clinical decision-making."
)
VISUAL_WORKSPACE_MODES = ("Explore", "Curate", "Audit")
DEFAULT_ARTIFACT_INDEX = Path("reports/artifact_index.json")
DEFAULT_CURATION_REGISTRY = Path("reports/review/curation_run_registry.json")
REVIEW_GRAPHS: tuple[tuple[str, Path], ...] = tuple(
    (topic.label, Path(topic.graph_jsonl)) for topic in REVIEW_TOPICS
)


def visual_workspace_context(
    root: str | Path = ".",
    *,
    topic_key: str | None = None,
    graph_path: str | Path | None = None,
    search: str = "",
    node_labels: list[str] | None = None,
    relation_types: list[str] | None = None,
    min_evidence_tier: int = 0,
    mode: str = "Explore",
    overlay_only: bool = False,
    tier_changed_only: bool = False,
) -> dict[str, Any]:
    """Build the visual workspace data model from local graph artifacts."""

    base = Path(root)
    topic = get_review_topic(topic_key)
    index_path = base / DEFAULT_ARTIFACT_INDEX
    selected_graph = _resolve_visual_graph_path(base, graph_path, topic_key=topic_key)
    graph_options = _graph_options(base, index_path)
    warnings: list[str] = []
    records = []
    if selected_graph.exists():
        service = GraphExplorerService.from_jsonl(
            selected_graph,
            artifact_index_path=index_path if index_path.exists() else None,
        )
        try:
            graph = service.neighborhood(
                search=search,
                node_labels=_parse_node_labels(node_labels or []),
                relation_types=_parse_relation_types(relation_types or []),
                min_evidence_tier=EvidenceTier(min_evidence_tier),
                overlay_only=overlay_only,
                tier_changed_only=tier_changed_only,
                limit=140,
            )
            inspection = service.inspection(recent_limit=12)
            metadata = service.metadata()
            records = service.records or []
        finally:
            service.close()
    else:
        graph = _empty_graph(search)
        inspection = {
            "counts": {"nodes": 0, "relationships": 0, "labels": {}, "relation_types": {}},
            "evidence_tiers": [],
            "recent_papers": [],
        }
        metadata = {"node_labels": [], "relation_types": [], "evidence_tiers": [], "graph_artifacts": []}
        warnings.append(f"Graph records not found: {selected_graph}")

    article_graph = _article_constellation(records, search=search, limit=140)
    active_graph = article_graph if mode == "Curate" else graph
    papers = _visible_papers(active_graph, records)
    artifact_lineage = _artifact_lineage(base / DEFAULT_ARTIFACT_INDEX)
    curation_timeline = _curation_timeline(base / DEFAULT_CURATION_REGISTRY)
    return {
        "mode": mode if mode in VISUAL_WORKSPACE_MODES else "Explore",
        "topic_key": topic.key,
        "topic_label": topic.label,
        "graph_path": str(selected_graph),
        "graph_options": graph_options,
        "graph": graph,
        "article_graph": article_graph,
        "papers": papers,
        "inspection": inspection,
        "metadata": metadata,
        "artifact_lineage": artifact_lineage,
        "curation_timeline": curation_timeline,
        "warnings": warnings,
    }


def render_visual_workspace_page(st: object, *, mode: str = "Explore") -> None:
    selected_mode = st.sidebar.radio("Workspace mode", VISUAL_WORKSPACE_MODES, index=VISUAL_WORKSPACE_MODES.index(mode))
    topic = active_review_topic(st)
    initial_context = visual_workspace_context(mode=selected_mode, topic_key=topic.key)
    graph_options = initial_context["graph_options"]
    graph_labels = [item["label"] for item in graph_options] or [initial_context["graph_path"]]
    selected_label = st.sidebar.selectbox(
        "Graph source",
        graph_labels,
        index=_default_graph_option_index(graph_options, initial_context["graph_path"]),
        key=f"visual_graph_source_{topic.key}",
    )
    selected_graph = next(
        (item["path"] for item in graph_options if item["label"] == selected_label),
        initial_context["graph_path"],
    )
    search = st.sidebar.text_input("Search articles, entities, or relations", "")
    metadata = initial_context["metadata"]
    node_labels = st.sidebar.multiselect(
        "Node labels",
        [item["value"] for item in metadata.get("node_labels", [])],
    )
    relation_types = st.sidebar.multiselect(
        "Relation types",
        [item["value"] for item in metadata.get("relation_types", [])],
    )
    tier_options = [item["value"] for item in metadata.get("evidence_tiers", [])] or [0, 1, 2, 3, 4, 5]
    min_tier = st.sidebar.select_slider("Minimum evidence tier", options=tier_options, value=min(tier_options))
    overlay_only = st.sidebar.checkbox("Curated overlay only", value=False)
    tier_changed_only = st.sidebar.checkbox("Tier changed only", value=False)
    context = visual_workspace_context(
        topic_key=topic.key,
        graph_path=selected_graph,
        search=search,
        node_labels=node_labels,
        relation_types=relation_types,
        min_evidence_tier=int(min_tier),
        mode=selected_mode,
        overlay_only=overlay_only,
        tier_changed_only=tier_changed_only,
    )
    st.subheader(f"{topic.label.title()} Visual Workspace")
    st.caption(
        "Explore the research-review article, entity, condition, procedure, and relationship map "
        "from one rotatable 3D surface."
    )
    _render_workspace_metrics(st, context)
    _render_workspace_html(st, context)
    render_paper_opener(st, context, key_prefix=f"visual_paper_{topic.key}")
    for warning in context["warnings"]:
        st.warning(warning)


def visual_workspace_html(context: dict[str, Any]) -> str:
    payload = json.dumps(_visual_payload(context), ensure_ascii=False)
    html = r"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    :root {
      --ink: #182026; --muted: #61717d; --paper: #fbfcfb; --line: #d7ded9;
      --source: #5b6c8f; --claim: #9a6a2d; --audit: #4f6b3c; --teal: #2f766d;
    }
    * { box-sizing: border-box; }
    body { margin: 0; background: var(--paper); color: var(--ink); font: 13px/1.45 system-ui, sans-serif; }
    .workspace { display: grid; grid-template-columns: 260px minmax(0, 1fr) 320px; min-height: 748px; border: 1px solid var(--line); }
    .rail, .detail { padding: 14px; background: #f3f6f3; overflow: auto; }
    .rail { border-right: 1px solid var(--line); }
    .detail { border-left: 1px solid var(--line); }
    .canvas-wrap { min-width: 0; display: grid; grid-template-rows: auto 1fr auto; background: #ffffff; }
    .toolbar { padding: 12px 14px; border-bottom: 1px solid var(--line); display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    .chip, .mode { border: 1px solid var(--line); background: #fff; border-radius: 4px; padding: 4px 8px; color: var(--muted); }
    .mode.active { color: var(--ink); border-color: #8ca69b; background: #e8f1ed; }
    #three-graph { position: relative; width: 100%; height: 560px; min-height: 420px; background: #ffffff; overflow: hidden; }
    #three-graph canvas { display: block; width: 100%; height: 100%; }
    #three-status { position: absolute; inset: 0; display: grid; place-items: center; color: var(--muted); pointer-events: none; }
    h2, h3 { margin: 0 0 10px; }
    h2 { font-size: 15px; } h3 { font-size: 12px; text-transform: uppercase; color: var(--muted); }
    .section { border-top: 1px solid var(--line); padding-top: 12px; margin-top: 12px; }
    .stat { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.35fr); gap: 8px; padding: 7px 0; border-bottom: 1px solid #e3e8e5; }
    .stat span { color: var(--muted); }
    .stat strong { overflow-wrap: anywhere; text-align: right; font-weight: 600; }
    .list { display: grid; gap: 8px; margin: 0; padding: 0; list-style: none; }
    .list li { padding: 8px; background: #fff; border: 1px solid var(--line); border-radius: 4px; overflow-wrap: anywhere; }
    .legend { display: grid; gap: 6px; }
    .legend-item { display: flex; align-items: center; gap: 7px; }
    .dot { width: 11px; height: 11px; border-radius: 50%; flex: 0 0 auto; }
    .query { background: #20282f; color: #f4f7f8; margin: 0; padding: 10px 14px; font: 12px/1.45 Consolas, monospace; max-height: 118px; overflow: auto; }
    .stage { display: grid; grid-template-columns: 1fr auto; gap: 8px; align-items: center; }
    .stage strong { font-size: 16px; }
    .open-links { display: grid; gap: 6px; max-height: 260px; overflow: auto; }
    .open-link { display: block; padding: 8px 10px; background: #fff; border: 1px solid #8ca69b; border-radius: 4px;
      color: var(--teal); font-weight: 600; text-decoration: none; overflow-wrap: anywhere; }
    .open-link:hover { background: #e8f1ed; }
    .open-more { color: var(--muted); text-decoration: underline; }
    .hint { color: var(--muted); padding-top: 6px; }
    /* Stacked layout: the graph leads, then the selection detail, then the lineage rail.
       Without the ordering the rail pushes the graph past the bottom of the embed. */
    @media (max-width: 980px) {
      .workspace { grid-template-columns: 1fr; }
      .canvas-wrap { order: -2; }
      .detail { order: -1; }
      .rail { order: 0; }
      .rail, .detail { border: 0; border-bottom: 1px solid var(--line); }
      #three-graph { height: 460px; }
    }
  </style>
</head>
<body>
  <div class="workspace">
    <aside class="rail">
      <h2>Visual Workspace</h2>
      <div id="mode-list"></div>
      <div class="section"><h3>Lineage</h3><ul id="lineage" class="list"></ul></div>
      <div class="section"><h3>Evidence</h3><div id="evidence" class="legend"></div></div>
    </aside>
    <section class="canvas-wrap">
      <div class="toolbar"><span class="chip" id="graph-source"></span><span class="chip" id="visible-counts"></span><span class="chip" id="selected-mode"></span></div>
      <div id="three-graph" role="img" aria-label="Visual Workspace Graph"><div id="three-status">Loading 3D graph</div></div>
      <pre id="query" class="query"></pre>
    </section>
    <aside class="detail"><h2 id="detail-title">Graph</h2><div id="detail-body"></div></aside>
  </div>
  <script type="application/json" id="visual-workspace-payload">__PAYLOAD__</script>
  <script type="module">
    import * as THREE from "https://esm.sh/three@0.160.0";
    import { OrbitControls } from "https://esm.sh/three@0.160.0/examples/jsm/controls/OrbitControls.js";

    const payload = JSON.parse(document.getElementById("visual-workspace-payload").textContent);
    const PUBMED_BASE = "https://pubmed.ncbi.nlm.nih.gov/";
    const tierColors = {0:"#8b98a3",1:"#0b6e69",2:"#587728",3:"#b66a13",4:"#7b5fb2",5:"#8f2431"};
    const labelColors = {Paper:"#5b6c8f", Trial:"#5b6c8f", Claim:"#9a6a2d", Drug:"#3b7770", Treatment:"#3b7770", DeliveryModifier:"#3b7770", Outcome:"#7a7840", Disease:"#7a7840", Stage:"#4f6b3c"};
    const mount = document.getElementById("three-graph");
    const status = document.getElementById("three-status");
    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    const selectable = [];
    const nodeSources = new Map();
    let renderer;
    let camera;
    let scene;
    let controls;
    let hovered;

    function activeGraph() { if (payload.mode === "Curate") return payload.article_graph; if (payload.mode === "Audit") return payload.lineage_graph; return payload.graph; }
    function short(value, max=28) { const text = String(value || ""); return text.length > max ? text.slice(0, max - 3) + "..." : text; }
    function esc(value) { return String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
    function colorFor(node) { const label = (node.labels && node.labels[0]) || node.kind || "Node"; return labelColors[label] || "#34786f"; }
    function edgeColor(edge) { return tierColors[Number(edge.evidence_tier || 0)] || "#8b98a3"; }
    function renderChrome() {
      document.getElementById("mode-list").innerHTML = payload.modes.map(mode => `<div class="mode ${mode === payload.mode ? "active" : ""}">${mode}</div>`).join("");
      document.getElementById("graph-source").textContent = payload.graph_path;
      document.getElementById("selected-mode").textContent = payload.mode;
      document.getElementById("lineage").innerHTML = payload.artifact_lineage.nodes.map(stage => `<li class="stage"><span>${esc(stage.label)}</span><strong>${stage.count}</strong></li>`).join("");
      document.getElementById("evidence").innerHTML = payload.evidence_tiers.map(item => `<div class="legend-item"><span class="dot" style="background:${edgeColor({evidence_tier:item.tier})}"></span><span>tier ${item.tier}: ${item.count}</span></div>`).join("") || `<div class="legend-item"><span class="dot" style="background:#8b98a3"></span><span>none</span></div>`;
    }
    function vectorLayout(nodes) {
      const groups = Array.from(new Set(nodes.map(node => (node.labels && node.labels[0]) || node.kind || "Node")));
      const counts = {};
      const positions = {};
      nodes.forEach((node, index) => {
        const group = (node.labels && node.labels[0]) || node.kind || "Node";
        const groupIndex = Math.max(0, groups.indexOf(group));
        const slot = counts[group] || 0;
        counts[group] = slot + 1;
        const band = groupIndex - (groups.length - 1) / 2;
        const angle = slot * 2.399963 + groupIndex * 0.77;
        const radius = 26 + Math.sqrt(slot + 1) * 10 + (index % 5) * 1.8;
        const z = band * 32 + Math.sin(slot * 0.9) * 16;
        positions[node.id] = new THREE.Vector3(Math.cos(angle) * radius, Math.sin(angle) * radius, z);
      });
      return positions;
    }
    function makeLabel(text, color) {
      const canvas = document.createElement("canvas");
      canvas.width = 256;
      canvas.height = 72;
      const ctx = canvas.getContext("2d");
      ctx.font = "600 22px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = "rgba(255,255,255,0.92)";
      ctx.fillRect(0, 10, 256, 52);
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.strokeRect(2, 12, 252, 48);
      ctx.fillStyle = "#182026";
      ctx.fillText(short(text, 24), 128, 37, 226);
      const texture = new THREE.CanvasTexture(canvas);
      const sprite = new THREE.Sprite(new THREE.SpriteMaterial({map: texture, transparent: true}));
      sprite.scale.set(22, 6.2, 1);
      return sprite;
    }
    function cylinderBetween(start, end, color, radius) {
      const direction = new THREE.Vector3().subVectors(end, start);
      const length = direction.length();
      const geometry = new THREE.CylinderGeometry(radius, radius, Math.max(length, 0.1), 10, 1);
      const material = new THREE.MeshStandardMaterial({color, roughness: 0.56, metalness: 0.08});
      const cylinder = new THREE.Mesh(geometry, material);
      cylinder.position.copy(start).add(end).multiplyScalar(0.5);
      cylinder.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize());
      return cylinder;
    }
    function renderGraph3D() {
      const graph = activeGraph();
      const nodes = graph.nodes || [];
      const edges = graph.edges || [];
      document.getElementById("visible-counts").textContent = `${nodes.length} nodes / ${edges.length} edges`;
      nodeSources.clear();
      edges.forEach(edge => {
        const props = edge.properties || {};
        const pmids = [].concat(edge.source_pmids || props.source_pmids || [], props.source_id ? [props.source_id] : []);
        [edge.source, edge.target].forEach(endpoint => {
          if (!endpoint) return;
          const bucket = nodeSources.get(endpoint) || [];
          pmids.forEach(value => {
            const pmid = String(value ?? "").trim();
            if (/^\d{1,12}$/.test(pmid) && !bucket.includes(pmid)) bucket.push(pmid);
          });
          if (bucket.length) nodeSources.set(endpoint, bucket);
        });
      });
      document.getElementById("query").textContent = payload.mode === "Explore" ? payload.query : payload.mode + " visual model";
      if (!nodes.length) { status.textContent = "No visual records match the current filters"; renderDetail({label:"No selection", properties:{}}); return; }

      scene = new THREE.Scene();
      scene.background = new THREE.Color("#ffffff");
      const width = Math.max(320, mount.clientWidth || 840);
      const height = Math.max(380, mount.clientHeight || 560);
      camera = new THREE.PerspectiveCamera(48, width / height, 0.1, 1000);
      camera.position.set(0, -155, 118);
      renderer = new THREE.WebGLRenderer({antialias: true, alpha: false});
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.setSize(width, height);
      mount.appendChild(renderer.domElement);
      status.style.display = "none";

      scene.add(new THREE.HemisphereLight("#eef7f4", "#d7d1bc", 1.4));
      const key = new THREE.DirectionalLight("#ffffff", 1.9);
      key.position.set(80, -100, 120);
      scene.add(key);
      const grid = new THREE.GridHelper(180, 12, "#d5ded9", "#edf1ef");
      grid.rotation.x = Math.PI / 2;
      scene.add(grid);

      const positions = vectorLayout(nodes);
      const nodeById = new Map(nodes.map(node => [node.id, node]));
      edges.forEach((edge, index) => {
        const source = positions[edge.source];
        const target = positions[edge.target];
        if (!source || !target) return;
        const mesh = cylinderBetween(source, target, edgeColor(edge), Math.max(0.35, Math.min(1.35, 0.42 + Number(edge.evidence_tier || 0) * 0.15)));
        mesh.userData.item = edge;
        mesh.userData.baseColor = edgeColor(edge);
        mesh.userData.kind = "edge";
        selectable.push(mesh);
        scene.add(mesh);
      });
      nodes.forEach((node) => {
        const radius = node.kind === "article" || (node.labels || [])[0] === "Paper" || (node.labels || [])[0] === "Trial" ? 5.8 : 4.5;
        const color = colorFor(node);
        const mesh = new THREE.Mesh(
          new THREE.SphereGeometry(radius, 24, 18),
          new THREE.MeshStandardMaterial({color, roughness: 0.42, metalness: 0.12})
        );
        mesh.position.copy(positions[node.id]);
        mesh.userData.item = node;
        mesh.userData.baseScale = radius;
        mesh.userData.kind = "node";
        selectable.push(mesh);
        scene.add(mesh);
        const label = makeLabel(node.label || node.id, color);
        label.position.copy(mesh.position).add(new THREE.Vector3(0, 0, radius + 5.5));
        scene.add(label);
      });

      controls = new OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.08;
      controls.rotateSpeed = 0.65;
      controls.zoomSpeed = 0.72;
      controls.minDistance = 55;
      controls.maxDistance = 310;
      controls.autoRotate = true;
      controls.autoRotateSpeed = 0.45;
      renderer.domElement.addEventListener("pointermove", onPointerMove);
      renderer.domElement.addEventListener("click", onClick);
      renderer.domElement.addEventListener("dblclick", onDoubleClick);
      window.addEventListener("resize", onResize);
      renderDetail(nodes[0]);
      animate();
    }
    function pick(event) {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      return raycaster.intersectObjects(selectable, false)[0]?.object;
    }
    function onPointerMove(event) {
      const hit = pick(event);
      mount.style.cursor = hit ? "pointer" : "grab";
      if (hovered && hovered !== hit && hovered.userData.kind === "node") hovered.scale.setScalar(1);
      hovered = hit;
      if (hovered && hovered.userData.kind === "node") hovered.scale.setScalar(1.24);
    }
    function onClick(event) {
      const hit = pick(event);
      if (hit?.userData?.item) {
        controls.autoRotate = false;
        renderDetail(hit.userData.item);
      }
    }
    function onDoubleClick(event) {
      const hit = pick(event);
      const item = hit?.userData?.item;
      if (!item) return;
      controls.autoRotate = false;
      renderDetail(item);
      const targets = openTargets(item);
      if (targets.links.length) window.open(targets.links[0][1], "_blank", "noopener,noreferrer");
    }
    function onResize() {
      if (!renderer || !camera) return;
      const width = Math.max(320, mount.clientWidth || 840);
      const height = Math.max(380, mount.clientHeight || 560);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height);
    }
    function animate() {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }
    function pmidsFor(item) {
      // A selection is openable when it is a paper, or when it carries / connects to source PMIDs.
      const props = (item && item.properties) || {};
      const labels = (item && item.labels) || [];
      const found = [];
      const add = value => {
        const text = String(value ?? "").trim();
        if (/^\d{1,12}$/.test(text) && !found.includes(text)) found.push(text);
      };
      if (labels.includes("Paper")) { add(item.key_value); add(item.label); }
      add(props.pmid); add(props.source_pmid); add(props.source_id);
      (item.source_pmids || props.source_pmids || []).forEach(add);
      const idText = String((item && item.id) || "");
      if (idText.startsWith("Paper:")) add(idText.slice(6));
      if (idText.startsWith("Claim:")) add(idText.split(":")[1]);
      if (!found.length && item.kind === "entity") (nodeSources.get(item.id) || []).forEach(add);
      if (!found.length && item.id && nodeSources.has(item.id)) (nodeSources.get(item.id) || []).forEach(add);
      return found;
    }
    function openTargets(item) {
      const props = (item && item.properties) || {};
      const labels = (item && item.labels) || [];
      const pmids = pmidsFor(item);
      const links = [];
      const titles = payload.paper_titles || {};
      if (pmids.length > 1) {
        // PubMed resolves a comma-separated PMID list as one result set.
        links.push(["Open all " + pmids.length + " papers in PubMed", PUBMED_BASE + "?term=" + pmids.join("%2C")]);
      }
      pmids.slice(0, 8).forEach(pmid => {
        const title = titles[pmid];
        const label = pmids.length === 1 ? "Open in PubMed" : (title ? pmid + " - " + title : "PubMed " + pmid);
        links.push([label, PUBMED_BASE + pmid + "/"]);
      });
      const pmcidRaw = String(props.pmcid || "").trim().toUpperCase();
      if (pmcidRaw) {
        const pmcid = pmcidRaw.startsWith("PMC") ? pmcidRaw : "PMC" + pmcidRaw;
        links.push(["Full text (PMC)", "https://www.ncbi.nlm.nih.gov/pmc/articles/" + pmcid + "/"]);
      }
      const doi = String(props.doi || "").replace(/^https?:\/\/(dx\.)?doi\.org\//i, "").trim();
      if (doi.includes("/")) links.push(["DOI", "https://doi.org/" + doi]);
      let nct = String(props.nct_id || "").trim();
      if (!nct && labels.includes("Trial")) nct = String(item.key_value || "").trim();
      if (/^NCT\d{6,}$/i.test(nct)) links.push(["ClinicalTrials.gov", "https://clinicaltrials.gov/study/" + nct.toUpperCase()]);
      return {pmids, links};
    }
    function renderDetail(item) {
      document.getElementById("detail-title").textContent = item.type ? "Relationship" : (item.label || "Selection");
      const props = item.properties || {};
      const labels = item.labels ? item.labels.join(", ") : (item.type || "");
      const kv = Object.entries(props).slice(0, 12).map(([key, value]) => `<div class="stat"><span>${esc(key)}</span><strong>${esc(JSON.stringify(value))}</strong></div>`).join("");
      const basics = [["Kind", labels || item.kind || "item"], ["Id", item.id || ""], ["Source", item.source || ""], ["Target", item.target || ""], ["Evidence", item.evidence_tier !== undefined ? "tier " + item.evidence_tier : ""]].filter(row => row[1] !== "").map(row => `<div class="stat"><span>${esc(row[0])}</span><strong>${esc(row[1])}</strong></div>`).join("");
      const targets = openTargets(item);
      let openBlock;
      if (targets.links.length) {
        const buttons = targets.links.map(([label, url]) => `<a class="open-link" href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)}</a>`).join("");
        const extra = targets.pmids.length > 8 ? `<div class="hint">${targets.pmids.length - 8} more source papers are covered by the "Open all" link.</div>` : "";
        const hint = targets.pmids.length ? `<div class="hint">Double-click a node to open its paper directly.</div>` : "";
        openBlock = `<div class="section"><h3>Open</h3><div class="open-links">${buttons}</div>${extra}${hint}</div>`;
      } else {
        openBlock = `<div class="section"><h3>Open</h3><div class="hint">No paper link on this selection. Pick a paper node, a claim, or an entity that a paper mentions.</div></div>`;
      }
      document.getElementById("detail-body").innerHTML = basics + openBlock + (kv ? `<div class="section"><h3>Properties</h3>${kv}</div>` : "");
    }
    renderChrome();
    renderGraph3D();
  </script>
</body>
</html>"""
    return html.replace("__PAYLOAD__", payload)


def _default_graph_option_index(graph_options: list[dict[str, str]], graph_path: str) -> int:
    """Preselect the graph source matching the active topic's resolved graph."""

    for index, item in enumerate(graph_options):
        if item["path"] == graph_path:
            return index
    return 0


def _resolve_visual_graph_path(
    base: Path,
    graph_path: str | Path | None,
    *,
    topic_key: str | None = None,
) -> Path:
    if graph_path:
        path = Path(graph_path)
        return path if path.is_absolute() else base / path
    topic_graph = base / get_review_topic(topic_key).graph_jsonl
    if topic_graph.exists():
        return topic_graph
    for _, review_graph in REVIEW_GRAPHS:
        if (base / review_graph).exists():
            return base / review_graph
    baseline = base / DEFAULT_BASELINE_DATA
    if baseline.exists():
        return baseline
    sample = base / DEFAULT_SAMPLE_DATA
    if sample.exists():
        return sample
    options = _graph_options(base, base / DEFAULT_ARTIFACT_INDEX)
    if options:
        path = Path(options[0]["path"])
        return path if path.is_absolute() else base / path
    return sample


def _graph_options(base: Path, index_path: Path) -> list[dict[str, str]]:
    options: list[dict[str, str]] = []
    for review_label, review_path in REVIEW_GRAPHS:
        review_graph = base / review_path
        if review_graph.exists():
            options.append(
                {
                    "label": f"{review_label} ({review_path.parent.as_posix()})",
                    "path": str(review_graph),
                }
            )
    for path in (DEFAULT_BASELINE_DATA, DEFAULT_SAMPLE_DATA):
        candidate = base / path
        if candidate.exists():
            options.append({"label": f"{candidate.name} ({path.parent.as_posix()})", "path": str(candidate)})
    if index_path.exists():
        for item in graph_artifacts_from_index(index_path):
            path = Path(item["path"])
            resolved = path if path.is_absolute() else base / path
            if resolved.exists() and not any(existing["path"] == str(resolved) for existing in options):
                options.append({"label": f"{item['artifact_type']} - {path.name}", "path": str(resolved)})
    return options


def _parse_node_labels(values: list[str]) -> list[NodeLabel]:
    labels: list[NodeLabel] = []
    for value in values:
        try:
            labels.append(NodeLabel(value))
        except ValueError:
            continue
    return labels


def _parse_relation_types(values: list[str]) -> list[RelationType]:
    relations: list[RelationType] = []
    for value in values:
        try:
            relations.append(RelationType(value))
        except ValueError:
            continue
    return relations


def _empty_graph(search: str) -> dict[str, Any]:
    return {"nodes": [], "edges": [], "cypher": "", "parameters": {"search": search}, "warning": RESEARCH_WARNING, "mode": "missing"}


def _article_constellation(records: list[Any], *, search: str = "", limit: int = 120) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    search_text = search.casefold()
    for record in records:
        source_id = str(getattr(record, "pmid", "") or getattr(record, "nct_id", ""))
        if not source_id:
            continue
        title = _record_title(record)
        searchable = " ".join([source_id, title, " ".join(_record_entity_labels(record))]).casefold()
        if search_text and search_text not in searchable:
            continue
        source_label = "Paper" if hasattr(record, "pmid") else "Trial"
        source_node_id = f"{source_label}:{source_id}"
        nodes[source_node_id] = {
            "id": source_node_id,
            "label": source_id,
            "labels": [source_label],
            "kind": "article",
            "key_value": source_id,
            "properties": {"title": title, "date": _record_date(record), "entities": len(getattr(record, "nodes", []) or []), "relations": len(getattr(record, "relations", []) or [])},
        }
        for entity in getattr(record, "nodes", []) or []:
            entity_node_id = f"{entity.label.value}:{entity.key_value}"
            nodes[entity_node_id] = {
                "id": entity_node_id,
                "label": _display_name(entity.properties, entity.key_value),
                "labels": [entity.label.value],
                "kind": "entity",
                "key_value": str(entity.key_value),
                "properties": entity.properties,
            }
            edges.append({"id": f"{source_node_id}|MENTIONS|{entity_node_id}", "source": source_node_id, "target": entity_node_id, "type": "MENTIONS", "evidence_tier": 0, "properties": {"source_id": source_id}})
            if len(edges) >= limit:
                break
        for index, relation in enumerate(getattr(record, "relations", []) or []):
            claim_id = f"Claim:{source_id}:{index}"
            nodes[claim_id] = {
                "id": claim_id,
                "label": relation.relation.value,
                "labels": ["Claim"],
                "kind": "claim",
                "key_value": claim_id,
                "properties": {"source_id": source_id, "evidence_tier": int(getattr(relation, "evidence_tier", 0) or 0), "sentence": (getattr(relation, "properties", {}) or {}).get("sentence", "")},
            }
            head_id = f"{relation.head.label.value}:{relation.head.key_value}"
            tail_id = f"{relation.tail.label.value}:{relation.tail.key_value}"
            tier = int(getattr(relation, "evidence_tier", 0) or 0)
            edges.extend(
                [
                    {"id": f"{source_node_id}|SUPPORTS|{claim_id}", "source": source_node_id, "target": claim_id, "type": "SUPPORTS", "evidence_tier": tier, "properties": {"source_id": source_id}},
                    {"id": f"{claim_id}|HEAD|{head_id}", "source": claim_id, "target": head_id, "type": "HEAD", "evidence_tier": tier, "properties": {"relation": relation.relation.value}},
                    {"id": f"{claim_id}|TAIL|{tail_id}", "source": claim_id, "target": tail_id, "type": "TAIL", "evidence_tier": tier, "properties": {"relation": relation.relation.value}},
                ]
            )
            if len(edges) >= limit:
                break
        if len(edges) >= limit:
            break
    return {"nodes": list(nodes.values()), "edges": edges[:limit], "mode": "article_constellation"}


def _graph_pmids(graph_payload: dict[str, Any]) -> list[str]:
    """Collect the source PMIDs reachable from the nodes and edges on screen."""

    from gbmbert.dashboard.paper_links import normalize_pmid

    found: list[str] = []
    seen: set[str] = set()

    def _add(value: object) -> None:
        pmid = normalize_pmid(value)
        if pmid and pmid not in seen:
            seen.add(pmid)
            found.append(pmid)

    for node in graph_payload.get("nodes") or []:
        properties = node.get("properties") or {}
        if "Paper" in (node.get("labels") or []):
            _add(node.get("key_value"))
        _add(properties.get("pmid"))
        _add(properties.get("source_id"))
    for edge in graph_payload.get("edges") or []:
        properties = edge.get("properties") or {}
        for value in edge.get("source_pmids") or properties.get("source_pmids") or []:
            _add(value)
        _add(properties.get("source_id"))
    return found


def _visible_papers(graph_payload: dict[str, Any], records: list[Any]) -> list[dict[str, Any]]:
    """Build openable paper rows for every paper reachable from the current view."""

    from gbmbert.dashboard.paper_links import normalize_pmid

    by_pmid: dict[str, Any] = {}
    for record in records:
        pmid = normalize_pmid(getattr(record, "pmid", ""))
        if pmid:
            by_pmid[pmid] = record

    papers: list[dict[str, Any]] = []
    for pmid in _graph_pmids(graph_payload):
        record = by_pmid.get(pmid)
        properties = dict(getattr(record, "paper_properties", None) or {}) if record is not None else {}
        papers.append(
            {
                "pmid": pmid,
                "title": str(properties.get("title") or "").strip(),
                "abstract": str(properties.get("abstract") or "").strip(),
                "journal": str(properties.get("journal") or "").strip(),
                "publication_date": str(properties.get("publication_date") or "").strip(),
                "doi": str(properties.get("doi") or "").strip(),
                "entity_count": len(getattr(record, "nodes", []) or []) if record is not None else 0,
            }
        )
    return papers


def _paper_option_label(paper: dict[str, Any]) -> str:
    """Selectbox label: PMID first so a PMID read off the graph is easy to find."""

    title = paper.get("title") or "(no title in local record)"
    if len(title) > 96:
        title = title[:93] + "..."
    year = str(paper.get("publication_date") or "")[:4]
    return f"PMID {paper['pmid']} · {year} · {title}" if year else f"PMID {paper['pmid']} · {title}"


def render_paper_opener(st: object, context: dict[str, Any], *, key_prefix: str = "visual_paper") -> None:
    """Open-the-paper controls for the papers on the current graph view."""

    from gbmbert.dashboard.paper_links import render_paper_row, render_pmid_open_list

    papers = context.get("papers") or []
    st.subheader("Open a paper from this view")
    st.caption(
        "Select a node in the 3D graph and its open links appear in the detail panel "
        "(double-click a node to jump straight to PubMed). This list is the same set of "
        "papers, for when the embedded graph cannot open a new tab."
    )
    if not papers:
        st.info(
            "No papers on the current graph view. Clear the search or lower the minimum "
            "evidence tier in the sidebar."
        )
        return
    labels = [_paper_option_label(paper) for paper in papers]
    selected = st.selectbox("Paper", labels, key=f"{key_prefix}_select")
    paper = papers[labels.index(selected)] if selected in labels else papers[0]
    render_paper_row(st, paper, key_prefix=f"{key_prefix}_card", show_abstract=True)
    with st.expander(f"All {len(papers)} papers on this view"):
        render_pmid_open_list(
            st,
            [item["pmid"] for item in papers],
            key_prefix=f"{key_prefix}_list",
            title="",
        )


def _record_title(record: Any) -> str:
    props = getattr(record, "paper_properties", None) or getattr(record, "trial_properties", None) or {}
    return str(props.get("title") or props.get("brief_title") or props.get("name") or "")


def _record_date(record: Any) -> str:
    props = getattr(record, "paper_properties", None) or getattr(record, "trial_properties", None) or {}
    return str(props.get("publication_date") or props.get("last_update_date") or props.get("start_date") or "")


def _record_entity_labels(record: Any) -> list[str]:
    labels: list[str] = []
    for node in getattr(record, "nodes", []) or []:
        labels.append(str(node.key_value))
        labels.append(_display_name(node.properties, node.key_value))
    return labels


def _display_name(properties: dict[str, Any], fallback: object) -> str:
    return str(properties.get("display_name") or properties.get("name") or properties.get("symbol") or fallback)


def _artifact_lineage(index_path: Path) -> dict[str, Any]:
    payload = _read_json(index_path)
    artifacts = payload.get("artifacts", []) if isinstance(payload, dict) else []
    stages = [
        ("sources", "Sources"),
        ("graph", "Graph Records"),
        ("review", "Review Queues"),
        ("curation", "Curated Evidence"),
        ("training", "Training Packs"),
        ("governance", "Audit Reports"),
    ]
    stage_artifacts: dict[str, list[dict[str, Any]]] = {key: [] for key, _ in stages}
    for artifact in artifacts:
        stage = _lineage_stage_for_artifact(artifact)
        if stage:
            stage_artifacts[stage].append(artifact)
    nodes = []
    for key, label in stages:
        examples = sorted(stage_artifacts[key], key=lambda item: item.get("modified_at_utc", ""), reverse=True)[:5]
        nodes.append(
            {
                "id": key,
                "label": label,
                "count": len(stage_artifacts[key]),
                "examples": [{"path": item.get("path", ""), "artifact_type": item.get("artifact_type", ""), "category": item.get("category", "")} for item in examples],
            }
        )
    return {
        "artifact_count": int(payload.get("artifact_count") or len(artifacts)) if isinstance(payload, dict) else 0,
        "nodes": nodes,
        "edges": [{"source": stages[index][0], "target": stages[index + 1][0], "type": "feeds"} for index in range(len(stages) - 1)],
        "category_counts": payload.get("category_counts", {}) if isinstance(payload, dict) else {},
    }


def _lineage_stage_for_artifact(artifact: dict[str, Any]) -> str:
    artifact_type = str(artifact.get("artifact_type", ""))
    category = str(artifact.get("category", ""))
    path = str(artifact.get("path", "")).casefold()
    if category == "raw":
        return "sources"
    if "graph_records" in artifact_type:
        return "graph"
    if "review_queue" in artifact_type or "reviewed_queue" in artifact_type:
        return "review"
    if "curated_evidence" in artifact_type or "evidence_overlay" in artifact_type:
        return "curation"
    if "training_pack" in artifact_type or "gold_training_pack" in artifact_type or category == "training":
        return "training"
    if "audit" in artifact_type or "governance" in artifact_type or "dashboard_training" in artifact_type:
        return "governance"
    if "reports/training/governance" in path:
        return "governance"
    return ""


def _curation_timeline(registry_path: Path) -> list[dict[str, Any]]:
    payload = _read_json(registry_path)
    entries = payload.get("entries", []) if isinstance(payload, dict) else []
    return [
        {
            "run_id": entry.get("run_id", ""),
            "graph_path": entry.get("graph_path", ""),
            "overlay_graph_path": entry.get("overlay_graph_path", ""),
            "reviewed_queue_path": entry.get("reviewed_queue_path", ""),
            "handoff_bundle_path": entry.get("handoff_bundle_path", ""),
        }
        for entry in entries[-8:]
    ]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _render_workspace_metrics(st: object, context: dict[str, Any]) -> None:
    counts = context["inspection"].get("counts", {})
    graph = context["graph"]
    article_graph = context["article_graph"]
    lineage = context["artifact_lineage"]
    columns = st.columns(5)
    columns[0].metric("Graph nodes", counts.get("nodes", 0))
    columns[1].metric("Relationships", counts.get("relationships", 0))
    columns[2].metric("Visible edges", len(graph.get("edges", [])))
    columns[3].metric("Article map nodes", len(article_graph.get("nodes", [])))
    columns[4].metric("Indexed artifacts", lineage.get("artifact_count", 0))


def _render_workspace_html(st: object, context: dict[str, Any]) -> None:
    html = visual_workspace_html(context)
    if hasattr(st, "iframe"):
        st.iframe(html, height=780)
        return
    components = getattr(st, "components", None)
    if components is not None and hasattr(components, "v1"):
        components.v1.html(html, height=780, scrolling=True)
    else:
        import streamlit.components.v1 as components_v1

        components_v1.html(html, height=780, scrolling=True)


def _visual_payload(context: dict[str, Any]) -> dict[str, Any]:
    lineage = context["artifact_lineage"]
    lineage_graph = {
        "nodes": [
            {"id": item["id"], "label": item["label"], "labels": ["Stage"], "kind": "stage", "properties": {"artifact_count": item["count"], "examples": item["examples"]}}
            for item in lineage["nodes"]
        ],
        "edges": [
            {"id": f"{item['source']}|{item['type']}|{item['target']}", "source": item["source"], "target": item["target"], "type": item["type"], "evidence_tier": 0, "properties": {}}
            for item in lineage["edges"]
        ],
    }
    return {
        "modes": list(VISUAL_WORKSPACE_MODES),
        "mode": context["mode"],
        "graph_path": context["graph_path"],
        "graph": context["graph"],
        "article_graph": context["article_graph"],
        "lineage_graph": lineage_graph,
        "artifact_lineage": lineage,
        "evidence_tiers": context["inspection"].get("evidence_tiers", []),
        "paper_titles": _paper_title_index(context.get("papers") or []),
        "query": context["graph"].get("cypher", ""),
    }


def _paper_title_index(papers: list[dict[str, Any]], *, max_chars: int = 72) -> dict[str, str]:
    """Short titles keyed by PMID for the graph's open-link labels."""

    index: dict[str, str] = {}
    for paper in papers:
        title = str(paper.get("title") or "").strip()
        if len(title) > max_chars:
            title = title[: max_chars - 3] + "..."
        index[str(paper.get("pmid"))] = title
    return index
