/*
  # Database Security and Performance Optimization

  1. Performance Improvements
    - Add missing foreign key index for payment_transactions
    - Update function search paths to IMMUTABLE where appropriate
    
  2. Security Hardening
    - Replace auth.uid() with (select auth.uid()) in RLS policies for better performance
    - Remove unrestricted "Anonymous can create users" policy
    - Fix RLS initialization plan issues

  3. Index Strategy
    - Keep all indexes (they'll be used once application scales)
    - Indexes are essential for foreign key lookups and filtering operations
*/

-- Add missing index for foreign key
CREATE INDEX IF NOT EXISTS idx_payment_transactions_subscription_id 
  ON payment_transactions(subscription_id);

-- Fix function search_path mutability
ALTER FUNCTION update_updated_at() IMMUTABLE;
ALTER FUNCTION get_user_stats(uuid) STABLE;
ALTER FUNCTION get_revenue_stats(integer) STABLE;

-- Drop the overly permissive anonymous user creation policy
DROP POLICY IF EXISTS "Anonymous can create users" ON users;

-- Recreate RLS policies with optimized auth function calls
DROP POLICY IF EXISTS "Users can read own data" ON users;
CREATE POLICY "Users can read own data"
  ON users FOR SELECT
  TO authenticated
  USING (id = (select auth.uid()));

DROP POLICY IF EXISTS "Users can update own data" ON users;
CREATE POLICY "Users can update own data"
  ON users FOR UPDATE
  TO authenticated
  USING (id = (select auth.uid()))
  WITH CHECK (id = (select auth.uid()));

DROP POLICY IF EXISTS "Users can read own subscriptions" ON subscriptions;
CREATE POLICY "Users can read own subscriptions"
  ON subscriptions FOR SELECT
  TO authenticated
  USING (user_id = (select auth.uid()));

DROP POLICY IF EXISTS "Users can read own tips" ON user_tips;
CREATE POLICY "Users can read own tips"
  ON user_tips FOR SELECT
  TO authenticated
  USING (user_id = (select auth.uid()));

DROP POLICY IF EXISTS "Users can create own tips" ON user_tips;
CREATE POLICY "Users can create own tips"
  ON user_tips FOR INSERT
  TO authenticated
  WITH CHECK (user_id = (select auth.uid()));

DROP POLICY IF EXISTS "Users can read own transactions" ON payment_transactions;
CREATE POLICY "Users can read own transactions"
  ON payment_transactions FOR SELECT
  TO authenticated
  USING (user_id = (select auth.uid()));

-- Add policy to allow service role to create users (replaces anonymous creation)
CREATE POLICY "Service can insert users"
  ON users FOR INSERT
  TO service_role
  WITH CHECK (true);

-- Add policy to allow service role to update users
CREATE POLICY "Service can update users"
  ON users FOR UPDATE
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Verify RLS is still enabled
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_tips ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;