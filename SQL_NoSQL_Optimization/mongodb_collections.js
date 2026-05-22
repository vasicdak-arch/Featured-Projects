// MongoDB collection design for flexible, high-velocity document storage
// Example using a schema-like model for clarity

const customerActivitySchema = {
  _id: 'ObjectId',
  customerId: 'ObjectId',
  email: 'string',
  sessionId: 'string',
  events: [
    {
      eventType: 'string',
      eventTime: 'date',
      metadata: 'object'
    }
  ],
  createdAt: 'date'
};

const productCatalogSchema = {
  _id: 'ObjectId',
  sku: 'string',
  name: 'string',
  category: 'string',
  price: 'number',
  available: 'boolean',
  attributes: 'object',
  tags: ['string'],
  updatedAt: 'date'
};

const orderSnapshotSchema = {
  _id: 'ObjectId',
  orderId: 'number',
  customerId: 'ObjectId',
  status: 'string',
  totalAmount: 'number',
  placedAt: 'date',
  shippingAddress: {
    line1: 'string',
    city: 'string',
    state: 'string',
    zip: 'string',
    country: 'string'
  },
  items: [
    {
      productId: 'ObjectId',
      name: 'string',
      quantity: 'number',
      price: 'number'
    }
  ],
  payment: {
    method: 'string',
    transactionId: 'string'
  },
  createdAt: 'date'
};

const indexes = [
  { collection: 'customer_activity', index: { customerId: 1, createdAt: -1 }, options: { background: true } },
  { collection: 'customer_activity', index: { sessionId: 1 }, options: { unique: false, background: true } },
  { collection: 'product_catalog', index: { sku: 1 }, options: { unique: true, background: true } },
  { collection: 'product_catalog', index: { category: 1, price: 1 }, options: { background: true } },
  { collection: 'order_snapshots', index: { customerId: 1, placedAt: -1 }, options: { background: true } },
  { collection: 'order_snapshots', index: { orderId: 1 }, options: { unique: true, background: true } }
];

module.exports = {
  customerActivitySchema,
  productCatalogSchema,
  orderSnapshotSchema,
  indexes
};
