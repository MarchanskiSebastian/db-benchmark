# PostgreSQL 16

## Start

```bash
docker compose -f databases/postgres/docker-compose.yml --env-file .env up -d
```

## Planned steps

1. `schema.sql` with the 12-table relational schema (see `generator/README.md`).
2. Product specs in `product_attributes` (EAV); compare with a `JSONB` column variant.
3. Bulk load generated CSVs with `COPY`.
4. Run CRUD scenarios without secondary indexes, then add indexes and rerun.
5. Capture plans with `EXPLAIN (ANALYZE, BUFFERS)`.
6. Repeat at 500k / 1M / 10M rows.
