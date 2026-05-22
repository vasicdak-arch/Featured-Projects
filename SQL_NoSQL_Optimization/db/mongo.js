const { MongoClient, ObjectId } = require('mongodb');

const uri = process.env.MONGODB_URI || 'mongodb://localhost:27017';
const dbName = process.env.MONGODB_DB || 'appdb';

const client = new MongoClient(uri, {
  serverApi: {
    version: '1',
    strict: true,
    deprecationErrors: true,
  },
});

let db;

async function connect() {
  if (!db) {
    await client.connect();
    db = client.db(dbName);
  }
  return db;
}

async function getProductBySku(sku) {
  const database = await connect();
  return database.collection('product_catalog').findOne({ sku });
}

async function getCustomerActivity(customerId, limit = 20) {
  const database = await connect();
  return database
    .collection('customer_activity')
    .find({ customerId })
    .sort({ createdAt: -1 })
    .limit(limit)
    .toArray();
}

module.exports = {
  ObjectId,
  getProductBySku,
  getCustomerActivity,
};
