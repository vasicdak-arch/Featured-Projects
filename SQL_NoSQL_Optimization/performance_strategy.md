# Performance Strategy

This implementation highlights optimization patterns for a mixed SQL/NoSQL data platform.

## SQL Optimization

- Use normalized PostgreSQL schemas for transactional integrity and structured joins.
- Add targeted indexes for frequent filter and sort combinations, e.g. `orders(customer_id, placed_at DESC)`.
- Avoid expensive joins on wide result sets by selecting only required columns.
- Tune queries using `EXPLAIN ANALYZE` and add covering indexes where appropriate.
- Apply application-level write batching or partitioning for high-volume inserts.

## NoSQL Optimization

- Design MongoDB collections for query-driven access patterns rather than strict normalization.
- Embed related subdocuments when low-latency reads outweigh update complexity.
- Use sparse or partial indexes for large event collections to reduce index size.
- Maintain consistency at the application layer using careful document structure and validation.
- Enable horizontal scalability via shard keys chosen for evenly distributed high-cardinality fields.

## High-Traffic API Considerations

- Analyze slow queries with database-specific profiling tools.
- Introduce caching layers for repeated reads, such as Redis or in-memory object caches.
- Reduce load by refining schema relationships and denormalizing read-heavy attributes.
- Use read replicas for reporting or analytics workloads when PostgreSQL read scaling is needed.
- Monitor peak traffic and tune connection pools, query timeouts, and index usage continuously.
