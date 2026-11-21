-- Engine-agnostic reference DDL (PostgreSQL flavour) for the computer parts store.
-- Per-engine DDL in databases/* is adapted from this file.
-- Only primary keys, unique constraints and foreign keys are declared: secondary indexes are
-- added later in the index phase so "before" measurements start from a clean baseline.
-- Note: InnoDB (MySQL) creates an index on every foreign key automatically, PostgreSQL does not.

CREATE TABLE customers (
    id          INTEGER      PRIMARY KEY,
    first_name  VARCHAR(50)  NOT NULL,
    last_name   VARCHAR(50)  NOT NULL,
    email       VARCHAR(120) NOT NULL UNIQUE,
    phone       VARCHAR(20)  NOT NULL,
    created_at  TIMESTAMP    NOT NULL
);

CREATE TABLE addresses (
    id           INTEGER      PRIMARY KEY,
    customer_id  INTEGER      NOT NULL REFERENCES customers (id) ON DELETE CASCADE,
    street       VARCHAR(120) NOT NULL,
    city         VARCHAR(60)  NOT NULL,
    postal_code  VARCHAR(10)  NOT NULL,
    country      CHAR(2)      NOT NULL,
    is_default   BOOLEAN      NOT NULL
);

CREATE TABLE categories (
    id    INTEGER     PRIMARY KEY,
    name  VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE brands (
    id       INTEGER     PRIMARY KEY,
    name     VARCHAR(40) NOT NULL UNIQUE,
    country  CHAR(2)     NOT NULL
);

CREATE TABLE suppliers (
    id       INTEGER      PRIMARY KEY,
    name     VARCHAR(100) NOT NULL,
    email    VARCHAR(120) NOT NULL,
    country  CHAR(2)      NOT NULL
);

CREATE TABLE products (
    id            INTEGER       PRIMARY KEY,
    sku           VARCHAR(20)   NOT NULL UNIQUE,
    name          VARCHAR(160)  NOT NULL,
    category_id   INTEGER       NOT NULL REFERENCES categories (id),
    brand_id      INTEGER       NOT NULL REFERENCES brands (id),
    price         NUMERIC(10,2) NOT NULL CHECK (price > 0),
    release_date  DATE          NOT NULL
);

-- Category-specific specs (socket, vram_gb, capacity_gb, ...) as key/value rows.
CREATE TABLE product_attributes (
    product_id  INTEGER     NOT NULL REFERENCES products (id) ON DELETE CASCADE,
    name        VARCHAR(40) NOT NULL,
    value       VARCHAR(80) NOT NULL,
    PRIMARY KEY (product_id, name)
);

CREATE TABLE inventory (
    product_id   INTEGER     NOT NULL REFERENCES products (id) ON DELETE CASCADE,
    supplier_id  INTEGER     NOT NULL REFERENCES suppliers (id),
    warehouse    VARCHAR(40) NOT NULL,
    quantity     INTEGER     NOT NULL CHECK (quantity >= 0),
    updated_at   TIMESTAMP   NOT NULL,
    PRIMARY KEY (product_id, supplier_id)
);

CREATE TABLE orders (
    id            INTEGER       PRIMARY KEY,
    customer_id   INTEGER       NOT NULL REFERENCES customers (id) ON DELETE CASCADE,
    address_id    INTEGER       NOT NULL REFERENCES addresses (id),
    status        VARCHAR(12)   NOT NULL
                  CHECK (status IN ('pending', 'paid', 'shipped', 'delivered', 'cancelled')),
    total_amount  NUMERIC(12,2) NOT NULL,
    created_at    TIMESTAMP     NOT NULL
);

CREATE TABLE order_items (
    id          INTEGER       PRIMARY KEY,
    order_id    INTEGER       NOT NULL REFERENCES orders (id) ON DELETE CASCADE,
    product_id  INTEGER       NOT NULL REFERENCES products (id),
    quantity    INTEGER       NOT NULL CHECK (quantity > 0),
    unit_price  NUMERIC(10,2) NOT NULL,
    UNIQUE (order_id, product_id)
);

CREATE TABLE payments (
    id        INTEGER       PRIMARY KEY,
    order_id  INTEGER       NOT NULL UNIQUE REFERENCES orders (id) ON DELETE CASCADE,
    method    VARCHAR(20)   NOT NULL,
    status    VARCHAR(12)   NOT NULL CHECK (status IN ('pending', 'completed', 'refunded')),
    amount    NUMERIC(12,2) NOT NULL,
    paid_at   TIMESTAMP
);

CREATE TABLE shipments (
    id               INTEGER     PRIMARY KEY,
    order_id         INTEGER     NOT NULL UNIQUE REFERENCES orders (id) ON DELETE CASCADE,
    carrier          VARCHAR(20) NOT NULL,
    tracking_number  VARCHAR(30) NOT NULL,
    shipped_at       TIMESTAMP   NOT NULL,
    delivered_at     TIMESTAMP
);
