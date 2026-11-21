# MySQL 8

## Start

```bash
docker compose -f databases/mysql/docker-compose.yml --env-file .env up -d
```

## Planned steps

1. `schema.sql` with the 12-table relational schema (InnoDB, see `generator/README.md`).
2. Product specs in `product_attributes`; compare with a `JSON` column variant.
3. Bulk load generated CSVs with `LOAD DATA LOCAL INFILE`.
4. Run CRUD scenarios without secondary indexes, then add indexes and rerun.
5. Capture plans with `EXPLAIN ANALYZE`.
6. Repeat at 500k / 1M / 10M rows.
