# MongoDB 7

## Start

```bash
docker compose -f databases/mongodb/docker-compose.yml --env-file .env up -d
```

## Planned document model

- `products`: one document per product with category, brand and a nested `specs`
  sub-document whose shape depends on the category (semi-structured data):
  ```json
  { "name": "GeForce RTX 4070", "category": "GPU", "brand": "NVIDIA", "price": 599.0,
    "specs": { "vram_gb": 12, "memory_type": "GDDR6X", "tdp_w": 200 } }
  ```
- `orders`: order documents with embedded `items` (product id, name, quantity, price),
  payment and shipment.
- `customers`: customer documents with embedded addresses.
- `reviews`: separate collection referencing product and customer ids.

## Planned steps

1. Load generated data with `insertMany` in batches.
2. Run CRUD scenarios without secondary indexes, then add indexes and rerun.
3. Capture plans with `explain("executionStats")`.
4. Repeat at 500k / 1M / 10M documents in the largest collection.
