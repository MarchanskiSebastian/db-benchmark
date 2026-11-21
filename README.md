# db-benchmark

University project comparing the performance of four database engines on the same dataset:

| Model      | Engine      |
|------------|-------------|
| Relational | PostgreSQL 16 |
| Relational | MySQL 8     |
| Document   | MongoDB 7   |
| Graph      | Neo4j 5     |

## Scenario

The dataset is an online store selling computer parts and consumer electronics:
CPUs, GPUs, motherboards, RAM, SSDs, monitors, laptops and peripherals.

Product specifications differ per category (GPU: VRAM, CPU: cores and socket, SSD: capacity
and interface), so each engine stores them in its natural way:

- **PostgreSQL / MySQL** – a `product_attributes` table (or a JSON column).
- **MongoDB** – nested `specs` sub-documents inside product documents (semi-structured data).
- **Neo4j** – properties on `Product` nodes, plus compatibility as relationships, e.g.
  `(CPU)-[:COMPATIBLE_WITH]->(Motherboard)` via socket, and
  `(Customer)-[:PLACED]->(Order)-[:CONTAINS]->(Product)`.

## Scope

- Relational schema with 12 tables
- CRUD performance tests (24 scenarios, 6 per operation, 3 runs each)
- Index comparison (before / after)
- `EXPLAIN` / query plan analysis
- Scalability tests at 10k / 500k / 1M / 10M rows in the largest table (sizes S / M / L / XL)

## Tech stack

- Docker Compose (one stack per engine, identical CPU / memory limits)
- Python 3: `faker` (data generation), `psycopg2-binary`, `mysql-connector-python`,
  `pymongo`, `neo4j` (drivers), `pandas` + `matplotlib` (results and charts)

## Folder structure

```
db-benchmark/
├── data/          generated datasets (git-ignored)
├── databases/
│   ├── postgres/  docker-compose + schema
│   ├── mysql/     docker-compose + schema
│   ├── mongodb/   docker-compose + collections
│   └── neo4j/     docker-compose + graph model
├── generator/     data generator
├── benchmark/     benchmark runner and scenarios
├── results/       CSV results and charts (raw/ is git-ignored)
└── docs/          report and analysis
```

## How to run

```bash
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
docker compose -f databases/postgres/docker-compose.yml --env-file .env up -d
```

Repeat the last command for `mysql`, `mongodb` and `neo4j`.

Generate a dataset (sizes `s`, `m`, `l`, `xl`, see [`generator/README.md`](generator/README.md)):

```bash
python -m generator --size s --out data/s --seed 42
pytest generator/tests
```

Benchmark commands will be documented once the runner is implemented.

## Progress

| Branch                  | Area                                   | Status      |
|-------------------------|----------------------------------------|-------------|
| `feat/postgres-setup`   | PostgreSQL container and plan          | In review   |
| `feat/mysql-setup`      | MySQL container and plan               | In review   |
| `feat/mongodb-setup`    | MongoDB container and document model   | In review   |
| `feat/neo4j-setup`      | Neo4j container, import, scenarios     | ✅ Done     |
| `feat/data-generator`   | 12-table schema and data generator     | ✅ Done     |
| `feat/benchmark-runner` | 24 CRUD scenarios and runner           | In review   |
| indexes                 | Index comparison before / after        | Planned     |
| scalability             | S / M / L / XL tests                   | Planned     |
| report                  | Final report and charts                | Planned     |
