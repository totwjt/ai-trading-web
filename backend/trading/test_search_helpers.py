from trading.routers import get_stock_match_score, get_stock_name_initials


def test_get_stock_name_initials_returns_pinyin_initials():
    assert get_stock_name_initials("平安银行") == "payh"


def test_get_stock_match_score_supports_initials_prefix():
    assert get_stock_match_score("pay", "000001.SZ", "平安银行") == 3


def test_get_stock_match_score_prefers_code_prefix():
    assert get_stock_match_score("000", "000001.SZ", "平安银行") == 1
