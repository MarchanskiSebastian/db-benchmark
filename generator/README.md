# Data generator

Generates one shared dataset (CSV in `data/`) that is loaded into all four engines, so every
engine is benchmarked on identical data. Uses `faker` with a fixed seed for reproducibility.

## Planned relational schema (12 tables)

| # | Table                | Key columns                                                              |
|---|----------------------|--------------------------------------------------------------------------|
| 1 | `customers`          | id, first_name, last_name, email (unique), phone, created_at            |
| 2 | `addresses`          | id, customer_id → customers, street, city, postal_code, country, is_default |
| 3 | `categories`         | id, name (CPU, GPU, Motherboard, RAM, SSD, Monitor, Laptop, Peripheral), parent_id |
| 4 | `brands`             | id, name (AMD, Intel, NVIDIA, ASUS, MSI, Corsair, Samsung, ...), country |
| 5 | `suppliers`          | id, name, email, country                                                 |
| 6 | `products`           | id, sku (unique), name, category_id, brand_id, price, release_date      |
| 7 | `product_attributes` | product_id → products, name, value (e.g. `socket=AM5`, `vram_gb=12`)    |
| 8 | `inventory`          | product_id, supplier_id, quantity, warehouse, updated_at                |
| 9 | `orders`             | id, customer_id, address_id, status, total_amount, created_at           |
| 10 | `order_items`       | order_id, product_id, quantity, unit_price (largest table)              |
| 11 | `payments`          | id, order_id, method, amount, status, paid_at                           |
| 12 | `shipments`         | id, order_id, carrier, tracking_number, shipped_at, delivered_at        |

`reviews` (product_id, customer_id, rating, comment, created_at) is an optional 13th table.
It stays out of the core schema to keep exactly 12 tables and is added only if time allows.

## Realistic product data

Names and specs come from per-category templates rather than random words, for example:

| Category    | Example name                    | Attributes                                   |
|-------------|---------------------------------|----------------------------------------------|
| CPU         | AMD Ryzen 7 7800X3D             | cores, threads, socket (AM5/LGA1700), base_ghz, tdp_w |
| GPU         | MSI GeForce RTX 4070 Ventus 12G | vram_gb, memory_type, tdp_w, length_mm      |
| Motherboard | ASUS TUF B650-PLUS              | socket, chipset, form_factor, memory_type   |
| RAM         | Corsair Vengeance 32GB DDR5-6000 | capacity_gb, memory_type, speed_mhz, modules |
| SSD         | Samsung 990 PRO 2TB             | capacity_gb, interface (NVMe/SATA), read_mbps |
| Monitor     | Dell S2721DGF 27"               | size_in, resolution, refresh_hz, panel      |
| Laptop      | Lenovo Legion 5 16"             | cpu, ram_gb, storage_gb, gpu, screen_in     |
| Peripheral  | Logitech G Pro X Superlight     | type, connection, dpi                       |

Socket and memory type values are shared between CPUs, motherboards and RAM so that
compatibility (`COMPATIBLE_WITH` in Neo4j) can be derived from the data.

## Dataset sizes

Sizes refer to rows in the largest table (`order_items`); other tables scale proportionally.

| Size   | order_items | orders (approx.) | customers (approx.) |
|--------|-------------|------------------|---------------------|
| small  | 500k        | 170k             | 50k                 |
| medium | 1M          | 340k             | 100k                |
| large  | 10M         | 3.4M             | 1M                  |

## Planned steps

1. Static reference data: categories, brands, suppliers, product templates.
2. Generate products and attributes from templates.
3. Generate customers, addresses, orders, items, payments, shipments.
4. Write CSVs to `data/<size>/`, one file per table.
5. Per-engine loaders (in `databases/*`) read the same CSVs.
