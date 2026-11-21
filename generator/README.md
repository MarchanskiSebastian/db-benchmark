# Data generator

Generates one dataset of the computer parts store and writes it, in a single pass, for all four
engines, so every engine is benchmarked on identical data. Output is deterministic for a given
`--seed` (and Faker version).

Schema: [`SCHEMA.md`](SCHEMA.md) (12 tables, PKs, FKs, guaranteed rules) and the reference DDL
[`schema.sql`](schema.sql).

## Usage

```bash
pip install -r requirements.txt
python -m generator --size s --out data/s --seed 42
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--size {s,m,l,xl}` | required | dataset size, see below |
| `--out DIR` | `data/<size>` | output directory |
| `--seed N` | `42` | random seed |
| `--quiet` | off | hide progress output |

Tests (generate size S and check counts, FKs, totals, dates, compatibility, determinism):

```bash
pytest generator/tests
```

## Sizes

The size is the row count of the largest table, `order_items`; other tables scale with it.

| Table | Rule | S | M | L | XL |
|-------|------|---|---|---|----|
| order_items | size | 10,000 | 500,000 | 1,000,000 | 10,000,000 |
| orders | 40% of items (avg. 2.5 items per order) | 4,000 | 200,000 | 400,000 | 4,000,000 |
| payments | 1 per order | 4,000 | 200,000 | 400,000 | 4,000,000 |
| shipments | shipped / delivered orders (~80%) | ~3,200 | ~160,000 | ~320,000 | ~3.2M |
| customers | 5% of items | 500 | 25,000 | 50,000 | 500,000 |
| addresses | 1–3 per customer | ~740 | ~37,600 | ~75,000 | ~750,000 |
| products | 0.5% of items, min 500, max 50,000 | 500 | 2,500 | 5,000 | 50,000 |
| product_attributes | 3–7 per product | ~2,400 | ~12,000 | ~24,000 | ~240,000 |
| inventory | 1–3 suppliers per product | ~1,000 | ~5,000 | ~10,000 | ~100,000 |
| suppliers | items / 20,000, min 20, max 200 | 20 | 25 | 50 | 200 |
| categories / brands | fixed | 14 / 42 | 14 / 42 | 14 / 42 | 14 / 42 |

The product floor keeps every category, socket and memory type present in the small dataset.

## Data

- 14 categories: CPU, GPU, Motherboard, RAM, SSD, HDD, PSU, Case, Cooler, Monitor, Laptop,
  Keyboard, Mouse, Headset. Products are spread evenly across them.
- Product names, specs and prices come from model tables in [`catalog.py`](catalog.py), e.g.
  `AMD Ryzen 7 7800X3D Box`, `MSI GeForce RTX 4070 Super Gaming X Trio 12GB`,
  `ASUS TUF Gaming B760M DDR4`, `Corsair Vengeance 32GB (2x16GB) DDR5-6000 CL30`.
  Names repeat across products (same model, different SKU); `sku` is unique.
- Compatibility is real: CPU `socket` and motherboard `socket` use the same values, and RAM
  `memory_type` matches motherboard `memory_type` (AM4 / LGA1200 = DDR4, AM5 / LGA1851 = DDR5,
  LGA1700 boards are either).
- Product popularity follows a Zipf-like curve, so there are clear best-sellers.
- Orders span 2021-01-01 to 2026-06-30; payment, shipment and delivery dates follow the order date.

## Output layout

```
data/<size>/
├── relational/   PostgreSQL + MySQL: one CSV per table
├── mongo/        MongoDB: NDJSON per collection
└── neo4j/        Neo4j: neo4j-admin import CSVs + *_header.csv
```

**relational/**: `<table>.csv` for all 12 tables. Header row, UTF-8, ISO 8601 timestamps
(`2025-09-05T08:59:28`, UTC), decimal money (`293.96`), booleans as `1`/`0`, NULL as an empty field
(PostgreSQL `COPY ... CSV` reads it as NULL; MySQL `LOAD DATA` needs `NULLIF(@col, '')`).
Specs are rows in `product_attributes.csv`.

**mongo/**: Extended JSON (relaxed), one document per line, for `mongoimport`:
- `products.ndjson`: category and brand embedded, nested `specs`, `stock` per supplier
- `customers.ndjson`: embedded `addresses`
- `orders.ndjson`: embedded `items` (with product name and category), `payment` and `shipment` (or null)

```bash
mongoimport --db store --collection orders --file data/s/mongo/orders.ndjson
```

**neo4j/**: nodes `Customer`, `Order`, `Product` (+ category label, e.g. `Product;CPU`),
`Category`, `Brand`; relationships `PLACED`, `CONTAINS` (quantity, unit_price), `BELONGS_TO`,
`MADE_BY`, `COMPATIBLE_WITH` (`via` = socket or memory_type). Payment and shipment fields are
properties of `Order`. Specs are typed product properties; empty cells mean no property.

```bash
neo4j-admin database import full neo4j \
  --nodes=Customer=customers_header.csv,customers.csv \
  --nodes=Order=orders_header.csv,orders.csv \
  --nodes=products_header.csv,products.csv \
  --nodes=Category=categories_header.csv,categories.csv \
  --nodes=Brand=brands_header.csv,brands.csv \
  --relationships=PLACED=placed_header.csv,placed.csv \
  --relationships=CONTAINS=contains_header.csv,contains.csv \
  --relationships=BELONGS_TO=belongs_to_header.csv,belongs_to.csv \
  --relationships=MADE_BY=made_by_header.csv,made_by.csv \
  --relationships=COMPATIBLE_WITH=compatible_with_header.csv,compatible_with.csv
```

## Performance

Customers and orders are generated and written one at a time through buffered CSV / NDJSON
writers; only reference data and products (≤ 50k) are kept in memory, so memory stays flat.

Measured on a 4-vCPU cloud container (Python 3.13, `--seed 42`, all three formats):

| Size | Time | Peak memory | relational | mongo | neo4j | Total |
|------|------|-------------|-----------|-------|-------|-------|
| S | 0.6 s | 30 MB | 1.1 MB | 3.4 MB | 0.9 MB | 5.3 MB |
| M | 9.8 s | 45 MB | 52 MB | 155 MB | 38 MB | 244 MB |
| L (estimate) | ~20 s | ~50 MB | ~105 MB | ~310 MB | ~80 MB | ~0.5 GB |
| XL (estimate) | ~3.5 min | ~100 MB | ~1 GB | ~3 GB | ~0.9 GB | ~5 GB |

L and XL are linear extrapolations from M, not measured. XL also has a larger `compatible_with.csv`
because it has 50k products.
