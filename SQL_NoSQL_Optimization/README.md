# SQL/NoSQL Optimization

This project demonstrates a backend data platform design that supports both relational and non-relational data models. It highlights:

- Normalized PostgreSQL schemas for transactional workloads
- Flexible MongoDB document collections for high-velocity, scalable reads
- Indexing and query optimization strategies
- Cache and schema design patterns for high-traffic APIs
- A sample Node.js API layer that integrates both PostgreSQL and MongoDB

## Overview

The system optimizes for both strong relational consistency and schema flexibility. PostgreSQL is used for ACID-safe business transactions and join-heavy reporting. MongoDB is used for low-latency reads, fast ingestion, and horizontal scalability.

## Contents

- `postgres_schema.sql` — normalized relational schema definitions and index recommendations
- `mongodb_collections.js` — example MongoDB collection models and indexing strategy
- `performance_strategy.md` — optimization notes on queries, joins, caching, and data modeling
- `server.js` — sample Express API server demonstrating mixed relational and document access
- `db/postgres.js` — PostgreSQL query helpers for order and customer access patterns
- `db/mongo.js` — MongoDB helpers for product catalog and customer activity queries
- `.env.example` — environment variables for local setup
- `docker-compose.yml` — optional Postgres and MongoDB services for local development

## Getting Started

1. Copy `.env.example` to `.env` and customize connection values.
2. Install dependencies:

```bash
npm install
```

3. Start the application:

```bash
npm start
```

4. Use the API endpoints:

- `GET /health`
- `GET /orders/recent?customer_id=123`
- `GET /orders/:id`
- `GET /products/:sku`
- `GET /cache/products/:sku`
- `GET /activity/customer/:customerId`

## Development Notes

- The API includes a simple in-memory caching layer for MongoDB product lookups.
- PostgreSQL queries are intentionally written to reduce expensive joins and return only relevant columns.
- MongoDB collections are modeled for read performance with query-driven shape and indexing.
- `docker-compose.yml` provides a quick local stack for testing Postgres and MongoDB together.
