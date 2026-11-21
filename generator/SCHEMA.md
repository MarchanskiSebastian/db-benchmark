# Relational schema

12 tables. The reference DDL is [`schema.sql`](schema.sql) (PostgreSQL flavour), adapted per engine later.
Money is `NUMERIC`, timestamps are UTC without a time zone, written as ISO 8601 (`2025-03-14T09:26:53`).

```
customers 1──* addresses
customers 1──* orders *──1 addresses
orders    1──* order_items *──1 products
orders    1──1 payments
orders    1──0..1 shipments
products  *──1 categories
products  *──1 brands
products  1──* product_attributes
products  1──* inventory *──1 suppliers
```

| # | Table | Columns | PK | FKs |
|---|-------|---------|----|-----|
| 1 | `customers` | id, first_name, last_name, email (unique), phone, created_at | id | – |
| 2 | `addresses` | id, customer_id, street, city, postal_code, country, is_default | id | customer_id → customers |
| 3 | `categories` | id, name (unique) | id | – |
| 4 | `brands` | id, name (unique), country | id | – |
| 5 | `suppliers` | id, name, email, country | id | – |
| 6 | `products` | id, sku (unique), name, category_id, brand_id, price, release_date | id | category_id → categories, brand_id → brands |
| 7 | `product_attributes` | product_id, name, value | (product_id, name) | product_id → products |
| 8 | `inventory` | product_id, supplier_id, warehouse, quantity, updated_at | (product_id, supplier_id) | product_id → products, supplier_id → suppliers |
| 9 | `orders` | id, customer_id, address_id, status, total_amount, created_at | id | customer_id → customers, address_id → addresses |
| 10 | `order_items` | id, order_id, product_id, quantity, unit_price; unique (order_id, product_id) | id | order_id → orders, product_id → products |
| 11 | `payments` | id, order_id (unique), method, status, amount, paid_at | id | order_id → orders |
| 12 | `shipments` | id, order_id (unique), carrier, tracking_number, shipped_at, delivered_at | id | order_id → orders |

`reviews` is left out to keep exactly 12 tables.

## Rules the generator guarantees

- Every FK points to an existing row. An order's `address_id` belongs to that order's customer.
- `orders.total_amount` = Σ `quantity × unit_price` of its items, and `payments.amount` = `total_amount`.
- `customers.created_at` ≤ `orders.created_at` ≤ `payments.paid_at` ≤ `shipments.shipped_at` ≤ `shipments.delivered_at`.
- Payment status follows order status: `pending` → `pending` (no `paid_at`), `cancelled` → `refunded`, otherwise `completed`.
- Only `shipped` and `delivered` orders have a shipment, and only `delivered` ones have `delivered_at`.
- CPU `socket` always exists on some motherboards, and RAM `memory_type` always matches some motherboards.
  Compatibility is derived from these attributes (`product_attributes` join in SQL, `COMPATIBLE_WITH` in Neo4j).

## Product attributes per category

| Category | Attributes |
|----------|------------|
| CPU | cores, threads, socket, base_clock_ghz, boost_clock_ghz, tdp_w, packaging |
| GPU | chipset, gpu_vendor, vram_gb, memory_type, tdp_w, length_mm |
| Motherboard | socket, chipset, form_factor, memory_type, memory_slots |
| RAM | memory_type, capacity_gb, modules, speed_mhz, cas_latency |
| SSD | capacity_gb, interface, form_factor, read_mbps |
| HDD | capacity_gb, rpm, cache_mb, interface, form_factor |
| PSU | wattage_w, efficiency, modular |
| Case | form_factor, color, fans_included, tempered_glass |
| Cooler | cooler_type, radiator_mm (AIO only), max_tdp_w, supported_sockets, color |
| Monitor | size_in, resolution, refresh_hz, panel, response_ms |
| Laptop | cpu, gpu, ram_gb, storage_gb, screen_in |
| Keyboard | layout, switch_type, connection, color |
| Mouse | dpi, weight_g, buttons, connection, color |
| Headset | connection, driver_mm, microphone, color |

Socket ↔ memory type: AM4 = DDR4, AM5 = DDR5, LGA1200 = DDR4, LGA1700 = DDR4 or DDR5 (board-specific), LGA1851 = DDR5.
