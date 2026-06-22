# Step 4 — Unified Relations Report

**Total unified edges (USED↔USED):** 196


**By source:** {'MODEL_FK': 188, 'SQL_JOIN': 8}

**By confidence:** {'HIGH': 188, 'MED': 8}


## Coverage

- FK fields extracted: 193
- FK fields where BOTH endpoints in schema: 189
- FK fields pointing to UNUSED table (dropped): 0
- Models with db_table: 260
- Raw SQL JOIN edges: 10
- Shared-key clusters (naming hints): 46


## Top shared-key clusters (naming hints)

| column | tables sharing |
|---|---|
| `user_id` | 90 |
| `channel_id` | 51 |
| `video_id` | 48 |
| `product_id` | 14 |
| `brand_logo_id` | 14 |
| `campaign_id` | 12 |
| `partner_team_id` | 11 |
| `post_id` | 10 |
| `partner_id` | 8 |
| `adslot_id` | 8 |