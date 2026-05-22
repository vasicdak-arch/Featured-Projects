require('dotenv').config();

const express = require('express');
const NodeCache = require('node-cache');
const postgres = require('./db/postgres');
const mongo = require('./db/mongo');

const app = express();
const cache = new NodeCache({ stdTTL: Number(process.env.CACHE_TTL_SECONDS || 30) });
const port = Number(process.env.PORT || 3000);

app.use(express.json());

app.get('/health', (_req, res) => {
  res.json({ status: 'ok', service: 'sql-nosql-optimization' });
});

app.get('/orders/recent', async (req, res) => {
  const customerId = Number(req.query.customer_id);
  if (!customerId) {
    return res.status(400).json({ error: 'customer_id query parameter is required' });
  }

  try {
    const result = await postgres.getRecentOrdersByCustomer(customerId);
    res.json(result.rows);
  } catch (error) {
    console.error('Failed to fetch recent orders:', error);
    res.status(500).json({ error: 'Failed to fetch recent orders' });
  }
});

app.get('/orders/:id', async (req, res) => {
  const orderId = Number(req.params.id);
  if (!orderId) {
    return res.status(400).json({ error: 'order id must be numeric' });
  }

  try {
    const order = await postgres.getOrderDetails(orderId);
    if (!order) {
      return res.status(404).json({ error: 'order not found' });
    }
    res.json(order);
  } catch (error) {
    console.error('Failed to fetch order details:', error);
    res.status(500).json({ error: 'Failed to fetch order details' });
  }
});

app.get('/products/:sku', async (req, res) => {
  const sku = req.params.sku;
  if (!sku) {
    return res.status(400).json({ error: 'sku is required' });
  }

  try {
    const product = await mongo.getProductBySku(sku);
    if (!product) {
      return res.status(404).json({ error: 'product not found' });
    }
    res.json(product);
  } catch (error) {
    console.error('Failed to fetch product by SKU:', error);
    res.status(500).json({ error: 'Failed to fetch product' });
  }
});

app.get('/cache/products/:sku', async (req, res) => {
  const sku = req.params.sku;
  if (!sku) {
    return res.status(400).json({ error: 'sku is required' });
  }

  const cacheKey = `product:${sku}`;
  const cached = cache.get(cacheKey);
  if (cached) {
    return res.json({ source: 'cache', data: cached });
  }

  try {
    const product = await mongo.getProductBySku(sku);
    if (!product) {
      return res.status(404).json({ error: 'product not found' });
    }
    cache.set(cacheKey, product);
    res.json({ source: 'mongo', data: product });
  } catch (error) {
    console.error('Failed to fetch cached product:', error);
    res.status(500).json({ error: 'Failed to fetch product' });
  }
});

app.get('/activity/customer/:customerId', async (req, res) => {
  const customerId = req.params.customerId;
  if (!customerId) {
    return res.status(400).json({ error: 'customerId is required' });
  }

  try {
    const activity = await mongo.getCustomerActivity(customerId, Number(req.query.limit) || 20);
    res.json(activity);
  } catch (error) {
    console.error('Failed to fetch customer activity:', error);
    res.status(500).json({ error: 'Failed to fetch customer activity' });
  }
});

app.listen(port, () => {
  console.log(`API server listening on port ${port}`);
});
