import asyncio
import ccxt.pro as pro
import sys
import time
import logging
from collections import defaultdict, deque

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Настройка логирования
logging.basicConfig(
    filename="order_book_analysis.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Константы
HISTORY_SIZE = 500
LEVEL_THRESHOLD = 10
FAKE_THRESHOLD = 3
BIG_ORDER_THRESHOLD = 5

# История стакана и отслеживание уровней
order_book_history = deque(maxlen=HISTORY_SIZE)
support_levels = defaultdict(lambda: {"count": 0, "volume": 0, "last_seen": 0, "is_fake": False})
resistance_levels = defaultdict(lambda: {"count": 0, "volume": 0, "last_seen": 0, "is_fake": False})
fake_orders = set()

def log_event(message):
    """Логирует события в файл и выводит в консоль."""
    logging.info(message)
    print(message)

def track_levels(levels_dict, levels, timestamp):
    """Отслеживает уровни поддержки/сопротивления и выявляет фейковые заявки."""
    for price, volume in levels:
        if price in levels_dict:
            levels_dict[price]["count"] += 1
            levels_dict[price]["volume"] = volume
            levels_dict[price]["last_seen"] = timestamp
        else:
            levels_dict[price] = {"count": 1, "volume": volume, "last_seen": timestamp, "is_fake": False}

    # Отмечаем фейковые заявки
    for price in list(levels_dict.keys()):
        if levels_dict[price]["count"] < FAKE_THRESHOLD:
            levels_dict[price]["is_fake"] = True
            fake_orders.add((price, levels_dict[price]["volume"]))

def format_levels(levels_dict, is_resistance=False):
    """Форматирует уровни для вывода, показывая даже фейки если нет других."""
    sorted_levels = sorted(
        [(p, d) for p, d in levels_dict.items()],
        key=lambda x: x[0],
        reverse=is_resistance
    )[:10]

    if not sorted_levels:
        return ["Нет данных"]

    has_real_levels = any(not d["is_fake"] for _, d in sorted_levels)

    formatted_levels = []
    for price, data in sorted_levels:
        volume = data["volume"]
        tag = "🔴" if not is_resistance else "🟢"
        if data["is_fake"]:
            tag = "⚠️ (фейк)"
        formatted_levels.append(f"│ {price:.3f} │ {volume:.2f} {tag} │")

    return formatted_levels if has_real_levels else ["Нет данных"]

def analyze_order_book(order_book, timestamp):
    """Анализирует стакан и определяет ключевые уровни, крупные заявки и фейки."""
    bids = order_book["bids"]
    asks = order_book["asks"]

    total_bids = sum([bid[1] for bid in bids])
    total_asks = sum([ask[1] for ask in asks])

    imbalance = (total_bids - total_asks) / (total_bids + total_asks + 1e-8)
    market_sentiment = "🟢 Бычий" if imbalance > 0.1 else "🔴 Медвежий" if imbalance < -0.1 else "⚪ Нейтральный"
    avg_order_size = (total_bids + total_asks) / (len(bids) + len(asks))

    # Отслеживаем поддержку и сопротивление
    track_levels(support_levels, bids[:10], timestamp)
    track_levels(resistance_levels, asks[:10], timestamp)

    support_strength = sum([lvl["volume"] for lvl in support_levels.values() if not lvl["is_fake"]])
    resistance_strength = sum([lvl["volume"] for lvl in resistance_levels.values() if not lvl["is_fake"]])
    break_probability = (
        "🔼 Высокий шанс пробоя вверх" if support_strength > resistance_strength * 1.5 else
        "🔽 Высокий шанс пробоя вниз" if resistance_strength > support_strength * 1.5 else
        "⚖️ Баланс (ожидаем накопление)"
    )

    # Фильтруем крупные заявки, исключая фейки
    big_bids = [(p, v) for p, v in bids if v > BIG_ORDER_THRESHOLD * avg_order_size and (p, v) not in fake_orders]
    big_asks = [(p, v) for p, v in asks if v > BIG_ORDER_THRESHOLD * avg_order_size and (p, v) not in fake_orders]

    return {
        "best_bid": bids[0][0] if bids else None,
        "best_ask": asks[0][0] if asks else None,
        "total_bids": total_bids,
        "total_asks": total_asks,
        "imbalance": imbalance,
        "market_sentiment": market_sentiment,
        "avg_order_size": avg_order_size,
        "break_probability": break_probability,
        "support_levels": format_levels(support_levels, is_resistance=False),
        "resistance_levels": format_levels(resistance_levels, is_resistance=True),
        "big_bids": big_bids[:10],
        "big_asks": big_asks[:10],
        "fake_orders": sorted(fake_orders, key=lambda x: x[1], reverse=True)[:10]
    }

async def websocket_order_book_monitor(exchange, symbol):
    """Получает обновления ордербука и анализирует их в реальном времени."""
    while True:
        try:
            order_book = await exchange.watch_order_book(symbol)
            timestamp = time.time()
            analysis = analyze_order_book(order_book, timestamp)

            print("\033c", end="")

            print(f"\n📈 {symbol} | Best Bid: {analysis['best_bid']:.4f} | Best Ask: {analysis['best_ask']:.4f}")
            print(f"💰 Объем покупок: {analysis['total_bids']:.2f} | 📉 Объем продаж: {analysis['total_asks']:.2f}")
            print(f"⚖️ Имбаланс: {analysis['imbalance']:.2f} | 📊 Настроение: {analysis['market_sentiment']}")
            print(f"🔮 {analysis['break_probability']}\n")

            print("📉 Уровни поддержки:")
            for level in analysis["support_levels"]:
                print(level)

            print("\n📈 Уровни сопротивления:")
            for level in analysis["resistance_levels"]:
                print(level)

            print("\n🔥 **Крупные заявки покупателей (🔵):**")
            for price, volume in analysis["big_bids"]:
                print(f"   {price:.3f} USDT | Объем: {volume:.2f} 🔵")

            print("\n🔥 **Крупные заявки продавцов (🔴):**")
            for price, volume in analysis["big_asks"]:
                print(f"   {price:.3f} USDT | Объем: {volume:.2f} 🔴")

            print("\n⚠️ **Топ 10 фейковых заявок:**")
            for price, volume in analysis["fake_orders"]:
                print(f"   {price:.3f} USDT | Объем: {volume:.2f} ⚠️")

            await asyncio.sleep(1)

        except Exception as e:
            log_event(f"WebSocket Error: {e}")

async def main():
    exchange = pro.binance({"rateLimit": 10, "enableRateLimit": True, "newUpdates": True})
    symbol = "DEXE/USDT"
    await websocket_order_book_monitor(exchange, symbol)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
