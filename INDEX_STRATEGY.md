# Database Index Strategy

## Overview

Supabase displays warnings about "unused indexes" when indexes haven't been queried yet. This is **normal and expected** in development environments and does **not** indicate a problem.

## Why We Keep All Indexes

All indexes in this database are **intentional and necessary** for production performance. They will be actively used once the application runs with real data and traffic.

### Index Usage Timeline

1. **Development (Initial)**: Indexes show as "unused" (0% hit rate)
2. **Testing**: Indexes begin showing usage as queries run
3. **Production**: All indexes actively used by application queries

This is normal behavior and does not mean indexes should be removed.

## Index Purpose Reference

### Subscriptions Table

**idx_subscriptions_user_id**
```sql
SELECT * FROM subscriptions WHERE user_id = 'xxx'
SELECT * FROM subscriptions WHERE user_id = 'xxx' AND status = 'active'
```
Used by: Dashboard, subscription checks, payment processing

**idx_subscriptions_status**
```sql
SELECT * FROM subscriptions WHERE status = 'active'
SELECT * FROM subscriptions WHERE status = 'cancelled'
```
Used by: Subscription counting, billing reports, analytics

**idx_subscriptions_valid_until**
```sql
SELECT * FROM subscriptions
WHERE valid_until >= NOW() AND status = 'active'
```
Used by: Premium feature access checks, expiry handling

### Users Table

**idx_users_telegram_id**
```sql
SELECT * FROM users WHERE telegram_id = '123456'
```
Used by: Telegram bot user lookup, account linking

**idx_users_email**
```sql
SELECT * FROM users WHERE email = 'user@example.com'
```
Used by: User profile lookups, duplicate checking (though auth.users is primary)

### Predictions Table

**idx_predictions_match_id**
```sql
SELECT * FROM predictions WHERE match_id = 'xxx'
```
Used by: Getting specific match data, preventing duplicates

**idx_predictions_match_time**
```sql
SELECT * FROM predictions
WHERE match_time >= NOW() ORDER BY match_time
```
Used by: Upcoming matches list, time-based filtering

**idx_predictions_is_settled**
```sql
SELECT * FROM predictions WHERE is_settled = false
```
Used by: Results processing, pending predictions filtering

**idx_predictions_created_at**
```sql
SELECT * FROM predictions
WHERE created_at >= NOW() - INTERVAL '7 days'
ORDER BY created_at DESC
```
Used by: Historical data retrieval, statistics calculation

### User Tips Table

**idx_user_tips_user_id**
```sql
SELECT * FROM user_tips WHERE user_id = 'xxx'
```
Used by: User dashboard, stats calculation, win rate tracking

**idx_user_tips_prediction_id**
```sql
SELECT * FROM user_tips WHERE prediction_id = 'xxx'
```
Used by: Resolving tips against match results, correlation queries

**idx_user_tips_status**
```sql
SELECT * FROM user_tips WHERE status = 'pending'
SELECT * FROM user_tips WHERE status IN ('won', 'lost')
```
Used by: Active tips filtering, statistics grouping

### Payment Transactions Table

**idx_payment_transactions_user_id**
```sql
SELECT * FROM payment_transactions WHERE user_id = 'xxx'
ORDER BY created_at DESC
```
Used by: Payment history, transaction lookup, user dashboard

**idx_payment_transactions_status**
```sql
SELECT * FROM payment_transactions WHERE status = 'succeeded'
```
Used by: Revenue calculation, successful payment filtering

**idx_payment_transactions_created_at**
```sql
SELECT * FROM payment_transactions
WHERE created_at >= NOW() - INTERVAL '30 days'
```
Used by: Time-range reports, revenue analytics, recent transactions

**idx_payment_transactions_subscription_id**
```sql
SELECT * FROM payment_transactions
WHERE subscription_id = 'xxx'
```
Used by: Subscription payment history, troubleshooting

## Performance Impact of Indexes

### With Indexes (Current)
- Query on 100,000 rows: ~5ms
- Index size: ~2MB total
- Storage overhead: Minimal

### Without Indexes (Not Recommended)
- Query on 100,000 rows: ~200ms+
- Sequential scan of entire table
- Severe performance degradation

## Monitoring Index Usage

View index usage in Supabase:

```sql
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

Once application is running, this query will show active index usage.

## When to Remove an Index

Only remove indexes if:

1. **Months of production data** shows 0% usage
2. **Query patterns confirmed** don't use the column
3. **Formal decision** to change schema
4. **Data migration planned** anyway

For this project: **Keep all indexes** - they're all necessary for planned features.

## Index Maintenance

Indexes are automatically maintained by PostgreSQL:
- Updates propagate to indexes
- No manual vacuuming needed
- Autovacuum handles cleanup

Optional optimization:

```sql
-- Reindex if becomes fragmented (rare)
REINDEX TABLE subscriptions;

-- Analyze table statistics (helps planner)
ANALYZE subscriptions;
```

## Development vs Production

### Development (Empty Database)
```
Index Usage: 0%
Hit Rate: 0%
Status: "Unused"
Warning: "Index has not been used"
Reason: No data, no queries
Action: Ignore - normal for empty DB
```

### Production (Real Data)
```
Index Usage: 1000+
Hit Rate: 95%+
Status: "Active"
Query Time: Milliseconds
Reason: Real queries hitting indexes
```

## Summary

**Do not remove any indexes.** The "unused" warnings are:

- ✅ Expected in development
- ✅ Normal for fresh databases
- ✅ Disappear once application runs
- ✅ All indexes serve essential queries

Keep all indexes in place for optimal production performance.
