# -*- coding: utf-8 -*-
"""財務データの取得層。

正データは data/financials.json（tools/fetch_financials.py が生成する実データのスナップショット）。
同梱スナップショットを既定とし、ライブ取得は画面から明示的に呼ばれたときだけ yfinance を叩く。

方針:
  - 数字を乱数で作らない。取得できなかった項目は None のまま返し、画面側で「-」を出す。
  - 取得元と取得日時は snapshot_meta() で必ず開示する。
"""
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT_PATH = os.path.join(BASE_DIR, "data", "financials.json")


class DataSourceManager:
    """同梱スナップショット＋任意コードのライブ取得を束ねる。"""

    def __init__(self, snapshot_path: Optional[str] = None):
        self.snapshot_path = snapshot_path or SNAPSHOT_PATH
        self.snapshot = self._load_snapshot()
        self.company_master: Dict[str, Dict[str, Any]] = self.snapshot.get("companies", {})
        # ライブ取得の結果はセッション中だけ保持する（ファイルには書かない）
        self._live_cache: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------ 読み込み

    def _load_snapshot(self) -> Dict[str, Any]:
        try:
            with open(self.snapshot_path, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return {"companies": {}, "financials": {}}

    def snapshot_meta(self) -> Dict[str, Any]:
        """データの出どころ。画面に必ず出す。"""
        return {
            "generated_at": self.snapshot.get("generated_at"),
            "source": self.snapshot.get("source"),
            "unit": self.snapshot.get("unit", "百万円"),
            "disclaimer": self.snapshot.get("disclaimer"),
            "count": len(self.company_master),
        }

    def list_companies(self) -> List[Dict[str, Any]]:
        """同梱している企業の一覧（画面のボタン生成用）。"""
        companies = [
            {
                "code": code,
                "name": c.get("name") or c.get("name_en") or code,
                "sector": c.get("sector") or "—",
            }
            for code, c in self.company_master.items()
        ]
        return sorted(companies, key=lambda x: x["code"])

    # ------------------------------------------------------------------ 企業情報

    def get_company_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        code = (code or "").strip()
        company = self.company_master.get(code)
        if company is None:
            company = self._live_cache.get(code, {}).get("company")
        if company is None:
            return None

        data = dict(company)
        data["code"] = code
        data.setdefault("segments", [])  # セグメント別売上は取得元に無いので持たない

        financial = self.get_financial_data(code)
        if financial:
            data["recent_performance"] = self._recent_performance(financial)
            data["data_notes"] = financial.get("notes", [])
        return data

    def get_company_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        keyword = (name or "").strip()
        if not keyword:
            return None
        lowered = keyword.lower()
        for code, company in self.company_master.items():
            ja = company.get("name") or ""
            en = (company.get("name_en") or "").lower()
            if keyword in ja or (lowered and lowered in en):
                return self.get_company_by_code(code)
        return None

    # ------------------------------------------------------------------ 財務データ

    def get_financial_data(self, code: str, periods: int = 5) -> Optional[Dict[str, Any]]:
        code = (code or "").strip()
        financial = self.snapshot.get("financials", {}).get(code)
        if financial is None:
            financial = self._live_cache.get(code, {}).get("financials")
        if financial is None:
            return None
        return self._trim(financial, periods)

    @staticmethod
    def _trim(financial: Dict[str, Any], periods: int) -> Dict[str, Any]:
        """直近 periods 期に絞る（期数がそれ以下ならそのまま）。"""
        years = financial.get("years") or []
        if not periods or len(years) <= periods:
            return financial

        trimmed = dict(financial)
        for key in ("years", "fiscal_period_end", "income_statement",
                    "balance_sheet", "cash_flow", "ratios"):
            value = financial.get(key)
            if isinstance(value, list):
                trimmed[key] = value[-periods:]
        trimmed["periods"] = len(trimmed.get("years", []))
        return trimmed

    @staticmethod
    def _recent_performance(financial: Dict[str, Any]) -> Dict[str, Any]:
        """直近期の実績と前期比。計算できないものは None を返す（0 で埋めない）。"""
        income = financial.get("income_statement") or []
        ratios = financial.get("ratios") or []
        if not income:
            return {}

        current = income[-1]
        previous = income[-2] if len(income) >= 2 else None

        def growth(key):
            if previous is None:
                return None
            now, before = current.get(key), previous.get(key)
            if now is None or not before:
                return None
            return round((now / before - 1) * 100, 1)

        latest_ratio = ratios[-1] if ratios else {}
        roe = latest_ratio.get("roe")

        return {
            "period": current.get("year"),
            "revenue": current.get("revenue"),
            "revenue_growth": growth("revenue"),
            "operating_profit_growth": growth("operating_profit"),
            # 画面側の呼び名に合わせる（純利益の前期比）
            "profit_growth": growth("net_profit"),
            "net_profit_growth": growth("net_profit"),
            # ROE はパーセント値、負債比率は小数のまま（画面側で 100 倍する）
            "roe": round(roe * 100, 1) if roe is not None else None,
            "debt_ratio": latest_ratio.get("debt_ratio"),
            "equity_ratio": latest_ratio.get("equity_ratio"),
        }

    # ------------------------------------------------------------------ ライブ取得

    def fetch_live(self, code: str) -> Tuple[bool, str]:
        """任意の証券コードを yfinance から取りに行く。

        同梱スナップショットに無い企業を見るための経路。
        失敗しても同梱データの表示は壊さない（False とメッセージを返すだけ）。
        """
        code = (code or "").strip()
        if not code.isdigit():
            return False, "証券コードは数字で入力してください（例: 6758）"

        tools_dir = os.path.join(BASE_DIR, "tools")
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        try:
            from fetch_financials import build
        except ImportError as e:
            return False, "ライブ取得を利用できません（%s）。同梱データのみ表示します" % e

        try:
            profile, financial = build(code)
        except Exception as e:
            return False, "取得に失敗しました（%s）。同梱データのみ表示します" % type(e).__name__

        income = financial.get("income_statement") or []
        if not income or income[-1].get("revenue") is None:
            return False, "証券コード %s の財務データが見つかりませんでした" % code

        self._live_cache[code] = {"company": profile, "financials": financial}
        return True, "%s の実データを取得しました（出典: Yahoo! Finance）" % code
