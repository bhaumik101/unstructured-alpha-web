"""Tests for utils.symbols — directory parsing + safe degradation (no network)."""
from utils import symbols as sym

_NASDAQ_FIXTURE = """Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares
AAPL|Apple Inc. - Common Stock|Q|N|N|100|N|N
NVDA|NVIDIA Corporation - Common Stock|Q|N|N|100|N|N
ZTEST|Nasdaq Test Issue|Q|Y|N|100|N|N
BAD$SYM|Weird Symbol|Q|N|N|100|N|N
File Creation Time: 0717202616:00|||||
"""

_OTHER_FIXTURE = """ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol
BRK.B|Berkshire Hathaway Inc. Class B|N|BRK.B|N|100|N|BRK.B
TSTX|Some Test|N|TSTX|N|100|Y|TSTX
File Creation Time: 0717202616:00|||||
"""


def test_parse_nasdaq_skips_header_test_and_junk():
    out = sym._parse(_NASDAQ_FIXTURE, sym_idx=0, name_idx=1, test_idx=3)
    assert "AAPL" in out and "NVDA" in out
    assert "ZTEST" not in out          # Test Issue == Y
    assert "BAD$SYM" not in out        # non-alphanumeric symbol
    assert not any(k.startswith("File Creation") for k in out)


def test_parse_other_uses_its_own_test_column():
    out = sym._parse(_OTHER_FIXTURE, sym_idx=0, name_idx=1, test_idx=6)
    assert "BRK.B" in out              # dots are valid share-class symbols
    assert "TSTX" not in out


def test_clean_name_trims_boilerplate_and_length():
    assert sym._clean_name("Apple Inc. - Common Stock") == "Apple Inc"
    assert sym._clean_name("NVIDIA Corporation - Common Stock") == "NVIDIA Corporation"
    assert len(sym._clean_name("X" * 200)) <= sym._NAME_MAXLEN


def test_parse_handles_empty_and_malformed():
    assert sym._parse("", 0, 1, 3) == {}
    assert sym._parse("header\n|||\n", 0, 1, 3) == {}


def test_build_index_falls_back_when_fetch_fails(monkeypatch):
    monkeypatch.setattr(sym, "fetch_symbol_directory", lambda: {})
    idx = sym.build_symbol_index()
    assert idx, "must fall back to tracked tickers rather than return empty"
    # every value is a display label
    assert all(isinstance(v, str) and v for v in idx.values())


def test_build_index_respects_cap(monkeypatch):
    monkeypatch.setattr(sym, "fetch_symbol_directory",
                        lambda: {f"SYM{i}": f"Company {i}" for i in range(50000)})
    monkeypatch.setattr(sym, "MAX_SEARCH_SYMBOLS", 1000)
    idx = sym.build_symbol_index()
    assert len(idx) <= 1000


def test_build_index_keeps_tracked_tickers_even_when_capped(monkeypatch):
    from utils.config import TICKERS
    monkeypatch.setattr(sym, "fetch_symbol_directory",
                        lambda: {f"ZZZ{i}": f"Co {i}" for i in range(5000)})
    monkeypatch.setattr(sym, "MAX_SEARCH_SYMBOLS", 300)
    idx = sym.build_symbol_index()
    some_tracked = list(TICKERS.keys())[:5]
    for t in some_tracked:
        assert t in idx, "tracked tickers must survive the cap"


def test_is_tracked():
    from utils.config import TICKERS
    a_tracked = next(iter(TICKERS))
    assert sym.is_tracked(a_tracked)
    assert sym.is_tracked(a_tracked.lower())     # case-insensitive
    assert not sym.is_tracked("ZZZZNOTREAL")
    assert not sym.is_tracked("")
