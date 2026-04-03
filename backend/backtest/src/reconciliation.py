from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


def simulate_juejin_bollinger_trades(
    frame: pd.DataFrame,
    symbol: str,
    *,
    ma_period: int = 26,
    std_period: int = 26,
    std_range: float = 1.0,
    size: int = 100,
    commission_rate: float = 0.0003,
    min_commission: float = 5.0,
) -> List[Dict[str, Any]]:
    """Reproduce the Juejin sample strategy on an adjusted daily close series."""
    if frame.empty:
        return []

    data = frame.sort_index().copy()
    close = data["close"].astype(float)
    mean = close.rolling(ma_period).mean()
    std = close.rolling(std_period).std(ddof=1)
    upper = mean + std_range * std
    lower = mean - std_range * std

    position = 0
    trades: List[Dict[str, Any]] = []

    for idx in range(1, len(data)):
        current_close = float(close.iloc[idx])
        previous_close = float(close.iloc[idx - 1])
        current_upper = upper.iloc[idx]
        previous_upper = upper.iloc[idx - 1]
        current_lower = lower.iloc[idx]
        previous_lower = lower.iloc[idx - 1]

        if pd.isna(current_upper) or pd.isna(previous_upper) or pd.isna(current_lower) or pd.isna(previous_lower):
            continue

        trade_time = data.index[idx].strftime("%Y-%m-%d 00:00:00")
        commission = max(min_commission, current_close * size * commission_rate)

        if position > 0 and current_close > float(current_upper) and previous_close <= float(previous_upper):
            trades.append(
                {
                    "time": trade_time,
                    "code": symbol,
                    "type": "SELL",
                    "price": current_close,
                    "quantity": size,
                    "amount": current_close * size,
                    "commission": commission,
                }
            )
            position = max(0, position - size)
        elif position == 0 and current_close < float(current_lower) and previous_close >= float(previous_lower):
            trades.append(
                {
                    "time": trade_time,
                    "code": symbol,
                    "type": "BUY",
                    "price": current_close,
                    "quantity": size,
                    "amount": current_close * size,
                    "commission": commission,
                }
            )
            position += size

    return trades


def compare_trade_sequences(
    expected: List[Dict[str, Any]],
    actual: List[Dict[str, Any]],
    *,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for idx in range(limit):
        expected_trade = expected[idx] if idx < len(expected) else None
        actual_trade = actual[idx] if idx < len(actual) else None
        expected_price = float(expected_trade["price"]) if expected_trade else None
        actual_price = float(actual_trade["price"]) if actual_trade else None
        price_diff = None
        if expected_price is not None and actual_price is not None:
            price_diff = actual_price - expected_price

        rows.append(
            {
                "index": idx + 1,
                "expected_time": expected_trade["time"] if expected_trade else None,
                "actual_time": actual_trade["time"] if actual_trade else None,
                "expected_type": expected_trade["type"] if expected_trade else None,
                "actual_type": actual_trade["type"] if actual_trade else None,
                "expected_price": expected_price,
                "actual_price": actual_price,
                "price_diff": price_diff,
                "expected_quantity": expected_trade["quantity"] if expected_trade else None,
                "actual_quantity": actual_trade["quantity"] if actual_trade else None,
                "matched": (
                    expected_trade is not None
                    and actual_trade is not None
                    and expected_trade["time"] == actual_trade["time"]
                    and expected_trade["type"] == actual_trade["type"]
                    and expected_trade["quantity"] == actual_trade["quantity"]
                ),
            }
        )

    return rows
