"""Output writers. Each receives the same entities from generate() and writes one format."""

import csv
import json
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


def mongo_date(value):
    return {"$date": f"{value}Z"} if value else None


class MongoWriter:
    """NDJSON in MongoDB Extended JSON (relaxed), loadable with mongoimport.

    products embed specs and stock, customers embed addresses, and orders embed items,
    payment and shipment, the read-optimised document model planned for MongoDB.
    """

    def __init__(self, directory):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.files = {
            name: open(self.dir / f"{name}.ndjson", "w", encoding="utf-8", buffering=BUFFER)
            for name in ("products", "customers", "orders")
        }
        self.encode = json.JSONEncoder(ensure_ascii=False, separators=(",", ":")).encode

    def _write(self, collection, doc):
        self.files[collection].write(self.encode(doc) + "\n")

    def catalog(self, cat):
        categories = dict(cat.categories)
        brands = {i: name for i, name, _ in cat.brands}
        suppliers = {s[0]: s[1] for s in cat.suppliers}
        stock = {}
        for product_id, supplier_id, warehouse, quantity, updated in cat.inventory:
            stock.setdefault(product_id, []).append({
                "supplier_id": supplier_id, "supplier": suppliers[supplier_id], "warehouse": warehouse,
                "quantity": quantity, "updated_at": mongo_date(updated),
            })
        # Kept for embedding product name and category into order items.
        self.products = {p.id: (p.name, categories[p.category_id]) for p in cat.products}
        for p in cat.products:
            self._write("products", {
                "_id": p.id, "sku": p.sku, "name": p.name,
                "category": {"id": p.category_id, "name": categories[p.category_id]},
                "brand": {"id": p.brand_id, "name": brands[p.brand_id]},
                "price": p.price / 100, "release_date": mongo_date(f"{p.release_date}T00:00:00"),
                "specs": p.specs, "stock": stock[p.id],
            })

    def customer(self, customer, addresses):
        cid, first, last, email, phone, created = customer
        self._write("customers", {
            "_id": cid, "first_name": first, "last_name": last, "email": email, "phone": phone,
            "created_at": mongo_date(created),
            "addresses": [
                {"address_id": a[0], "street": a[2], "city": a[3], "postal_code": a[4],
                 "country": a[5], "is_default": a[6]}
                for a in addresses
            ],
        })

    def order(self, order, items, payment, shipment):
        oid, customer_id, address_id, status, total, created = order
        doc = {
            "_id": oid, "customer_id": customer_id, "address_id": address_id, "status": status,
            "total_amount": total / 100, "created_at": mongo_date(created),
            "items": [
                {"item_id": i[0], "product_id": i[2], "name": self.products[i[2]][0],
                 "category": self.products[i[2]][1], "quantity": i[3], "unit_price": i[4] / 100}
                for i in items
            ],
            "payment": {"payment_id": payment[0], "method": payment[2], "status": payment[3],
                        "amount": payment[4] / 100, "paid_at": mongo_date(payment[5])},
            "shipment": None,
        }
        if shipment:
            doc["shipment"] = {"shipment_id": shipment[0], "carrier": shipment[2], "tracking_number": shipment[3],
                               "shipped_at": mongo_date(shipment[4]), "delivered_at": mongo_date(shipment[5])}
        self._write("orders", doc)

    def close(self):
        for f in self.files.values():
            f.close()
