import pandas as pd

from backtest.src.reconciliation import compare_trade_sequences, simulate_juejin_bollinger_trades


def test_simulate_juejin_bollinger_trades_generates_same_bar_close_signal():
    index = pd.date_range("2024-01-01", periods=6, freq="D")
    frame = pd.DataFrame(
        {
            "close": [10.0, 10.0, 10.0, 10.0, 10.0, 8.0],
        },
        index=index,
    )

    trades = simulate_juejin_bollinger_trades(
        frame,
        "600004.SH",
        ma_period=5,
        std_period=5,
        std_range=1.0,
        size=100,
    )

    assert len(trades) == 1
    assert trades[0]["time"] == "2024-01-06 00:00:00"
    assert trades[0]["type"] == "BUY"
    assert trades[0]["price"] == 8.0


def test_compare_trade_sequences_marks_exact_match():
    expected = [{"time": "2024-03-25 00:00:00", "type": "BUY", "price": 1.0, "quantity": 100}]
    actual = [{"time": "2024-03-25 00:00:00", "type": "BUY", "price": 1.0, "quantity": 100}]

    rows = compare_trade_sequences(expected, actual, limit=1)

    assert rows[0]["matched"] is True
