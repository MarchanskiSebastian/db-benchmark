# Test scenarios

The single source of truth for the 24 CRUD scenarios. Every engine (PostgreSQL, MySQL, MongoDB,
Neo4j) implements all of them with the same IDs, parameters and semantics, so results are
directly comparable. IDs are fixed and never reused.

## Implementation contract

Each engine has `databases/<engine>/scenarios.py` exposing a `SCENARIOS` dict keyed by ID
(`"C1"` … `"D6"`). Each entry provides:

| Field | Signature | Timed | Purpose |
|-------|-----------|-------|---------|
| `run` | `(conn, params) -> result` | yes | the measured operation |
| `setup` | `(conn, params) -> params` | no | optional: create temp rows or snapshot values; returns params for `run`/`cleanup` |
| `cleanup` | `(conn, params) -> None` | no | optional: remove temp rows or restore snapshot values |
| `params` | `dict` | – | default parameters from this document |

`conn` is the engine's native connection or driver. `result` is a row count or a small list,
used only for sanity checks.

**Repeatability.** After `setup → run → cleanup` the database must be logically identical to
before, so every run of every scenario starts from the same state. Two techniques are used:

- **Temp rows**: new rows use ids from the reserved range `id ≥ 900000000` (above any generated
  id at every size). Creates insert there and cleanup deletes them. Deletes get their victims
  from `setup`, which inserts temp rows that match the delete condition.
- **Snapshot / restore**: updates read the affected values in `setup` and write them back in `cleanup`.

Parameters only use values that exist at every size (S–XL) for `--seed 42`: product `1` is always
a CPU (products cycle through categories), customer `1` owns address `1`, and all generated orders
are dated 2021-01-01 to 2026-06-30. Temp rows dated before 2020 can't collide with real data.

## Create

| ID | Name | Description | Parameters | Repeatability |
|----|------|-------------|------------|---------------|
| C1 | Single insert | Insert one customer. | `id=900000000`, name `Bench User`, email `bench.c1@example.com` | cleanup deletes the customer |
| C2 | Batch insert 1000 | Insert 1000 customers in one batch / transaction. | ids `900000000`–`900000999`, emails `bench.c2.<n>@example.com` | cleanup deletes the id range |
| C3 | Insert order with items | In one transaction: an order for customer `1` / address `1` with 3 items (products `1`, `2`, `3`, quantity 1, current price) and its payment; total = Σ items. | `order_id=900000000`, `customer_id=1`, `address_id=1`, `product_ids=[1,2,3]` | cleanup deletes order, items, payment |
| C4 | Insert product with specs | Insert a GPU with its category-specific specs (attribute rows / nested document / node properties) and its category and brand links. | `id=900000000`, category `GPU`, brand `MSI`, specs `chipset, gpu_vendor, vram_gb=16, memory_type, tdp_w, length_mm` | cleanup deletes the product and its specs |
| C5 | Batch insert orders | Insert 1000 orders for customer `1`, each with 2 items (products `1` and `2`) and a payment, in one transaction. | order ids `900000000`–`900000999` | cleanup deletes the id range |
| C6 | Insert customer with addresses | Insert one customer together with 2 addresses (one default). | `customer_id=900000000`, address ids `900000000`, `900000001` | cleanup deletes customer and addresses |

## Read

| ID | Name | Description | Parameters | Repeatability |
|----|------|-------------|------------|---------------|
| R1 | Read by primary key | Fetch one product with category and brand names. | `product_id=42` | read-only |
| R2 | Read by non-indexed field | All customers with a given last name (no index on `last_name`). | `last_name=Smith` | read-only |
| R3 | Range query + sort + limit | Products of a category in a price range, cheapest first, first 20. | category `GPU`, price `300`–`800`, `limit=20` | read-only |
| R4 | Aggregation | Top 10 best-selling products by quantity in a date window, excluding cancelled orders. | `from=2026-05-31T00:00:00`, `to=2026-06-30T00:00:00`, `limit=10` | read-only |
| R5 | Join / lookup | All orders of a customer with their items and product names, newest first. | `customer_id=1` | read-only |
| R6 | Compatible parts lookup | Motherboards compatible with a given CPU (same socket), cheapest first. | `cpu_id=1` | read-only |

## Update

| ID | Name | Description | Parameters | Repeatability |
|----|------|-------------|------------|---------------|
| U1 | Update one record | Set the price of one product. | `product_id=42`, `price=199.99` | snapshot / restore price |
| U2 | Bulk update by condition | Raise prices by 10% for all products of one brand in one category. | brand `MSI`, category `GPU`, `factor=1.10` | snapshot / restore prices |
| U3 | Update nested / attribute field | Change one spec of a product (attribute row / nested field / node property). | `product_id=1`, spec `boost_clock_ghz=6.2` | snapshot / restore value |
| U4 | Update stock after order | In one transaction, for every item of an order, decrease stock of that product at its lowest-id supplier by the item quantity (never below 0). | `order_id=1` | snapshot / restore stock |
| U5 | Ship an order | Set the lowest-id `paid` order to `shipped` and record its shipment (carrier, tracking number, `shipped_at`). | order resolved in setup, carrier `UPS`, `shipped_at=2026-06-30T12:00:00` | snapshot / restore status, remove shipment |
| U6 | Bulk status change | Cancel all `pending` orders created before a date and mark their payments `refunded`. | `before=2025-01-01T00:00:00` | snapshot / restore statuses |

## Delete

| ID | Name | Description | Parameters | Repeatability |
|----|------|-------------|------------|---------------|
| D1 | Delete one | Delete one customer by id. | setup inserts temp customer `900000000` | temp row |
| D2 | Delete by condition | Delete all customers with a given last name created before a date (non-indexed filter). | setup inserts 1000 temp customers with last name `Tempbench` and `created_at=2019-06-01`; condition: last name `Tempbench`, `created_at < 2020-01-01` | temp rows |
| D3 | Cascading delete | Delete a customer with all addresses, orders, items, payments and shipments. | setup inserts temp customer `900000000` with 2 addresses and 5 orders × 3 items, payments, shipments | temp rows |
| D4 | Delete product with specs | Delete a product with its specs, stock and category / brand links. | setup inserts temp product `900000000` like C4, with stock at 2 suppliers | temp rows |
| D5 | Delete old records | Delete all orders created before a date, with their items, payments and shipments. | setup inserts 500 temp orders for customer `1` dated `2019-06-01`, 2 items each; `before=2020-01-01T00:00:00` | temp rows (no real order is that old) |
| D6 | Delete one order | Delete a single order with its items, payment and shipment. | setup inserts temp order `900000000` like C3 plus a shipment | temp rows |

## Coverage

| Requirement | Scenario |
|-------------|----------|
| single insert / batch insert 1000 / order with items | C1 / C2 / C3 |
| read by primary key / non-indexed field | R1 / R2 |
| range query, sorting + limit | R3 |
| aggregation (top-selling products) | R4 |
| join / lookup (orders of a customer with items) | R5 |
| compatible parts lookup | R6 |
| update one / bulk by condition / nested attribute / stock after order | U1 / U2 / U3 / U4 |
| delete one / by condition / cascading / old records | D1 / D2 / D3 / D5 |

`reviews` is not part of the 12-table schema, so the review scenarios of the earlier plan in
`benchmark/README.md` are replaced by C4–C6 and D4/D6.
