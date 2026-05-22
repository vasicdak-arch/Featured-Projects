-- PostgreSQL normalized schema for transactional workloads

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    inventory_count INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(customer_id),
    order_status TEXT NOT NULL,
    total_amount NUMERIC(12, 2) NOT NULL,
    placed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id),
    product_id INT NOT NULL REFERENCES products(product_id),
    unit_price NUMERIC(12, 2) NOT NULL,
    quantity INT NOT NULL,
    line_total NUMERIC(12, 2) GENERATED ALWAYS AS (unit_price * quantity) STORED
);

CREATE TABLE product_categories (
    category_id SERIAL PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE,
    parent_category_id INT REFERENCES product_categories(category_id)
);

-- Indexes for performance and access patterns
CREATE INDEX idx_orders_customer_placed_at ON orders(customer_id, placed_at DESC);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_customers_email ON customers(email);

-- Example reporting / lookups
-- SELECT o.*, c.email
-- FROM orders o
-- JOIN customers c ON c.customer_id = o.customer_id
-- WHERE o.placed_at >= NOW() - INTERVAL '7 days';

-- Query tuning notes:
-- 1. Avoid SELECT * when joining large tables.
-- 2. Use covering indexes for frequent filter / sort columns.
-- 3. Denormalize only when read performance justifies it.
