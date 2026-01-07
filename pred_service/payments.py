from fastapi import APIRouter, HTTPException, Request, Header
from typing import Optional
import os
import stripe
from datetime import datetime, timedelta
from shared.supabase_client import get_service_client

router = APIRouter(prefix="/payments", tags=["payments"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

PLANS = {
    "monthly": {"price": 29.99, "duration_days": 30},
    "yearly": {"price": 299.99, "duration_days": 365},
}


@router.post("/create-checkout-session")
async def create_checkout_session(
    plan_type: str,
    user_id: str,
    success_url: str,
    cancel_url: str
):
    """Create Stripe checkout session for subscription"""
    if plan_type not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan type")

    try:
        supabase = get_service_client()

        user_result = supabase.table("users").select("*").eq("id", user_id).maybeSingle().execute()

        if not user_result.data:
            raise HTTPException(status_code=404, detail="User not found")

        user = user_result.data
        stripe_customer_id = user.get("stripe_customer_id")

        if not stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.get("email"),
                metadata={"user_id": user_id}
            )
            stripe_customer_id = customer.id

            supabase.table("users").update({
                "stripe_customer_id": stripe_customer_id
            }).eq("id", user_id).execute()

        plan = PLANS[plan_type]

        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Football Tips {plan_type.capitalize()} Subscription",
                        "description": "Premium football betting tips and analysis",
                    },
                    "unit_amount": int(plan["price"] * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": user_id,
                "plan_type": plan_type,
            }
        )

        return {"checkout_url": session.url, "session_id": session.id}

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: Optional[str] = Header(None)):
    """Handle Stripe webhook events"""
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    supabase = get_service_client()

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"].get("user_id")
        plan_type = session["metadata"].get("plan_type")

        if user_id and plan_type:
            plan = PLANS.get(plan_type)

            if plan:
                valid_until = datetime.utcnow() + timedelta(days=plan["duration_days"])

                supabase.table("subscriptions").insert({
                    "user_id": user_id,
                    "plan_type": plan_type,
                    "status": "active",
                    "stripe_subscription_id": session.get("subscription"),
                    "valid_from": datetime.utcnow().isoformat(),
                    "valid_until": valid_until.isoformat(),
                }).execute()

                supabase.table("payment_transactions").insert({
                    "user_id": user_id,
                    "stripe_payment_intent_id": session.get("payment_intent"),
                    "amount": session["amount_total"] / 100,
                    "currency": session["currency"].upper(),
                    "status": "succeeded",
                    "payment_method": "stripe",
                }).execute()

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        stripe_sub_id = subscription["id"]

        supabase.table("subscriptions").update({
            "status": "cancelled"
        }).eq("stripe_subscription_id", stripe_sub_id).execute()

    return {"status": "success"}


@router.get("/plans")
async def get_plans():
    """Get available subscription plans"""
    return {
        "plans": [
            {
                "id": "monthly",
                "name": "Monthly Subscription",
                "price": PLANS["monthly"]["price"],
                "duration": "30 days",
                "features": [
                    "Daily pre-match predictions",
                    "Live match analysis",
                    "Real-time notifications",
                    "Historical statistics",
                ]
            },
            {
                "id": "yearly",
                "name": "Yearly Subscription",
                "price": PLANS["yearly"]["price"],
                "duration": "365 days",
                "discount": "Save 17%",
                "features": [
                    "All monthly features",
                    "Priority support",
                    "Advanced analytics",
                    "API access",
                ]
            }
        ]
    }
