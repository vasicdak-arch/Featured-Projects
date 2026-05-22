const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.POSTGRES_CONNECTION_STRING || 'postgresql://postgres:postgres@localhost:5432/appdb',
});

async function query(text, params) {
  return pool.query(text, params);
}

async function getRecentOrdersByCustomer(customerId, limit = 10) {
  const text = `
    SELECT o.order_id, o.order_status, o.total_amount, o.placed_at, c.email
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE o.customer_id = $1
    ORDER BY o.placed_at DESC
    LIMIT $2
  `;
  return query(text, [customerId, limit]);
}

async function getOrderDetails(orderId) {
  const orderText = `
    SELECT o.order_id, o.order_status, o.total_amount, o.placed_at, c.customer_id, c.email, c.first_name, c.last_name
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE o.order_id = $1
  `;

  const orderResult = await query(orderText, [orderId]);
  if (!orderResult.rows.length) {
    return null;
  }

  const itemsText = `
    SELECT oi.order_item_id, oi.product_id, p.name AS product_name, oi.unit_price, oi.quantity, oi.line_total
    FROM order_items oi
    JOIN products p ON p.product_id = oi.product_id
    WHERE oi.order_id = $1
  `;

  const itemsResult = await query(itemsText, [orderId]);
  return {
    ...orderResult.rows[0],
    items: itemsResult.rows,
  };
}

module.exports = {
  query,
  getRecentOrdersByCustomer,
  getOrderDetails,
};
