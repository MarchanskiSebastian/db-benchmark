"""Output writers. Each receives the same entities from generate() and writes one format."""

import csv
from pathlib import Path

TABLES = {
    "customers": ["id", "first_name", "last_name", "email", "phone", "created_at"],
    "addresses": ["id", "customer_id", "street", "city", "postal_code", "country", "is_default"],
    "categories": ["id", "name"],
    "brands": ["id", "name", "country"],
    "suppliers": ["id", "name", "email", "country"],
    "products": ["id", "sku", "name", "category_id", "brand_id", "price", "release_date"],
    "product_attributes": ["product_id", "name", "value"],
    "inventory": ["product_id", "supplier_id", "warehouse", "quantity", "updated_at"],
    "orders": ["id", "customer_id", "address_id", "status", "total_amount", "created_at"],
    "order_items": ["id", "order_id", "product_id", "quantity", "unit_price"],
    "payments": ["id", "order_id", "method", "status", "amount", "paid_at"],
    "shipments": ["id", "order_id", "carrier", "tracking_number", "shipped_at", "delivered_at"],
}

BUFFER = 1 << 20


def money(cents):
    return f"{cents // 100}.{cents % 100:02d}"


def attr_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


class _CsvFiles:
    def __init__(self, directory):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.files, self.writers = {}, {}

    def open(self, name, header=None):
        f = open(self.dir / f"{name}.csv", "w", newline="", encoding="utf-8", buffering=BUFFER)
        self.files[name] = f
        self.writers[name] = csv.writer(f)
        if header:
            self.writers[name].writerow(header)
        return self.writers[name]

    def close(self):
        for f in self.files.values():
            f.close()


class RelationalWriter:
    """One CSV per table with a header row, for PostgreSQL COPY and MySQL LOAD DATA.

    NULL is an empty unquoted field and booleans are 1/0, which both engines accept.
    """

    def __init__(self, directory):
        self.out = _CsvFiles(directory)
        self.w = {table: self.out.open(table, columns) for table, columns in TABLES.items()}

    def catalog(self, cat):
        self.w["categories"].writerows(cat.categories)
        self.w["brands"].writerows(cat.brands)
        self.w["suppliers"].writerows(cat.suppliers)
        for p in cat.products:
            self.w["products"].writerow((p.id, p.sku, p.name, p.category_id, p.brand_id, money(p.price), p.release_date))
            self.w["product_attributes"].writerows((p.id, k, attr_value(v)) for k, v in p.specs.items())
        self.w["inventory"].writerows(cat.inventory)

    def customer(self, customer, addresses):
        self.w["customers"].writerow(customer)
        self.w["addresses"].writerows(a[:6] + (int(a[6]),) for a in addresses)

    def order(self, order, items, payment, shipment):
        self.w["orders"].writerow(order[:4] + (money(order[4]),) + order[5:])
        self.w["order_items"].writerows(i[:4] + (money(i[4]),) for i in items)
        self.w["payments"].writerow(payment[:4] + (money(payment[4]),) + payment[5:])
        if shipment:
            self.w["shipments"].writerow(shipment)

    def close(self):
        self.out.close()
