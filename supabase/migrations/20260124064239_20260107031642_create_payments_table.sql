/*
  # Payment Transactions Schema

  1. New Tables
    - `payment_transactions`
      - `id` (uuid, primary key) - Transaction identifier
      - `user_id` (uuid, foreign key) - Reference to users table
      - `subscription_id` (uuid, foreign key) - Reference to subscriptions table
      - `stripe_payment_intent_id` (text) - Stripe payment intent ID
      - `amount` (numeric) - Payment amount
      - `currency` (text) - Payment currency
      - `status` (text) - Payment status
      - `payment_method` (text) - Payment method used
      - `created_at` (timestamptz) - Transaction creation timestamp

  2. Security
    - Enable RLS
    - Users can read their own transactions
    - Service role can manage all transactions
*/

-- Create payment transactions table
CREATE TABLE IF NOT EXISTS payment_transactions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  subscription_id uuid REFERENCES subscriptions(id) ON DELETE SET NULL,
  stripe_payment_intent_id text UNIQUE,
  telegram_payment_id text,
  amount numeric NOT NULL,
  currency text NOT NULL DEFAULT 'USD',
  status text NOT NULL DEFAULT 'pending',
  payment_method text DEFAULT 'stripe',
  metadata jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz DEFAULT now(),
  CONSTRAINT valid_status CHECK (status IN ('pending', 'succeeded', 'failed', 'refunded')),
  CONSTRAINT valid_payment_method CHECK (payment_method IN ('stripe', 'telegram', 'other'))
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_payment_transactions_user_id ON payment_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_status ON payment_transactions(status);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_created_at ON payment_transactions(created_at);

-- Enable RLS
ALTER TABLE payment_transactions ENABLE ROW LEVEL SECURITY;

-- Payment transactions policies
CREATE POLICY "Users can read own transactions"
  ON payment_transactions FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "Service can manage all transactions"
  ON payment_transactions FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Function to get subscription revenue stats
CREATE OR REPLACE FUNCTION get_revenue_stats(days integer DEFAULT 30)
RETURNS TABLE (
  total_revenue numeric,
  total_transactions bigint,
  active_subscriptions bigint,
  new_subscriptions bigint
) AS $$
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
$$ LANGUAGE plpgsql SECURITY DEFINER;