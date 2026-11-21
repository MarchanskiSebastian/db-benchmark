# Benchmark runner

Runs the same 24 scenarios (6 per CRUD operation) against PostgreSQL, MySQL, MongoDB and
Neo4j. Each scenario runs 3 times per engine and dataset size, timed on the client side
with `time.perf_counter()`.

## Scenarios

### Create

| ID | Scenario                                                  |
|----|-----------------------------------------------------------|
| C1 | Insert a single customer                                  |
| C2 | Insert a product with its category-specific attributes    |
| C3 | Place an order with 3 items (transaction)                 |
| C4 | Bulk insert 10k customers                                 |
| C5 | Bulk insert 10k orders with items                         |
| C6 | Add a review / rating for a product                       |

### Read

| ID | Scenario                                                       |
|----|----------------------------------------------------------------|
| R1 | Find products by category and price range                      |
| R2 | Find GPUs with at least 12 GB VRAM (attribute filter)          |
| R3 | Orders of a customer with items and product names              |
| R4 | Top 10 best-selling products in the last 30 days               |
| R5 | Motherboards compatible with a given CPU (socket match)        |
| R6 | Monthly revenue per category (aggregation)                     |

### Update

| ID | Scenario                                                  |
|----|-----------------------------------------------------------|
| U1 | Change the price of a single product                      |
| U2 | Raise prices by 10% for one brand in one category         |
| U3 | Change order status to shipped and set shipment date      |
| U4 | Decrease inventory after an order                         |
| U5 | Update a product attribute (e.g. boost clock)             |
| U6 | Bulk update status of orders older than 1 year            |

### Delete

| ID | Scenario                                                  |
|----|-----------------------------------------------------------|
| D1 | Delete a single review                                    |
| D2 | Delete a cancelled order with its items                   |
| D3 | Delete a customer with addresses and orders (cascade)     |
| D4 | Delete discontinued products and their attributes         |
| D5 | Delete shipments older than 2 years                       |
| D6 | Delete out-of-stock inventory rows                        |

## Method

- Dataset is reloaded (or restored from snapshot) before write scenarios so every run
  starts from the same state.
- Scenarios run before and after adding indexes.
- Plans captured with `EXPLAIN` / `explain()` / `PROFILE` for selected scenarios.

## Output

One CSV row per run, written to `results/raw/` (git-ignored); aggregated results go to `results/`.

```
engine,dataset_size,scenario_id,operation,indexed,run,duration_ms,rows_affected,timestamp
postgres,1M,R1,read,false,1,42.7,318,2026-11-20T12:00:00
```
