# Corpus Manifest: pubmed_gbm_merged_backfill_2026-07-18

Research-use only. Not medical advice. Not intended for diagnosis, treatment selection, or clinical decision-making.

- Generated UTC: 2026-07-18T02:52:17+00:00
- Source: NCBI PubMed via gbmbert-search-pubmed retmax-per-query=50
- Query pack: pubmed_gbm_v1+pubmed_gbm_v2
- Record count: 1839
- Command: `gbmbert-search-pubmed --query-pack pubmed_gbm_v1/v2 --retmax-per-query 50; merge+dedupe by pmid`
- NCBI email configured: True
- NCBI API key configured: True

## Files
- `data\raw\pubmed_gbm_v1_backfill_2026-07-18.jsonl`: 612 records, 1219252 bytes, SHA256 `2E3DC1361031FA54A49E63E5F9557F3F5CCEA469762A93EEBD902E9B4FB4A16F`
- `data\raw\pubmed_gbm_v2_backfill_2026-07-18.jsonl`: 315 records, 657144 bytes, SHA256 `9CAEF4D1458225B9D4F7921128F43957DBAED5523994E50DFE72FC220FD6ED4E`
- `data\raw\pubmed_gbm_merged_backfill_2026-07-18.jsonl`: 912 records, 1846773 bytes, SHA256 `5BBCCD79FD156F437B311D7183DAAD6CC890C356F6FF0D8E5FFC802667F6820B`

## Notes
- Tuned five previously empty v2 queries; 912 unique PMIDs; research-use only.
