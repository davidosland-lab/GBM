# Knowledge Graph Explorer Wireframe

> Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

This note captures the dashboard concept from the handoff. The repository now includes a local HTML/API Knowledge Graph Explorer prototype for graph review; the full Streamlit dashboard remains a Phase 7 deliverable.

## Page Purpose

The Knowledge Graph Explorer lets a researcher search for a biomedical node, inspect its graph neighborhood, filter by evidence strength, and trace every displayed claim back to source PMIDs.

## Layout

- Top warning strip: persistent research-use-only disclaimer.
- Left filter panel: search term, node labels, relation types, evidence tier, hop depth, and minimum source PMID count.
- Center graph canvas: selected node centered, biological node types colored by label, edge styling driven by evidence tier and relation direction, with a visible evidence-tier legend.
- Right detail panel: selected node or edge properties, top relations, evidence-tier histogram, provenance PMID list, and sentence/trigger details when available.
- Bottom query drawer: the Cypher query used to produce the current view.

## Query Helpers

The current implementation adds `gbmbert.knowledge_graph.queries` for the two backend calls this page will need later:

- `neighborhood_query(...)` builds the parameterized Cypher for the graph canvas.
- `node_summary_query(...)` builds the selected-node drill-down query.

The actual Streamlit page should be added during the dashboard phase once the data, Neo4j loader, and local Explorer interaction model are stable.
