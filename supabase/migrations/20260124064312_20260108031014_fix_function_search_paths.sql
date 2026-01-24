/*
  # Fix Function Search Path Mutability

  1. Security Fix
    - Recreate functions with explicit IMMUTABLE/STABLE and SET search_path
    - Prevents role-dependent search path variations
    - Improves performance and security

  Note: The "unused indexes" warnings are expected in development with empty database.
  Indexes will be actively used once application runs with real data and queries.
  Keeping all indexes is correct for production performance.
*/

-- Drop and recreate update_updated_at with proper search_path
DROP TRIGGER IF EXISTS users_updated_at ON users CASCADE;
DROP TRIGGER IF EXISTS subscriptions_updated_at ON subscriptions CASCADE;
DROP TRIGGER IF EXISTS predictions_updated_at ON predictions CASCADE;
DROP FUNCTION IF EXISTS update_updated_at();

CREATE FUNCTION update_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
IMMUTABLE
SET search_path = public
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

-- Recreate get_user_stats with proper search_path
DROP FUNCTION IF EXISTS get_user_stats(uuid);

CREATE FUNCTION get_user_stats(p_user_id uuid)
RETURNS TABLE (
  total_tips bigint,
  won_tips bigint,
  lost_tips bigint,
  pending_tips bigint,
  total_profit numeric,
  win_rate numeric
)
LANGUAGE plpgsql
STABLE
SET search_path = public
SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  SELECT
    COUNT(*) as total_tips,
    COUNT(*) FILTER (WHERE status = 'won') as won_tips,
    COUNT(*) FILTER (WHERE status = 'lost') as lost_tips,
    COUNT(*) FILTER (WHERE status = 'pending') as pending_tips,
    COALESCE(SUM(profit), 0) as total_profit,
    CASE
      WHEN COUNT(*) FILTER (WHERE status IN ('won', 'lost')) > 0
      THEN ROUND(
        (COUNT(*) FILTER (WHERE status = 'won')::numeric /
        COUNT(*) FILTER (WHERE status IN ('won', 'lost'))::numeric) * 100,
        2
      )
      ELSE 0
    END as win_rate
  FROM user_tips
  WHERE user_id = p_user_id;
END;
$$;

-- Recreate get_revenue_stats with proper search_path
DROP FUNCTION IF EXISTS get_revenue_stats(integer);

CREATE FUNCTION get_revenue_stats(days integer DEFAULT 30)
RETURNS TABLE (
  total_revenue numeric,
  total_transactions bigint,
  active_subscriptions bigint,
  new_subscriptions bigint
)
LANGUAGE plpgsql
STABLE
SET search_path = public
SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  SELECT
    COALESCE(SUM(pt.amount), 0) as total_revenue,
    COUNT(pt.id) as total_transactions,
    (SELECT COUNT(*) FROM subscriptions WHERE status = 'active') as active_subscriptions,
    (SELECT COUNT(*) FROM subscriptions WHERE created_at >= NOW() - (days || ' days')::interval) as new_subscriptions
  FROM payment_transactions pt
  WHERE pt.status = 'succeeded'
    AND pt.created_at >= NOW() - (days || ' days')::interval;
END;
$$;

-- Recreate triggers for updated_at
CREATE TRIGGER users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER subscriptions_updated_at
  BEFORE UPDATE ON subscriptions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER predictions_updated_at
  BEFORE UPDATE ON predictions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();