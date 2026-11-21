# Neo4j 5 (Community)

All commands run from the repo root with the virtualenv active (`pip install -r requirements.txt`)
and a `.env` copied from `.env.example`.

## Start

```bash
docker compose -f databases/neo4j/docker-compose.yml --env-file .env up -d
docker inspect -f '{{.State.Health.Status}}' bench-neo4j   # wait for "healthy"
```

Browser: http://localhost:7474 (user and password from `.env`).

The container gets the shared limits from `.env` (`DB_CPUS`, `DB_MEMORY`), 1 GB heap + 2 GB page
cache for the server, 2 GB heap for `neo4j-admin import`, and `data/` mounted read-only at `/import`.
There's no `env_file`: the image turns every `NEO4J_*` variable into a config setting and rejects
unknown ones.

## Import

```bash
python -m generator --size s --out data/s --seed 42    # if data/s does not exist yet
python databases/neo4j/load.py --size s
```

`load.py`:
1. stops Neo4j (offline import), then runs `neo4j-admin database import full` in a one-off container
   on the same volume with the CSVs from `data/<size>/neo4j/` (`--id-type=INTEGER`, `--overwrite-destination`),
2. starts Neo4j and waits for Bolt,
3. creates uniqueness constraints on the ids (`customerId`, `orderId`, `productId`, `categoryId`,
   `brandId`). Each constraint comes with an index, which is required for id lookups. All other indexes
   come in `perf/indexes-explain`,
4. sets `Product.stock` from `data/<size>/relational/inventory.csv` (see U4 below),
5. compares node counts per label and relationship counts per type with the CSV files (exits non-zero on a mismatch).

### Measured import times

On a 4-vCPU cloud container with `DB_CPUS=2`, `DB_MEMORY=4g`, Neo4j 5.26 Community.

| Size | Nodes | Relationships | neo4j-admin (tool) | Import step (incl. container) | Startup | Constraints | Stock | Total |
|------|-------|---------------|--------------------|------------------|---------|-------------|-------|-------|
| S | 5,056 | 15,936 | 2.6 s | 6.8 s | 10.9 s | 0.7 s | 0.6 s | 19.0 s |
| M | 227,556 | 728,126 | 9.0 s | 13.6 s | 11.1 s | 1.6 s | 0.7 s | 27.0 s |

"neo4j-admin (tool)" is the time the tool reports itself. The import step adds about 4 s to start
the one-off container and JVM, and startup is the server restart after the offline import.

## Graph model

```
(:Customer {customerId, first_name, last_name, email, phone, created_at})
    -[:PLACED]->
(:Order {orderId, status, total_amount, created_at,
         payment_method, payment_status, paid_at, carrier, shipped_at, delivered_at})
    -[:CONTAINS {quantity, unit_price}]->
(:Product:<Category> {productId, sku, name, price, release_date, stock, <specs...>})
    -[:BELONGS_TO]->(:Category {categoryId, name})
    -[:MADE_BY]->   (:Brand {brandId, name, country})

(:Product:CPU)-[:COMPATIBLE_WITH {via: 'socket'}]->(:Product:Motherboard)
(:Product:RAM)-[:COMPATIBLE_WITH {via: 'memory_type'}]->(:Product:Motherboard)
```

Every product also has its category as a label (`:CPU`, `:GPU`, `:Motherboard`, …). Specs such as
`socket`, `vram_gb` and `boost_clock_ghz` are typed node properties. Payment and shipment are
properties of `Order`. Addresses, suppliers and per-supplier inventory are not part of the graph.

## Scenarios

[`scenarios.py`](scenarios.py) implements the 24 scenarios of
[`docs/scenarios.md`](../../docs/scenarios.md) in Cypher with the official `neo4j` driver. It has the
same `SCENARIOS` dict (`C1`…`D6`), the same `Scenario(name, run, setup, cleanup, params)` entries and the
same parameters as the SQL engines. `run(driver, params)` is the part to time.

Smoke test, which runs every scenario once and checks the graph is unchanged afterwards (node counts
per label, relationship counts and sums, product and order property aggregates):

```bash
python databases/neo4j/scenarios.py            # all 24
python databases/neo4j/scenarios.py --only R6,D3
```

### Differences from the relational scenarios

| ID | Graph version |
|----|---------------|
| C3, C5 | No `address_id`: orders aren't linked to addresses in the graph model. Payment fields are set on the `Order` node. |
| C6, D3 | Addresses exist only for these scenarios, as `(:Customer)-[:HAS_ADDRESS]->(:Address)` nodes outside the imported model. |
| D3 | No FK cascade: the query deletes the customer, its orders and addresses explicitly with `DETACH DELETE`, and the `CONTAINS` relationships go with the orders. |
| D4, D6 | `DETACH DELETE` removes the node with its relationships. Specs are properties, so they go with the product. |
| R6 | Follows `COMPATIBLE_WITH {via: 'socket'}` relationships, built from matching sockets at generation time, instead of a join on attributes. |
| U3 | Sets a node property (`p.boost_clock_ghz`) instead of updating an attribute row. |
| U4 | The graph has no per-supplier inventory. `load.py` stores the stock of each product at its lowest-id supplier (the row the SQL version decrements) as `Product.stock`, and U4 decrements that property. |
| U5 | The shipment is `carrier`, `tracking_number` and `shipped_at` on the `Order` node, not a separate row. |
| U6 | `payment_status` is an `Order` property, so a single `SET` changes both the order and payment status. |
