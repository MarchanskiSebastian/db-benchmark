-- MySQL 8 adaptation of generator/schema.sql.
-- Primary keys, unique constraints and foreign keys only; secondary indexes come in
-- perf/indexes-explain. InnoDB still creates an index for every foreign key on its own,
-- which is unavoidable and documented in databases/mysql/README.md.
-- DATETIME instead of TIMESTAMP: no 2038 limit and no session time zone conversion.

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS shipments, payments, order_items, orders, inventory, product_attributes,
    products, suppliers, brands, categories, addresses, customers;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE customers (
    id          INT          NOT NULL PRIMARY KEY,
    first_name  VARCHAR(50)  NOT NULL,
    last_name   VARCHAR(50)  NOT NULL,
    email       VARCHAR(120) NOT NULL UNIQUE,
    phone       VARCHAR(20)  NOT NULL,
    created_at  DATETIME     NOT NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE addresses (
    id           INT          NOT NULL PRIMARY KEY,
    customer_id  INT          NOT NULL,
    street       VARCHAR(120) NOT NULL,
    city         VARCHAR(60)  NOT NULL,
    postal_code  VARCHAR(10)  NOT NULL,
    country      CHAR(2)      NOT NULL,
    is_default   BOOLEAN      NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE categories (
    id    INT         NOT NULL PRIMARY KEY,
    name  VARCHAR(30) NOT NULL UNIQUE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE brands (
    id       INT         NOT NULL PRIMARY KEY,
    name     VARCHAR(40) NOT NULL UNIQUE,
    country  CHAR(2)     NOT NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE suppliers (
    id       INT          NOT NULL PRIMARY KEY,
    name     VARCHAR(100) NOT NULL,
    email    VARCHAR(120) NOT NULL,
    country  CHAR(2)      NOT NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE products (
    id            INT           NOT NULL PRIMARY KEY,
    sku           VARCHAR(20)   NOT NULL UNIQUE,
    name          VARCHAR(160)  NOT NULL,
    category_id   INT           NOT NULL,
    brand_id      INT           NOT NULL,
    price         DECIMAL(10,2) NOT NULL CHECK (price > 0),
    release_date  DATE          NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories (id),
    FOREIGN KEY (brand_id) REFERENCES brands (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE product_attributes (
    product_id  INT         NOT NULL,
    name        VARCHAR(40) NOT NULL,
    value       VARCHAR(80) NOT NULL,
    PRIMARY KEY (product_id, name),
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE inventory (
    product_id   INT         NOT NULL,
    supplier_id  INT         NOT NULL,
    warehouse    VARCHAR(40) NOT NULL,
    quantity     INT         NOT NULL CHECK (quantity >= 0),
    updated_at   DATETIME    NOT NULL,
    PRIMARY KEY (product_id, supplier_id),
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE orders (
    id            INT           NOT NULL PRIMARY KEY,
    customer_id   INT           NOT NULL,
    address_id    INT           NOT NULL,
    status        VARCHAR(12)   NOT NULL
                  CHECK (status IN ('pending', 'paid', 'shipped', 'delivered', 'cancelled')),
    total_amount  DECIMAL(12,2) NOT NULL,
    created_at    DATETIME      NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE,
    FOREIGN KEY (address_id) REFERENCES addresses (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE order_items (
    id          INT           NOT NULL PRIMARY KEY,
    order_id    INT           NOT NULL,
    product_id  INT           NOT NULL,
    quantity    INT           NOT NULL CHECK (quantity > 0),
    unit_price  DECIMAL(10,2) NOT NULL,
    UNIQUE (order_id, product_id),
    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products (id)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE payments (
    id        INT           NOT NULL PRIMARY KEY,
    order_id  INT           NOT NULL UNIQUE,
    method    VARCHAR(20)   NOT NULL,
    status    VARCHAR(12)   NOT NULL CHECK (status IN ('pending', 'completed', 'refunded')),
    amount    DECIMAL(12,2) NOT NULL,
    paid_at   DATETIME      NULL,
    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;

CREATE TABLE shipments (
    id               INT         NOT NULL PRIMARY KEY,
    order_id         INT         NOT NULL UNIQUE,
    carrier          VARCHAR(20) NOT NULL,
    tracking_number  VARCHAR(30) NOT NULL,
    shipped_at       DATETIME    NOT NULL,
    delivered_at     DATETIME    NULL,
    FOREIGN KEY (order_id) REFERENCES orders (id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci;
