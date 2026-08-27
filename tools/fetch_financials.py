# -*- coding: utf-8 -*-
"""yfinance から実財務データを取得し、検証したうえで data/financials.json に固める。

方針:
  - 同梱データはすべてこのスクリプトの出力。出どころ不明の手入力値は持たない。
  - 取得した数字をそのまま信じない。検証して、引っかかったものは notes に残して画面に出す。
再取得: python tools/fetch_financials.py
"""
import json
import os
import sys
from datetime import datetime, timezone, timedelta

import yfinance as yf

JST = timezone(timedelta(hours=9))

# デモ対象（東証プライム・業種を散らす）
TARGETS = {
    "9432": {"name": "日本電信電話", "sector": "情報・通信業", "market": "東証プライム"},
    "9843": {"name": "ニトリホールディングス", "sector": "小売業", "market": "東証プライム"},
    "4661": {"name": "オリエンタルランド", "sector": "サービス業", "market": "東証プライム"},
    "2802": {"name": "味の素", "sector": "食料品", "market": "東証プライム"},
    "6758": {"name": "ソニーグループ", "sector": "電気機器", "market": "東証プライム"},
}

MILLION = 1000000
# 最終利益と継続事業利益がこの割合以上ずれたら継続事業ベースを採用する
DISCONTINUED_THRESHOLD = 0.05
# 総資産がこの割合以上動いたら構造変化として注記する
BALANCE_SHEET_THRESHOLD = 0.30


def pick(df, *names):
    """複数の候補行名から最初に見つかったものを返す（無ければ None）。"""
    if df is None or df.empty:
        return None
    for n in names:
        if n in df.index:
            return df.loc[n]
    return None


def val(series, col):
    """百万円単位の int に丸める。欠損は None。"""
    if series is None or col not in series.index:
        return None
    v = series[col]
    if v is None:
        return None
    try:
        if v != v:  # NaN
            return None
    except Exception:
        return None
    return int(round(float(v) / MILLION))


def ratio(a, b):
    if a is None or b in (None, 0):
        return None
    return round(a / b, 4)


def check_periods(period_ends):
    """決算期の連続性を調べ、飛び（12ヶ月から外れる間隔）を返す。"""
    gaps = []
    for prev, cur in zip(period_ends, period_ends[1:]):
        months = (cur.year - prev.year) * 12 + (cur.month - prev.month)
        if months > 13:
            gaps.append("%s → %s（%dヶ月・この間の決算期がデータに存在しない）"
                        % (prev.strftime("%Y-%m"), cur.strftime("%Y-%m"), months))
        elif months < 11:
            gaps.append("%s → %s（%dヶ月・変則決算の可能性）"
                        % (prev.strftime("%Y-%m"), cur.strftime("%Y-%m"), months))
    return gaps


def build(code):
    t = yf.Ticker(code + ".T")
    inc, bs, cf = t.income_stmt, t.balance_sheet, t.cashflow
    notes = []

    revenue_s = pick(inc, "Total Revenue", "Operating Revenue")
    # 営業利益は "As Reported"（各社の開示値）を優先する。
    # "Operating Income" は yfinance 側の正規化値で、開示値と数%ずれる
    # （例: NTT 2026年3月期 開示 1,706,221 に対し正規化値 1,786,410）。
    op_s = pick(inc, "Total Operating Income As Reported", "Operating Income")
    reported_s = pick(inc, "Net Income", "Net Income Common Stockholders")
    continuing_s = pick(inc, "Net Income From Continuing Operation Net Minority Interest",
                        "Net Income Continuous Operations")
    gross_s = pick(inc, "Gross Profit")

    ta_s = pick(bs, "Total Assets")
    eq_s = pick(bs, "Stockholders Equity", "Common Stock Equity")
    debt_s = pick(bs, "Total Debt")
    ca_s = pick(bs, "Current Assets")
    cl_s = pick(bs, "Current Liabilities")
    ltd_s = pick(bs, "Long Term Debt")

    ocf_s = pick(cf, "Operating Cash Flow")
    icf_s = pick(cf, "Investing Cash Flow")
    fcf_s = pick(cf, "Financing Cash Flow")
    free_s = pick(cf, "Free Cash Flow")

    # 決算期は新しい順で返るので古い順に並べ替える
    cols = sorted(list(inc.columns), key=lambda c: c)

    for g in check_periods(cols):
        notes.append("決算期に飛びがある: " + g)

    data = {
        "company_code": code,
        "periods": len(cols),
        "years": [c.year for c in cols],
        "fiscal_period_end": [c.strftime("%Y-%m-%d") for c in cols],
        "unit": "百万円",
        "net_profit_basis": "reported",
        "income_statement": [],
        "balance_sheet": [],
        "cash_flow": [],
        "ratios": [],
    }

    # 純利益の基準を決める（非継続事業の影響が大きい期があれば継続事業ベースへ）
    use_continuing = False
    for c in cols:
        rep, con = val(reported_s, c), val(continuing_s, c)
        if rep is None or con is None or rep == 0:
            continue
        if abs(rep - con) / max(abs(rep), 1) > DISCONTINUED_THRESHOLD:
            use_continuing = True
            notes.append(
                "%d年%d月期は最終利益（%s百万円）と継続事業利益（%s百万円）が乖離している。"
                "非継続事業の影響を除くため、本ツールでは継続事業ベースを純利益として扱う"
                % (c.year, c.month, format(rep, ","), format(con, ",")))
    if use_continuing:
        data["net_profit_basis"] = "continuing_operations"

    net_s = continuing_s if use_continuing else reported_s

    for c in cols:
        rev, op, net, gross = val(revenue_s, c), val(op_s, c), val(net_s, c), val(gross_s, c)
        data["income_statement"].append({
            "year": c.year,
            "revenue": rev,
            "operating_profit": op,
            "net_profit": net,
            "net_profit_reported": val(reported_s, c),
            "gross_margin": ratio(gross, rev),
            "operating_margin": ratio(op, rev),
            "net_margin": ratio(net, rev),
        })

    for c in cols:
        ta, eq, debt = val(ta_s, c), val(eq_s, c), val(debt_s, c)
        ca, cl, ltd = val(ca_s, c), val(cl_s, c), val(ltd_s, c)
        data["balance_sheet"].append({
            "year": c.year,
            "total_assets": ta,
            "total_equity": eq,
            "total_debt": debt,
            "current_assets": ca,
            "fixed_assets": (ta - ca) if (ta is not None and ca is not None) else None,
            "current_liabilities": cl,
            "long_term_debt": ltd,
        })

    estimated_fcf_years = []
    for c in cols:
        ocf, icf = val(ocf_s, c), val(icf_s, c)
        free = val(free_s, c)
        # フリーキャッシュフローが取れない期は 営業CF＋投資CF で代用する。
        # 投資CF には買収・売却なども含まれるので、厳密な FCF とはずれる。
        # 代用したことは記録して画面にも出す。
        is_estimate = free is None and ocf is not None and icf is not None
        if is_estimate:
            free = ocf + icf
            estimated_fcf_years.append(c.year)
        data["cash_flow"].append({
            "year": c.year,
            "operating_cf": ocf,
            "investing_cf": icf,
            "financing_cf": val(fcf_s, c),
            "free_cf": free,
            "free_cf_is_estimate": is_estimate,
        })

    if estimated_fcf_years:
        notes.append(
            "フリーキャッシュフローを取得できなかった期（%s）は「営業CF＋投資CF」で代用している。"
            "投資CF には買収・売却なども含まれるため、厳密なフリーキャッシュフローとはずれる"
            % "／".join("%d年" % y for y in estimated_fcf_years))

    for i, c in enumerate(cols):
        inc_row, bs_row = data["income_statement"][i], data["balance_sheet"][i]
        data["ratios"].append({
            "year": c.year,
            "roe": ratio(inc_row["net_profit"], bs_row["total_equity"]),
            "roa": ratio(inc_row["net_profit"], bs_row["total_assets"]),
            "debt_ratio": ratio(bs_row["total_debt"], bs_row["total_assets"]),
            "current_ratio": ratio(bs_row["current_assets"], bs_row["current_liabilities"]),
            "equity_ratio": ratio(bs_row["total_equity"], bs_row["total_assets"]),
        })

    # 貸借対照表の急変を検知する（事業の分離・取得、会計基準の変更など）。
    # 損益側には非継続事業の検知があるが、BS 側にも同種の断絶が起きる。
    for i in range(1, len(data["balance_sheet"])):
        prev_assets = data["balance_sheet"][i - 1].get("total_assets")
        curr_assets = data["balance_sheet"][i].get("total_assets")
        if not prev_assets or not curr_assets:
            continue
        change = (curr_assets - prev_assets) / abs(prev_assets)
        if abs(change) > BALANCE_SHEET_THRESHOLD:
            notes.append(
                "%s期は総資産が前期比 %+.0f%%（%s → %s百万円）と大きく動いている。"
                "事業の分離・取得や会計基準の変更が含まれる可能性があり、"
                "自己資本比率や資産効率の推移をそのまま比較できない"
                % (data["fiscal_period_end"][i][:7], change * 100,
                   format(prev_assets, ","), format(curr_assets, ",")))

    # 売上が空の期は分析に使えないので落とす（落としたことは notes に残す）
    keep = [i for i, row in enumerate(data["income_statement"]) if row["revenue"] is not None]
    if len(keep) != len(data["income_statement"]):
        dropped = [data["fiscal_period_end"][i]
                   for i in range(len(data["income_statement"])) if i not in keep]
        notes.append("売上を取得できなかった期を分析対象から外した: " + "／".join(dropped))
        for key in ("years", "fiscal_period_end", "income_statement",
                    "balance_sheet", "cash_flow", "ratios"):
            data[key] = [data[key][i] for i in keep]
        data["periods"] = len(data["years"])

    # 欠損チェック
    missing = [k for k in ("revenue", "operating_profit", "net_profit")
               if data["income_statement"] and data["income_statement"][-1][k] is None]
    if missing:
        notes.append("最新期に取得できなかった項目がある: " + "／".join(missing))

    data["notes"] = notes

    # 企業プロフィール（yfinance から取れるものだけ）
    profile = dict(TARGETS.get(code, {}))
    profile["code"] = code
    try:
        info = t.info
    except Exception:
        info = {}
    # 同梱対象以外（画面からのライブ取得）は日本語名・業種を持たないので取得値で代用する
    profile.setdefault("name", info.get("longName") or code)
    profile.setdefault("sector", info.get("sector") or "—")
    profile.setdefault("market", "—")
    profile["name_en"] = info.get("longName")
    profile["employees"] = info.get("fullTimeEmployees")
    profile["website"] = info.get("website")
    profile["headquarters"] = info.get("city")
    profile["business_description"] = info.get("longBusinessSummary")
    mc = info.get("marketCap")
    profile["market_cap"] = int(mc / MILLION) if mc else None

    return profile, data


def main():
    out = {
        "generated_at": datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S JST"),
        "source": "Yahoo! Finance（yfinance 経由で取得）",
        "unit": "百万円",
        "disclaimer": "本ツールの数値は Yahoo! Finance の公開データを取得したものであり、"
                      "各社の有価証券報告書と完全に一致することを保証しない。投資判断には使用しないこと。",
        "companies": {},
        "financials": {},
    }
    for code in TARGETS:
        sys.stdout.write("fetching %s ... " % code)
        sys.stdout.flush()
        try:
            profile, fin = build(code)
            out["companies"][code] = profile
            out["financials"][code] = fin
            n = len([r for r in fin["income_statement"] if r["revenue"] is not None])
            print("OK (%d期) notes=%d" % (n, len(fin["notes"])))
            for note in fin["notes"]:
                print("    - " + note)
        except Exception as e:
            print("FAILED: %s: %s" % (type(e).__name__, e))

    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "data", "financials.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    print("wrote:", path)


if __name__ == "__main__":
    main()
