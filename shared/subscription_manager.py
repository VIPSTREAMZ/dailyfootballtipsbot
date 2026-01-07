from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from supabase import Client


class SubscriptionManager:
    """Manage user subscriptions"""

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    async def check_active_subscription(self, user_id: str) -> bool:
        """Check if user has an active subscription"""
        try:
            result = self.supabase.table("subscriptions").select("*").eq(
                "user_id", user_id
            ).eq("status", "active").gte(
                "valid_until", datetime.utcnow().isoformat()
            ).maybeSingle().execute()

            return result.data is not None
        except Exception as e:
            print(f"Error checking subscription: {e}")
            return False

    async def get_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's active subscription"""
        try:
            result = self.supabase.table("subscriptions").select("*").eq(
                "user_id", user_id
            ).eq("status", "active").maybeSingle().execute()

            return result.data
        except Exception:
            return None

    async def create_subscription(
        self,
        user_id: str,
        plan_type: str = "monthly",
        stripe_subscription_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new subscription for user"""
        try:
            duration = 365 if plan_type == "yearly" else 30
            valid_until = datetime.utcnow() + timedelta(days=duration)

            sub_data = {
                "user_id": user_id,
                "plan_type": plan_type,
                "status": "active",
                "stripe_subscription_id": stripe_subscription_id,
                "valid_from": datetime.utcnow().isoformat(),
                "valid_until": valid_until.isoformat(),
            }

            result = self.supabase.table("subscriptions").insert(sub_data).execute()

            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error creating subscription: {e}")
            return None

    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel a subscription"""
        try:
            result = self.supabase.table("subscriptions").update({
                "status": "cancelled"
            }).eq("id", subscription_id).execute()

            return bool(result.data)
        except Exception as e:
            print(f"Error cancelling subscription: {e}")
            return False

    async def extend_subscription(
        self, subscription_id: str, days: int
    ) -> Optional[Dict[str, Any]]:
        """Extend an existing subscription"""
        try:
            result = self.supabase.table("subscriptions").select("*").eq(
                "id", subscription_id
            ).maybeSingle().execute()

            if not result.data:
                return None

            current_valid_until = datetime.fromisoformat(
                result.data["valid_until"].replace("Z", "+00:00")
            )
            new_valid_until = current_valid_until + timedelta(days=days)

            update_result = self.supabase.table("subscriptions").update({
                "valid_until": new_valid_until.isoformat()
            }).eq("id", subscription_id).execute()

            return update_result.data[0] if update_result.data else None
        except Exception as e:
            print(f"Error extending subscription: {e}")
            return None

    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for a user"""
        try:
            result = self.supabase.rpc("get_user_stats", {"p_user_id": user_id}).execute()

            if result.data:
                return result.data[0]
            return {
                "total_tips": 0,
                "won_tips": 0,
                "lost_tips": 0,
                "pending_tips": 0,
                "total_profit": 0,
                "win_rate": 0,
            }
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return {
                "total_tips": 0,
                "won_tips": 0,
                "lost_tips": 0,
                "pending_tips": 0,
                "total_profit": 0,
                "win_rate": 0,
            }
