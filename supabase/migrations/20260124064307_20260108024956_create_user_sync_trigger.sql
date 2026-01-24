/*
  # User Sync Trigger

  1. New Function
    - `handle_new_user()` - Automatically creates public.users record when auth user is created
    
  2. New Trigger
    - `on_auth_user_created` - Triggers when new user signs up via Supabase auth
    
  Note: This replaces the removed anonymous user creation policy with automatic sync
*/

-- Function to create user record in public.users when auth user is created
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER
SECURITY DEFINER SET search_path = public
LANGUAGE plpgsql
AS $$
BEGIN
  INSERT INTO public.users (id, email, created_at, updated_at)
  VALUES (
    new.id,
    new.email,
    now(),
    now()
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN new;
END;
$$;

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Create trigger for new user creation
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Note: The handle_new_user function uses SECURITY DEFINER to bypass RLS
-- This allows automatic user creation even though the anonymous user policy was removed
-- Only triggered by Supabase auth.users table events