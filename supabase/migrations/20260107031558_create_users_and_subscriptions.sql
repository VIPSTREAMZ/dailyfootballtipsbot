/*
  # Football Tipping Bot - Users and Subscriptions Schema

  1. New Tables
    - `users`
      - `id` (uuid, primary key) - Unique user identifier
      - `telegram_id` (text, unique) - Telegram user ID
      - `username` (text) - Telegram username
      - `first_name` (text) - User's first name
      - `email` (text, unique) - Email address for web access
      - `stripe_customer_id` (text) - Stripe customer ID
      - `created_at` (timestamptz) - Account creation timestamp
      - `updated_at` (timestamptz) - Last update timestamp

    - `subscriptions`
      - `id` (uuid, primary key) - Subscription identifier
      - `user_id` (uuid, foreign key) - Reference to users table
      - `plan_type` (text) - Subscription plan (monthly, yearly)
      - `status` (text) - Subscription status (active, cancelled, expired)
      - `stripe_subscription_id` (text) - Stripe subscription ID
      - `valid_from` (timestamptz) - Subscription start date
      - `valid_until` (timestamptz) - Subscription end date
      - `created_at` (timestamptz) - Subscription creation timestamp
      - `updated_at` (timestamptz) - Last update timestamp

  2. Security
    - Enable RLS on all tables
    - Users can read their own data
    - Users can read their own subscriptions
    - Service role required for creating/updating subscriptions
*/

-- Create users table
CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_id text UNIQUE,
  username text,
  first_name text,
  email text UNIQUE,
  stripe_customer_id text UNIQUE,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  plan_type text NOT NULL DEFAULT 'monthly',
  status text NOT NULL DEFAULT 'active',
  stripe_subscription_id text UNIQUE,
  valid_from timestamptz DEFAULT now(),
  valid_until timestamptz NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  CONSTRAINT valid_plan CHECK (plan_type IN ('monthly', 'yearly', 'lifetime')),
  CONSTRAINT valid_status CHECK (status IN ('active', 'cancelled', 'expired', 'trial'))
);

-- Create index for faster subscription lookups
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_valid_until ON subscriptions(valid_until);
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- Users table policies
CREATE POLICY "Users can read own data"
  ON users FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

CREATE POLICY "Users can update own data"
  ON users FOR UPDATE
  TO authenticated
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

CREATE POLICY "Service can manage all users"
  ON users FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Anonymous can create users"
  ON users FOR INSERT
  TO anon
  WITH CHECK (true);

-- Subscriptions table policies
CREATE POLICY "Users can read own subscriptions"
  ON subscriptions FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "Service can manage all subscriptions"
  ON subscriptions FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER subscriptions_updated_at
  BEFORE UPDATE ON subscriptions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();
