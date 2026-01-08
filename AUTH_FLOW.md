# Authentication Flow

This document explains how authentication and user creation work in the Football Tips Bot.

## Architecture

The system uses **Supabase Auth** with automatic sync to a public users table:

```
Frontend SignUp → Supabase Auth → auth.users created → Trigger → public.users created
```

## User Creation Flow

### Step 1: Frontend Sign Up

User enters email and password on the login page:

```typescript
const { error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'secure-password-123'
});
```

### Step 2: Supabase Creates Auth User

Supabase automatically:
- Validates email format
- Hashes password with bcrypt
- Creates entry in `auth.users` table
- Generates JWT token
- Stores session in browser

### Step 3: Trigger Creates Public User Record

A PostgreSQL trigger (`on_auth_user_created`) automatically:
- Detects new row in `auth.users`
- Calls `handle_new_user()` function
- Creates corresponding record in `public.users`
- Sets `created_at` and `updated_at` timestamps

### Step 4: User Can Access Features

After signup completes:
- User can sign in with credentials
- User has row in both `auth.users` and `public.users`
- RLS policies allow user to access their own data
- User can subscribe to plans

## Sign In Flow

### Step 1: User Signs In

```typescript
const { error, data } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'secure-password-123'
});
```

### Step 2: Supabase Validates Credentials

- Looks up user by email in `auth.users`
- Compares password hash
- Returns JWT token if valid
- Creates session

### Step 3: Session Stored Locally

Browser stores:
- JWT access token
- Refresh token
- Session timestamp

### Step 4: Automatic Session Check

App automatically:
- Checks for existing session on load
- Listens for auth state changes
- Updates user state
- Redirects to login if expired

## Data Flow

### Public vs Private Tables

```
auth.users (Supabase Auth)         public.users (Our Database)
├── id (UUID)                      ├── id (same as auth.users)
├── email                          ├── email
├── password_hash                  ├── telegram_id (optional)
├── created_at                     ├── username (optional)
└── last_sign_in_at                ├── first_name (optional)
                                   ├── stripe_customer_id
                                   ├── created_at
                                   └── updated_at
```

### Automatic Sync

The trigger ensures `public.users` always has records for all authenticated users.

**Important**: Manual inserts to `public.users` are only allowed via service role (for admin operations). User self-service is only through Supabase auth.

## Authentication Methods

### Frontend Authentication

```typescript
import { supabase } from '../lib/supabase';

// Sign up
await supabase.auth.signUp({ email, password });

// Sign in
await supabase.auth.signInWithPassword({ email, password });

// Sign out
await supabase.auth.signOut();

// Get current user
const { data: { user } } = await supabase.auth.getUser();

// Get session
const { data: { session } } = await supabase.auth.getSession();
```

### Backend Authentication

```python
from supabase import create_client

# Using anon key (for public operations)
supabase = create_client(url, anon_key)

# Using service role key (for admin operations)
supabase = create_client(url, service_role_key)

# Get user from JWT token
user_id = request.headers.get('Authorization')
```

## Session Management

### Auto Refresh

Supabase automatically refreshes tokens:
- Tokens expire after 1 hour
- Refresh token extends session
- Automatic refresh happens transparently
- Manual refresh available if needed

### Session Events

Listen for auth changes:

```typescript
supabase.auth.onAuthStateChange((event, session) => {
  if (event === 'SIGNED_IN') {
    // User just signed in
  } else if (event === 'SIGNED_OUT') {
    // User signed out
  } else if (event === 'TOKEN_REFRESHED') {
    // Session refreshed
  }
});
```

### Session Timeout

- Sessions expire after 1 hour of inactivity
- User must sign in again
- Tokens automatically refresh on activity
- Long-running apps handle refresh transparently

## Security Measures

### Password Security
- Minimum 6 characters (configurable)
- Hashed with bcrypt (12 rounds)
- Never stored in plain text
- Never transmitted in URLs

### Session Security
- JWT tokens only (no cookies by default)
- Tokens stored in secure browser storage
- Tokens expire automatically
- Tokens refreshed transparently

### RLS Protection
- All user data protected by RLS policies
- Users can only access their own data
- Service role can access all data
- Policies verified for each query

### Email Verification (Optional)

Can be enabled to verify email ownership:

```sql
-- In Supabase dashboard: Authentication → Policies
-- Enable "Email Confirmations Required"
```

When enabled:
- Sign up requires email confirmation
- Confirmation link sent automatically
- User can't sign in until confirmed
- Resend link available

## Error Handling

### Common Errors

```typescript
try {
  const { error } = await supabase.auth.signUp({ email, password });

  if (error?.message.includes('already')) {
    // User already exists
  } else if (error?.message.includes('Invalid')) {
    // Invalid email format
  } else if (error) {
    // Other auth error
  }
} catch (err) {
  // Network error
}
```

### User-Friendly Messages

Map errors to user messages:

```typescript
const errorMessages: Record<string, string> = {
  'User already registered': 'Email already in use',
  'Invalid email': 'Invalid email format',
  'Password should be minimum 6 characters': 'Password too short',
  'Invalid login credentials': 'Wrong email or password',
  'Email not confirmed': 'Please confirm your email',
};
```

## Testing Authentication

### Test Sign Up
1. Go to login page
2. Enter email and password
3. Verify user created in Supabase Auth dashboard
4. Check `public.users` table for auto-created record

### Test Sign In
1. Sign in with credentials
2. Verify session created
3. Check dashboard loads with user data
4. Verify RLS restricts access properly

### Test Session Expiry
1. Sign in
2. Wait 1 hour (or wait for token refresh)
3. Verify token refreshes automatically
4. Verify user stays signed in

### Test Logout
1. Sign in
2. Click sign out
3. Verify redirected to home
4. Verify can't access dashboard without signing in

## Telegram Bot Authentication

Telegram bot uses different auth:

```python
# Bot stores user data with telegram_id
user = await get_or_create_user(
    telegram_id=message.from_user.id,
    username=message.from_user.username,
    first_name=message.from_user.first_name
)

# Bot checks subscription via database
has_subscription = await check_subscription(user['id'])
```

Telegram users can:
1. Use bot without web account
2. Optionally link web account via email
3. Access premium features if subscribed

## Multi-Platform Considerations

### Same User Across Platforms

If a user signs up on web and wants to use Telegram:
1. Note their Telegram username/ID
2. Add to `users.telegram_id` manually or via API
3. User can now use both platforms with same subscription

### Separate Accounts

By default, web and Telegram are separate:
- Supabase auth is web-only
- Telegram uses simple ID tracking
- Subscriptions are shared via `user_id`

To link accounts:
1. Get email from web signup
2. Add to Telegram user record via backend
3. User can now switch between platforms

## Troubleshooting

### "User Already Registered"

User tried to sign up with existing email:
- Let them sign in instead
- Show link to sign in page
- Offer password reset if needed

### "Invalid Login Credentials"

User typed wrong email or password:
- Check email spelling
- Try password reset
- Verify account exists

### "Session Expired"

User session timed out:
- User must sign in again
- App should handle gracefully
- Offer quick re-authentication

### User Not in public.users

If user can sign in but data is missing:
- Trigger may have failed
- Run manual sync as service role:
```sql
INSERT INTO public.users (id, email, created_at, updated_at)
SELECT id, email, created_at, updated_at
FROM auth.users
WHERE id NOT IN (SELECT id FROM public.users);
```

## Environment Variables

Required for auth to work:

```env
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
```

These are public (safe to expose to frontend).

The `SUPABASE_SERVICE_KEY` must be kept secret (backend only).

## Further Reading

- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)
- [JWT Authentication](https://jwt.io/)
- [Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Session Management](https://supabase.com/docs/guides/auth/sessions)
