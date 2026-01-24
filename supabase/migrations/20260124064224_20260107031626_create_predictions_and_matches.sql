/*
  # Football Predictions and Matches Schema

  1. New Tables
    - `predictions`
      - `id` (uuid, primary key) - Prediction identifier
      - `match_id` (text, unique) - External match identifier
      - `home_team` (text) - Home team name
      - `away_team` (text) - Away team name
      - `prediction_type` (text) - Type of prediction (pre_match, inplay)
      - `home_prob` (numeric) - Probability of home win
      - `draw_prob` (numeric) - Probability of draw
      - `away_prob` (numeric) - Probability of away win
      - `recommended_bet` (text) - Recommended bet side
      - `edge` (numeric) - Edge value for the bet
      - `odds_home` (numeric) - Bookmaker home odds
      - `odds_draw` (numeric) - Bookmaker draw odds
      - `odds_away` (numeric) - Bookmaker away odds
      - `match_time` (timestamptz) - Match start time
      - `actual_result` (text) - Actual match result (home, draw, away)
      - `final_score_home` (integer) - Final home score
      - `final_score_away` (integer) - Final away score
      - `is_settled` (boolean) - Whether prediction has been settled
      - `created_at` (timestamptz) - Prediction creation timestamp
      - `updated_at` (timestamptz) - Last update timestamp

    - `user_tips`
      - `id` (uuid, primary key) - Tip identifier
      - `user_id` (uuid, foreign key) - Reference to users table
      - `prediction_id` (uuid, foreign key) - Reference to predictions table
      - `bet_side` (text) - User's bet choice (home, draw, away)
      - `stake` (numeric) - User's stake amount
      - `odds` (numeric) - Odds at time of bet
      - `status` (text) - Tip status (pending, won, lost)
      - `profit` (numeric) - Profit/loss amount
      - `created_at` (timestamptz) - Tip creation timestamp

  2. Security
    - Enable RLS on all tables
    - Predictions are readable by all authenticated users
    - Users can read their own tips
    - Users can create their own tips
    - Service role can manage all data
*/

-- Create predictions table
CREATE TABLE IF NOT EXISTS predictions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  match_id text NOT NULL UNIQUE,
  home_team text NOT NULL,
  away_team text NOT NULL,
  prediction_type text NOT NULL DEFAULT 'pre_match',
  home_prob numeric NOT NULL DEFAULT 0,
  draw_prob numeric NOT NULL DEFAULT 0,
  away_prob numeric NOT NULL DEFAULT 0,
  recommended_bet text,
  edge numeric DEFAULT 0,
  odds_home numeric,
  odds_draw numeric,
  odds_away numeric,
  match_time timestamptz,
  actual_result text,
  final_score_home integer,
  final_score_away integer,
  is_settled boolean DEFAULT false,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now(),
  CONSTRAINT valid_prediction_type CHECK (prediction_type IN ('pre_match', 'inplay')),
  CONSTRAINT valid_actual_result CHECK (actual_result IS NULL OR actual_result IN ('home', 'draw', 'away'))
);

-- Create user tips table
CREATE TABLE IF NOT EXISTS user_tips (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  prediction_id uuid NOT NULL REFERENCES predictions(id) ON DELETE CASCADE,
  bet_side text NOT NULL,
  stake numeric NOT NULL DEFAULT 0,
  odds numeric NOT NULL,
  status text NOT NULL DEFAULT 'pending',
  profit numeric DEFAULT 0,
  created_at timestamptz DEFAULT now(),
  CONSTRAINT valid_bet_side CHECK (bet_side IN ('home', 'draw', 'away')),
  CONSTRAINT valid_status CHECK (status IN ('pending', 'won', 'lost', 'void'))
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_predictions_match_id ON predictions(match_id);
CREATE INDEX IF NOT EXISTS idx_predictions_match_time ON predictions(match_time);
CREATE INDEX IF NOT EXISTS idx_predictions_is_settled ON predictions(is_settled);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at);
CREATE INDEX IF NOT EXISTS idx_user_tips_user_id ON user_tips(user_id);
CREATE INDEX IF NOT EXISTS idx_user_tips_prediction_id ON user_tips(prediction_id);
CREATE INDEX IF NOT EXISTS idx_user_tips_status ON user_tips(status);

-- Enable RLS
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_tips ENABLE ROW LEVEL SECURITY;

-- Predictions policies
CREATE POLICY "Anyone can read predictions"
  ON predictions FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Service can manage predictions"
  ON predictions FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- User tips policies
CREATE POLICY "Users can read own tips"
  ON user_tips FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

CREATE POLICY "Users can create own tips"
  ON user_tips FOR INSERT
  TO authenticated
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "Service can manage all tips"
  ON user_tips FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- Triggers for updated_at
CREATE TRIGGER predictions_updated_at
  BEFORE UPDATE ON predictions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- Function to calculate user statistics
CREATE OR REPLACE FUNCTION get_user_stats(p_user_id uuid)
RETURNS TABLE (
  total_tips bigint,
  won_tips bigint,
  lost_tips bigint,
  pending_tips bigint,
  total_profit numeric,
  win_rate numeric
) AS $$
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
$$ LANGUAGE plpgsql SECURITY DEFINER;