"""Deterministic, streaming generation of the store dataset.

Only reference data, products and two small per-customer arrays live in memory; customers
and orders are produced one at a time and handed to the writers, so memory stays flat
regardless of size. Each stage has its own RNG derived from the seed, so changing one stage
does not shift the random stream of the others.
"""

import random
import re
import sys
import time
from array import array
from collections import namedtuple
from datetime import date, datetime, timezone

from faker import Faker

from . import catalog

SIZES = {"s": 10_000, "m": 500_000, "l": 1_000_000, "xl": 10_000_000}

START = int(datetime(2021, 1, 1, tzinfo=timezone.utc).timestamp())
END = int(datetime(2026, 6, 30, tzinfo=timezone.utc).timestamp())
DAY = 86_400

ORDER_STATUSES = ["delivered", "shipped", "paid", "pending", "cancelled"]
ORDER_STATUS_WEIGHTS = [70, 10, 8, 5, 7]
PAYMENT_METHODS = ["credit_card", "paypal", "apple_pay", "bank_transfer", "gift_card"]
PAYMENT_METHOD_WEIGHTS = [50, 25, 10, 10, 5]
CARRIERS = ["UPS", "FedEx", "USPS", "DHL"]
WAREHOUSES = ["Newark NJ", "Dallas TX", "Reno NV", "Chicago IL"]
SUPPLIER_COUNTRIES = ["US", "US", "US", "CA", "MX", "TW", "CN", "DE"]

Product = namedtuple("Product", "id sku name category_id brand_id price release_date specs")
Catalog = namedtuple("Catalog", "categories brands suppliers products inventory")


def counts_for(order_items):
    """Row counts of the scaled tables for a given number of order items."""
    return {
        "order_items": order_items,
        "orders": order_items * 2 // 5,
        "customers": max(order_items // 20, 100),
        # Floor keeps every category and socket represented in the small dataset.
        "products": min(max(order_items // 200, 500), 50_000),
        "suppliers": min(max(order_items // 20_000, 20), 200),
    }


def iso(ts):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ts))


def _ascii(text):
    return re.sub(r"[^a-z]", "", text.lower())


class Progress:
    def __init__(self, label, total, enabled):
        self.label, self.total, self.enabled = label, total, enabled
        self.step = max(total // 100, 1)
        self.start = time.perf_counter()

    def update(self, done):
        if self.enabled and (done % self.step == 0 or done == self.total):
            elapsed = time.perf_counter() - self.start
            print(f"\r  {self.label:<10} {done * 100 // self.total:3d}%  {done:>11,}/{self.total:,}  {elapsed:6.1f}s",
                  end="\n" if done == self.total else "", file=sys.stderr, flush=True)


class Generator:
    def __init__(self, order_items, seed):
        self.seed = seed
        self.counts = counts_for(order_items)
        self.fake = Faker("en_US")
        self.fake.seed_instance(seed)
        # Faker is slow per call, so draw value pools once and sample them with the stage RNGs.
        self.first_names = [self.fake.first_name() for _ in range(1000)]
        self.last_names = [self.fake.last_name() for _ in range(1000)]
        self.streets = [self.fake.street_address() for _ in range(5000)]
        self.cities = [(self.fake.city(), self.fake.zipcode()) for _ in range(1000)]
        self.domains = ["gmail.com", "outlook.com", "yahoo.com", "icloud.com", "proton.me"]
        self.customer_created = array("q")
        self.customer_first_address = array("q")
        self.customer_address_count = array("b")

    def _rng(self, stage):
        return random.Random(f"{self.seed}:{stage}")

    def catalog(self):
        rng = self._rng("catalog")
        categories = [(i, name) for i, name in enumerate(catalog.CATEGORIES, 1)]
        category_ids = {name: i for i, name in categories}
        brands = [(i, name, country) for i, (name, country) in enumerate(catalog.BRANDS.items(), 1)]
        brand_ids = {name: i for i, name, _ in brands}

        suppliers = []
        for i in range(1, self.counts["suppliers"] + 1):
            name = f"{self.fake.company()} Distribution"
            suppliers.append((i, name, f"sales@{_ascii(name)[:20]}.com", rng.choice(SUPPLIER_COUNTRIES)))

        products = []
        per_category = {name: 0 for name in catalog.CATEGORIES}
        release_start = date(2020, 1, 1).toordinal()
        release_end = date(2026, 3, 1).toordinal()
        for i in range(1, self.counts["products"] + 1):
            category = catalog.CATEGORIES[(i - 1) % len(catalog.CATEGORIES)]
            brand, name, specs, price = catalog.make_product(category, rng, per_category[category])
            per_category[category] += 1
            sku = f"{catalog.SKU_PREFIX[category]}-{i:06d}"
            released = date.fromordinal(rng.randint(release_start, release_end)).isoformat()
            products.append(Product(i, sku, name, category_ids[category], brand_ids[brand], price, released, specs))

        inventory = []
        supplier_ids = range(1, len(suppliers) + 1)
        for p in products:
            for supplier_id in sorted(rng.sample(supplier_ids, rng.randint(1, 3))):
                quantity = 0 if rng.random() < 0.05 else rng.randint(1, 500)
                updated = iso(rng.randint(END - 90 * DAY, END))
                inventory.append((p.id, supplier_id, rng.choice(WAREHOUSES), quantity, updated))

        return Catalog(categories, brands, suppliers, products, inventory)

    def customers(self, progress=False):
        """Yield (customer_row, address_rows) and remember what orders need about each customer."""
        rng = self._rng("customers")
        total = self.counts["customers"]
        bar = Progress("customers", total, progress)
        address_id = 1
        for i in range(1, total + 1):
            first = rng.choice(self.first_names)
            last = rng.choice(self.last_names)
            email = f"{_ascii(first)}.{_ascii(last)}.{i}@{rng.choice(self.domains)}"
            phone = f"+1-{rng.randint(201, 989)}-{rng.randint(200, 999)}-{rng.randint(0, 9999):04d}"
            created = rng.randint(START, END - 30 * DAY)
            n_addresses = rng.choices([1, 2, 3], weights=[60, 30, 10])[0]

            self.customer_created.append(created)
            self.customer_first_address.append(address_id)
            self.customer_address_count.append(n_addresses)

            addresses = []
            for a in range(n_addresses):
                city, postal = rng.choice(self.cities)
                addresses.append((address_id, i, rng.choice(self.streets), city, postal, "US", a == 0))
                address_id += 1
            yield (i, first, last, email, phone, iso(created)), addresses
            bar.update(i)

    def orders(self, products, progress=False):
        """Yield (order, items, payment, shipment_or_None); requires customers() to have run."""
        rng = self._rng("orders")
        total_orders = self.counts["orders"]
        remaining_items = self.counts["order_items"]
        n_customers = len(self.customer_created)
        bar = Progress("orders", total_orders, progress)

        # Zipf-like popularity over a shuffled product order gives realistic best-sellers.
        ranked = list(products)
        rng.shuffle(ranked)
        cum_weights, acc = [], 0.0
        for rank in range(len(ranked)):
            acc += 1 / (rank + 1) ** 0.8
            cum_weights.append(acc)

        item_id = shipment_id = 1
        for order_id in range(1, total_orders + 1):
            orders_left = total_orders - order_id
            # Mean of randint(1, 4) is 2.5 = items/orders; clamping makes the total exact.
            k = min(max(rng.randint(1, 4), remaining_items - 5 * orders_left), remaining_items - orders_left, 5)
            remaining_items -= k

            customer = rng.randrange(n_customers)
            address_id = self.customer_first_address[customer] + rng.randrange(self.customer_address_count[customer])
            created = rng.randint(self.customer_created[customer], END)
            status = rng.choices(ORDER_STATUSES, weights=ORDER_STATUS_WEIGHTS)[0]

            picked = []
            while len(picked) < k:
                product = rng.choices(ranked, cum_weights=cum_weights)[0]
                if product not in picked:
                    picked.append(product)
            items, total = [], 0
            for product in picked:
                quantity = rng.choices([1, 2, 3], weights=[80, 15, 5])[0]
                items.append((item_id, order_id, product.id, quantity, product.price))
                total += quantity * product.price
                item_id += 1

            method = rng.choices(PAYMENT_METHODS, weights=PAYMENT_METHOD_WEIGHTS)[0]
            paid = None if status == "pending" else created + rng.randint(60, DAY)
            payment_status = {"pending": "pending", "cancelled": "refunded"}.get(status, "completed")
            payment = (order_id, order_id, method, payment_status, total, iso(paid) if paid else None)

            shipment = None
            if status in ("shipped", "delivered"):
                shipped = paid + rng.randint(4 * 3600, 3 * DAY)
                delivered = shipped + rng.randint(DAY, 5 * DAY) if status == "delivered" else None
                tracking = f"{rng.getrandbits(64):016X}"
                shipment = (shipment_id, order_id, rng.choice(CARRIERS), tracking, iso(shipped),
                            iso(delivered) if delivered else None)
                shipment_id += 1

            order = (order_id, customer + 1, address_id, status, total, iso(created))
            yield order, items, payment, shipment
            bar.update(order_id)


def generate(order_items, seed, writers, progress=False):
    """Generate the dataset once and pass every entity to all writers."""
    gen = Generator(order_items, seed)
    cat = gen.catalog()
    for w in writers:
        w.catalog(cat)
    for customer, addresses in gen.customers(progress):
        for w in writers:
            w.customer(customer, addresses)
    for order, items, payment, shipment in gen.orders(cat.products, progress):
        for w in writers:
            w.order(order, items, payment, shipment)
    for w in writers:
        w.close()
    return gen.counts
