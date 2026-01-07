import os
import asyncio
import aiohttp
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import redis
from supabase import create_client, Client
from datetime import datetime, timedelta

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
PRED_API = os.getenv("PRED_API", "http://localhost:8000")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

r = redis.from_url(REDIS_URL)
supabase: Client = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_KEY", "")
)

SUB_KEY_FMT = "subs:match:{}"
RATE_KEY_FMT = "rl:{}"


def rate_limit(max_per_min=12):
    """Rate limiting decorator"""
    def decorator(fn):
        async def wrapper(message: types.Message):
            uid = message.from_user.id
            k = RATE_KEY_FMT.format(uid)
            cnt = r.incr(k)
            if cnt == 1:
                r.expire(k, 60)
            if int(cnt) > max_per_min:
                await message.reply("Rate limit exceeded. Try again later.")
                return
            await fn(message)
        return wrapper
    return decorator


async def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None):
    """Get or create user in database"""
    try:
        result = supabase.table("users").select("*").eq("telegram_id", str(telegram_id)).maybeSingle().execute()

        if result.data:
            return result.data

        user_data = {
            "telegram_id": str(telegram_id),
            "username": username,
            "first_name": first_name,
        }

        result = supabase.table("users").insert(user_data).execute()
        return result.data[0]
    except Exception as e:
        print(f"Error getting/creating user: {e}")
        return None


async def check_subscription(user_id: str):
    """Check if user has active subscription"""
    try:
        result = supabase.table("subscriptions").select("*").eq("user_id", user_id).eq("status", "active").gte("valid_until", datetime.utcnow().isoformat()).maybeSingle().execute()
        return result.data is not None
    except Exception:
        return False


def subscription_required(fn):
    """Decorator to check subscription"""
    async def wrapper(message: types.Message):
        user = await get_or_create_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name
        )

        if not user:
            await message.reply("Error accessing user data. Please try again.")
            return

        has_sub = await check_subscription(user["id"])

        if not has_sub:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("Subscribe Now 💳", url=f"{FRONTEND_URL}/subscribe"))
            await message.reply(
                "This feature requires an active subscription.\n\n"
                "Get premium tips and insights!",
                reply_markup=keyboard
            )
            return

        await fn(message)
    return wrapper


@dp.message_handler(commands=['start', 'help'])
async def cmd_start(message: types.Message):
    """Start command"""
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Subscribe 💳", url=f"{FRONTEND_URL}/subscribe"))
    keyboard.add(InlineKeyboardButton("View Stats 📊", url=f"{FRONTEND_URL}/stats"))

    await message.reply(
        "⚽️ Welcome to Daily Football Tips Bot!\n\n"
        "Commands:\n"
        "/markets - Today's best value bets\n"
        "/match <id> - Live match analysis\n"
        "/subscribe <match_id> - Get live updates\n"
        "/unsubscribe <match_id> - Stop updates\n"
        "/mystats - Your subscription info\n\n"
        "Premium features require subscription.",
        reply_markup=keyboard
    )


@dp.message_handler(commands=['markets'])
@rate_limit()
@subscription_required
async def cmd_markets(message: types.Message):
    """Get best value markets"""
    async with aiohttp.ClientSession() as s:
        async with s.get(f"{PRED_API}/pre-match") as resp:
            if resp.status != 200:
                await message.reply("No market data available.")
                return
            data = await resp.json()

    text = "⚽️ *Best Value Bets Today*\n\n"

    for i, m in enumerate(data.get("results", [])[:8], 1):
        bm = m["best_market"]
        edge_pct = bm["edge"] * 100

        if edge_pct > 0:
            text += f"{i}. *{m['match']}*\n"
            text += f"   Bet: {bm['side']} @ {bm['book_odds']:.2f}\n"
            text += f"   Model: {bm['model_prob']*100:.1f}%\n"
            text += f"   Edge: +{edge_pct:.1f}%\n"
            text += f"   ID: `{m['match_id']}`\n\n"

    if not text.endswith("\n\n"):
        text = "No strong value bets found right now. Check back later!"

    await message.reply(text, parse_mode="Markdown")


@dp.message_handler(commands=['match'])
@rate_limit()
@subscription_required
async def cmd_match(message: types.Message):
    """Get match analysis"""
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Usage: /match <match_id>")
        return

    mid = parts[1]

    async with aiohttp.ClientSession() as s:
        async with s.get(f"{PRED_API}/match/{mid}") as resp:
            if resp.status != 200:
                await message.reply("Match not found or no live data available.")
                return
            data = await resp.json()

    text = f"⚽️ *{data.get('home_team', 'Home')} vs {data.get('away_team', 'Away')}*\n\n"
    text += f"Score: {data['score']['home']}-{data['score']['away']}\n"
    text += f"Minute: {data.get('minute', 0)}'\n\n"
    text += f"*Win Probabilities:*\n"
    text += f"Home: {data['home_prob']*100:.1f}%\n"
    text += f"Draw: {data['draw_prob']*100:.1f}%\n"
    text += f"Away: {data['away_prob']*100:.1f}%\n"

    await message.reply(text, parse_mode="Markdown")


@dp.message_handler(commands=['subscribe'])
@rate_limit()
@subscription_required
async def cmd_subscribe(message: types.Message):
    """Subscribe to match updates"""
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Usage: /subscribe <match_id>")
        return

    mid = parts[1]
    k = SUB_KEY_FMT.format(mid)
    r.sadd(k, message.chat.id)
    r.expire(k, 86400)

    await message.reply(f"✅ Subscribed to match {mid} updates.")


@dp.message_handler(commands=['unsubscribe'])
@rate_limit()
async def cmd_unsubscribe(message: types.Message):
    """Unsubscribe from match updates"""
    parts = message.text.split()
    if len(parts) < 2:
        await message.reply("Usage: /unsubscribe <match_id>")
        return

    mid = parts[1]
    k = SUB_KEY_FMT.format(mid)
    r.srem(k, message.chat.id)

    await message.reply(f"✅ Unsubscribed from match {mid}.")


@dp.message_handler(commands=['mystats'])
@rate_limit()
async def cmd_mystats(message: types.Message):
    """Get user subscription info"""
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )

    if not user:
        await message.reply("Error accessing user data.")
        return

    try:
        result = supabase.table("subscriptions").select("*").eq("user_id", user["id"]).eq("status", "active").maybeSingle().execute()

        if result.data:
            valid_until = datetime.fromisoformat(result.data["valid_until"].replace("Z", "+00:00"))
            days_left = (valid_until - datetime.utcnow()).days

            text = f"📊 *Your Subscription*\n\n"
            text += f"Status: ✅ Active\n"
            text += f"Plan: {result.data.get('plan_type', 'Premium')}\n"
            text += f"Valid until: {valid_until.strftime('%Y-%m-%d')}\n"
            text += f"Days remaining: {days_left}\n"
        else:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("Subscribe Now 💳", url=f"{FRONTEND_URL}/subscribe"))

            text = "📊 *Your Subscription*\n\nStatus: ❌ No active subscription"
            await message.reply(text, parse_mode="Markdown", reply_markup=keyboard)
            return

        await message.reply(text, parse_mode="Markdown")

    except Exception as e:
        print(f"Error fetching subscription: {e}")
        await message.reply("Error fetching subscription info.")


async def notifier():
    """Background task to send match updates"""
    await bot.delete_webhook(drop_pending_updates=True)

    last_scores = {}

    while True:
        try:
            keys = [k.decode().split(":")[-1] for k in r.keys("subs:match:*")]

            if not keys:
                await asyncio.sleep(10)
                continue

            async with aiohttp.ClientSession() as s:
                for mid in keys:
                    try:
                        async with s.get(f"{PRED_API}/match/{mid}") as resp:
                            if resp.status != 200:
                                continue
                            data = await resp.json()

                        score_str = f"{data['score']['home']}-{data['score']['away']}"

                        if last_scores.get(mid) != score_str:
                            last_scores[mid] = score_str

                            subs = [int(x) for x in r.smembers(SUB_KEY_FMT.format(mid))]

                            msg = f"⚽️ *Match Update*\n\n"
                            msg += f"{data.get('home_team', 'Home')} {data['score']['home']} - {data['score']['away']} {data.get('away_team', 'Away')}\n"
                            msg += f"Minute: {data.get('minute', 0)}'\n\n"
                            msg += f"Win Probabilities:\n"
                            msg += f"Home: {data['home_prob']*100:.1f}%\n"
                            msg += f"Draw: {data['draw_prob']*100:.1f}%\n"
                            msg += f"Away: {data['away_prob']*100:.1f}%"

                            for cid in subs:
                                try:
                                    await bot.send_message(cid, msg, parse_mode="Markdown")
                                except Exception as e:
                                    print(f"Error sending to {cid}: {e}")

                    except Exception as e:
                        print(f"Error processing match {mid}: {e}")

            await asyncio.sleep(15)

        except Exception as e:
            print(f"Error in notifier: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(notifier())
    executor.start_polling(dp, skip_updates=True)
