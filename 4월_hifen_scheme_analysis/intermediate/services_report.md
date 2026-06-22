# Step 7 — Inter-app Service Graph

**Total directed edges:** 122
**Apps active in graph:** 27

**Edges by source (non-exclusive):** IMPORTS=122, SHARED_TABLE=12, CRON=11

## Top 20 dependency edges (by weight)

| from | to | weight | sources | imports | shared_tables | cron |
|---|---|---|---|---|---|---|
| creators_insights | youtube | 51 | IMPORTS | 17 | 0 | 0 |
| express | user | 45 | IMPORTS | 15 | 0 | 0 |
| amore | oliveyoung | 27 | IMPORTS | 9 | 0 | 0 |
| instagram | user | 27 | IMPORTS | 9 | 0 | 0 |
| express | brand | 26 | IMPORTS|SHARED_TABLE | 8 | 1 | 0 |
| amore | youtube | 24 | IMPORTS | 8 | 0 | 0 |
| instagram | ugwanggiAPI | 21 | IMPORTS | 7 | 0 | 0 |
| express | youtube | 20 | IMPORTS|SHARED_TABLE | 6 | 1 | 0 |
| partner | youtube | 20 | IMPORTS|CRON | 6 | 0 | 1 |
| user | subscribe | 20 | IMPORTS|CRON | 6 | 0 | 1 |
| oliveyoung | brand | 19 | IMPORTS|CRON | 5 | 0 | 2 |
| search | brand | 19 | IMPORTS|SHARED_TABLE | 5 | 2 | 0 |
| ugwanggiAPI | subscribe | 19 | IMPORTS|CRON | 5 | 0 | 2 |
| amore | brand | 18 | IMPORTS | 6 | 0 | 0 |
| trends | youtube | 18 | IMPORTS | 6 | 0 | 0 |
| brand | ads | 16 | IMPORTS|SHARED_TABLE | 4 | 2 | 0 |
| search | youtube | 16 | IMPORTS|SHARED_TABLE | 4 | 2 | 0 |
| aichat | admin | 15 | IMPORTS | 5 | 0 | 0 |
| subscribe | user | 15 | IMPORTS | 5 | 0 | 0 |
| youtube | user | 15 | IMPORTS | 5 | 0 | 0 |

## Top inbound (most depended-upon) apps
| app | inbound_deps |
|---|---|
| ugwanggiAPI | 22 |
| user | 20 |
| brand | 18 |
| youtube | 17 |
| partner | 11 |
| ads | 7 |
| instagram | 7 |
| subscribe | 6 |
| search | 4 |
| express | 3 |

## Top outbound (most dependent) apps
| app | outbound_deps |
|---|---|
| ugwanggiAPI | 8 |
| brand | 7 |
| youtube | 7 |
| admin | 7 |
| search | 6 |
| aichat | 6 |
| partner_admin | 6 |
| amore | 6 |
| instagram | 6 |
| monitoring | 5 |