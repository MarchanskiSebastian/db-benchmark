# Neo4j 5

## Start

```bash
docker compose -f databases/neo4j/docker-compose.yml --env-file .env up -d
```

Browser: http://localhost:7474

## Planned graph model

Nodes: `Customer`, `Order`, `Product`, `Category`, `Brand`

```
(Customer)-[:PLACED]->(Order)-[:CONTAINS {quantity, unit_price}]->(Product)
(Product)-[:BELONGS_TO]->(Category)
(Product)-[:MADE_BY]->(Brand)
(CPU:Product)-[:COMPATIBLE_WITH]->(Motherboard:Product)   // matching socket
```

Category-specific specs (VRAM, cores, socket, capacity) are stored as node properties.

## Planned steps

1. Load generated CSVs with `LOAD CSV` / batched `UNWIND`.
2. Derive `COMPATIBLE_WITH` from matching sockets (CPU to motherboard) and memory type (RAM to motherboard).
3. Run CRUD scenarios without indexes, then add indexes / constraints and rerun.
4. Capture plans with `PROFILE`.
5. Repeat at 500k / 1M / 10M nodes in the largest label.
