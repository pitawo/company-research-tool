import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from datetime import datetime
import statistics

class FinancialAnalyzer:
    """
    財務分析を行うクラス
    収益性・安全性・成長性・効率性の分析機能を提供
    """
    
    def __init__(self):
        # 業界平均との比較は行わない（出典を示せる業界平均値を持っていないため）
        pass
    
    @staticmethod
    def _div(numerator, denominator, default=0.0):
        """None や 0 を含む割り算を安全に行う。

        取得元にデータが無い項目があっても分析全体が落ちないようにするための防御。
        """
        if numerator is None or denominator in (None, 0):
            return default
        return numerator / denominator

    @staticmethod
    def _ratio_of(financial_data, key, default=0.0):
        """最新期の比率を読む。

        ROE・ROA・負債比率などは tools/fetch_financials.py が算出済み。
        同じ式をここにも書くと、片方だけ直したときに食い違うので読むだけにする。
        """
        ratios = financial_data.get('ratios') or []
        if not ratios:
            return default
        value = ratios[-1].get(key)
        return default if value is None else value

    @staticmethod
    def _growth(current, previous, default=0.0):
        """前期比の増減率。計算できないときは default を返す。"""
        if current is None or previous in (None, 0):
            return default
        return (current - previous) / abs(previous)

    def analyze_profitability(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """収益性分析"""
        income_statements = financial_data.get('income_statement', [])
        balance_sheets = financial_data.get('balance_sheet', [])
        
        if not income_statements or not balance_sheets:
            return {"error": "財務データが不足しています"}
        
        # 最新年度のデータ
        latest_income = income_statements[-1]
        latest_balance = balance_sheets[-1]
        
        # 収益性指標を計算
        gross_margin = latest_income.get('gross_margin', 0)
        operating_margin = latest_income.get('operating_margin', 0)
        net_margin = latest_income.get('net_margin', 0)
        
        # 比率は取得時に算出済みのものを読む（式を二重に持たない）
        roe = self._ratio_of(financial_data, 'roe')
        roa = self._ratio_of(financial_data, 'roa')
        
        # 収益性トレンド分析
        margin_trend = self._analyze_margin_trend(income_statements)
        roe_trend = self._analyze_roe_trend(income_statements, balance_sheets)
        
        return {
            "latest_metrics": {
                "gross_margin": gross_margin,
                "operating_margin": operating_margin,
                "net_margin": net_margin,
                "roe": roe,
                "roa": roa
            },
            "trends": {
                "margin_trend": margin_trend,
                "roe_trend": roe_trend
            },
            "analysis": {
                "profitability_score": self._calculate_profitability_score(
                    operating_margin, roe, roa
                ),
                "margin_stability": margin_trend.get('stability', 'stable'),
                "roe_consistency": roe_trend.get('consistency', 'consistent')
            }
        }
    
    def analyze_financial_health(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """財務健全性分析"""
        balance_sheets = financial_data.get('balance_sheet', [])
        cash_flows = financial_data.get('cash_flow', [])
        
        if not balance_sheets:
            return {"error": "貸借対照表データが不足しています"}
        
        latest_balance = balance_sheets[-1]
        latest_cf = cash_flows[-1] if cash_flows else {}
        
        # 安全性指標
        debt_ratio = self._ratio_of(financial_data, 'debt_ratio')
        equity_ratio = self._ratio_of(financial_data, 'equity_ratio')
        current_ratio = self._ratio_of(financial_data, 'current_ratio')
        
        
        # レバレッジ分析
        debt_to_equity = self._div(latest_balance.get('total_debt'), latest_balance.get('total_equity'))
        
        # 財務健全性スコア
        health_score = self._calculate_health_score(
            debt_ratio, current_ratio, equity_ratio
        )
        
        return {
            "safety_metrics": {
                "debt_ratio": debt_ratio,
                "equity_ratio": equity_ratio,
                "current_ratio": current_ratio
            },
            "leverage_metrics": {
                "debt_to_equity": debt_to_equity
            },
            "analysis": {
                "health_score": health_score,
                "financial_strength": self._assess_financial_strength(health_score),
                "liquidity_assessment": self._assess_liquidity(current_ratio),
                "leverage_assessment": self._assess_leverage(debt_to_equity)
            }
        }
    
    def analyze_growth(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """成長性分析"""
        income_statements = financial_data.get('income_statement', [])
        balance_sheets = financial_data.get('balance_sheet', [])
        
        if len(income_statements) < 2:
            return {"error": "成長分析には複数年のデータが必要です"}
        
        # 成長率計算
        revenue_cagr = self._calculate_cagr(
            [stmt['revenue'] for stmt in income_statements]
        )
        profit_cagr = self._calculate_cagr(
            [stmt['net_profit'] for stmt in income_statements]
        )
        assets_cagr = self._calculate_cagr(
            [bs['total_assets'] for bs in balance_sheets]
        ) if balance_sheets else 0
        
        # 年次成長率
        latest_growth = self._calculate_yoy_growth(income_statements[-2:])
        
        # 成長の安定性
        revenue_volatility = self._calculate_growth_volatility(
            [stmt['revenue'] for stmt in income_statements]
        )
        
        # 成長質評価
        growth_quality = self._assess_growth_quality(
            revenue_cagr, profit_cagr, revenue_volatility
        )
        
        return {
            "growth_rates": {
                "revenue_cagr": revenue_cagr,
                "profit_cagr": profit_cagr,
                "assets_cagr": assets_cagr
            },
            "latest_growth": latest_growth,
            "volatility": {
                "revenue_volatility": revenue_volatility,
                "growth_stability": "high" if revenue_volatility < 0.1 else "medium" if revenue_volatility < 0.2 else "low"
            },
            "analysis": {
                "growth_quality": growth_quality,
                "growth_sustainability": self._assess_growth_sustainability(
                    revenue_cagr, profit_cagr
                ),
                "growth_consistency": self._assess_growth_consistency(
                    [stmt['revenue'] for stmt in income_statements]
                )
            }
        }
    
    def analyze_efficiency(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """効率性分析"""
        income_statements = financial_data.get('income_statement', [])
        balance_sheets = financial_data.get('balance_sheet', [])
        
        if not income_statements or not balance_sheets:
            return {"error": "効率性分析にはPL・BS両方のデータが必要です"}
        
        latest_income = income_statements[-1]
        latest_balance = balance_sheets[-1]
        
        # 効率性指標
        asset_turnover = self._div(latest_income.get('revenue'), latest_balance.get('total_assets'))
        equity_turnover = self._div(latest_income.get('revenue'), latest_balance.get('total_equity'))
        
        # 運転資本効率
        current_assets = latest_balance.get('current_assets')
        current_liabilities = latest_balance.get('current_liabilities')
        if current_assets is None or current_liabilities is None:
            working_capital = 0
        else:
            working_capital = current_assets - current_liabilities
        working_capital_turnover = self._div(latest_income.get('revenue'), working_capital if working_capital > 0 else None)
        
        # DuPont分析
        dupont_analysis = self._dupont_analysis(latest_income, latest_balance)
        
        return {
            "efficiency_metrics": {
                "asset_turnover": asset_turnover,
                "equity_turnover": equity_turnover,
                "working_capital_turnover": working_capital_turnover
            },
            "dupont_analysis": dupont_analysis,
            "analysis": {
                "efficiency_score": self._calculate_efficiency_score(asset_turnover),
                "asset_utilization": self._assess_asset_utilization(asset_turnover),
                "working_capital_management": self._assess_working_capital_management(
                    working_capital_turnover
                )
            }
        }
    
    
    def comprehensive_analysis(self, financial_data: Dict[str, Any],
                               sector: str = None) -> Dict[str, Any]:
        """包括的財務分析。

        投資判定は返さない（独自スコアを根拠にした投資助言になるため）。
        sector は互換のために受け取るが、業界比較には使わない。
        """
        profitability = self.analyze_profitability(financial_data)
        health = self.analyze_financial_health(financial_data)
        growth = self.analyze_growth(financial_data)
        efficiency = self.analyze_efficiency(financial_data)

        overall_score = self._calculate_overall_score(
            profitability, health, growth, efficiency
        )

        return {
            "profitability": profitability,
            "financial_health": health,
            "growth": growth,
            "efficiency": efficiency,
            "overall_analysis": {
                "overall_score": overall_score,
                "key_strengths": self._identify_key_strengths(
                    profitability, health, growth, efficiency
                ),
                "key_concerns": self._identify_key_concerns(
                    profitability, health, growth, efficiency
                )
            }
        }
    
    # 内部計算メソッド
    
    def _calculate_cagr(self, values: List[float]) -> float:
        """年平均成長率（CAGR）。

        初期値・終端値のどちらかが 0 以下だと定義できないので 0 を返す
        （負の利益から正へ転じた場合などは、成長率で語れない）。
        """
        if len(values) < 2:
            return 0.0
        start, end = values[0], values[-1]
        if start is None or end is None or start <= 0 or end <= 0:
            return 0.0
        years = len(values) - 1
        return ((end / start) ** (1 / years) - 1) * 100
    
    def _calculate_yoy_growth(self, statements: List[Dict]) -> Dict[str, float]:
        """前年同期比成長率計算"""
        if len(statements) < 2:
            return {}
        
        current = statements[-1]
        previous = statements[-2]
        
        return {
            "revenue_growth": self._growth(current.get('revenue'), previous.get('revenue')),
            "profit_growth": self._growth(current.get('net_profit'), previous.get('net_profit')),
            "operating_profit_growth": self._growth(current.get('operating_profit'), previous.get('operating_profit'))
        }
    
    def _calculate_growth_volatility(self, values: List[float]) -> float:
        """成長率のボラティリティ計算"""
        values = [v for v in values if v is not None]
        if len(values) < 3:
            return 0
        
        growth_rates = []
        for i in range(1, len(values)):
            if values[i-1] is not None and values[i-1] > 0:
                growth_rate = self._growth(values[i], values[i-1])
                growth_rates.append(growth_rate)
        
        return statistics.stdev(growth_rates) if len(growth_rates) > 1 else 0
    
    def _dupont_analysis(self, income: Dict, balance: Dict) -> Dict[str, float]:
        """DuPont分析"""
        net_margin = self._div(income.get('net_profit'), income.get('revenue'))
        asset_turnover = self._div(income.get('revenue'), balance.get('total_assets'))
        equity_multiplier = self._div(balance.get('total_assets'), balance.get('total_equity'))
        
        roe_dupont = net_margin * asset_turnover * equity_multiplier
        
        return {
            "net_margin": net_margin,
            "asset_turnover": asset_turnover,
            "equity_multiplier": equity_multiplier,
            "roe_dupont": roe_dupont
        }
    
    
    
    
    
    
    # スコア計算・評価メソッド
    def _calculate_profitability_score(self, operating_margin: float, 
                                     roe: float, roa: float) -> float:
        """収益性スコア計算（100点満点）"""
        margin_score = min(operating_margin * 500, 40)  # 最大40点
        roe_score = min(roe * 300, 35)  # 最大35点
        roa_score = min(roa * 500, 25)  # 最大25点
        
        return margin_score + roe_score + roa_score
    
    def _calculate_health_score(self, debt_ratio: float, 
                              current_ratio: float, equity_ratio: float) -> float:
        """財務健全性スコア計算（100点満点）"""
        # 負債比率（低い方が良い）
        debt_score = max(0, 40 - debt_ratio * 60)
        
        # 流動比率（1.2以上が理想）
        current_score = min(current_ratio * 25, 35)
        
        # 自己資本比率（高い方が良い）
        equity_score = min(equity_ratio * 50, 25)
        
        return debt_score + current_score + equity_score
    
    def _calculate_efficiency_score(self, asset_turnover: float) -> float:
        """効率性スコア（100点満点）。

        棚卸資産・売掛金の内訳は取得元に無いため、総資産回転率だけで評価する。
        """
        return min(asset_turnover * 100, 100)
    
    def _calculate_overall_score(self, profitability: Dict, health: Dict,
                               growth: Dict, efficiency: Dict) -> float:
        """総合スコア計算"""
        profit_score = profitability.get('analysis', {}).get('profitability_score', 0)
        health_score = health.get('analysis', {}).get('health_score', 0)
        
        # 成長スコア（簡易計算）
        revenue_cagr = growth.get('growth_rates', {}).get('revenue_cagr', 0)
        growth_score = min(max(revenue_cagr * 200, 0), 100)
        
        efficiency_score = efficiency.get('analysis', {}).get('efficiency_score', 0)
        
        # 重み付け平均
        weights = {'profitability': 0.3, 'health': 0.3, 'growth': 0.2, 'efficiency': 0.2}
        
        overall = (profit_score * weights['profitability'] + 
                  health_score * weights['health'] +
                  growth_score * weights['growth'] +
                  efficiency_score * weights['efficiency'])
        
        return min(overall, 100)
    
    # 評価・判定メソッド
    def _assess_financial_strength(self, health_score: float) -> str:
        """財務体力評価"""
        if health_score >= 80:
            return "非常に良好"
        elif health_score >= 60:
            return "良好"
        elif health_score >= 40:
            return "普通"
        else:
            return "要注意"
    
    def _assess_growth_quality(self, revenue_cagr: float, profit_cagr: float,
                             volatility: float) -> str:
        """成長質評価"""
        if revenue_cagr > 0.1 and profit_cagr > revenue_cagr and volatility < 0.1:
            return "高品質成長"
        elif revenue_cagr > 0.05 and profit_cagr > 0:
            return "安定成長"
        elif revenue_cagr > 0:
            return "緩やかな成長"
        else:
            return "成長鈍化"
    
    
    def _identify_key_strengths(self, profitability: Dict, health: Dict,
                              growth: Dict, efficiency: Dict) -> List[str]:
        """主要な強みを特定"""
        strengths = []
        
        if profitability.get('analysis', {}).get('profitability_score', 0) > 70:
            strengths.append("高い収益性")
        
        if health.get('analysis', {}).get('health_score', 0) > 70:
            strengths.append("良好な財務健全性")
        
        revenue_cagr = growth.get('growth_rates', {}).get('revenue_cagr', 0)
        if revenue_cagr > 0.1:
            strengths.append("高い成長性")
        
        if efficiency.get('analysis', {}).get('efficiency_score', 0) > 70:
            strengths.append("効率的な資産活用")
        
        return strengths if strengths else ["特記すべき強みなし"]
    
    def _identify_key_concerns(self, profitability: Dict, health: Dict,
                             growth: Dict, efficiency: Dict) -> List[str]:
        """主要な懸念点を特定"""
        concerns = []
        
        if profitability.get('analysis', {}).get('profitability_score', 0) < 40:
            concerns.append("収益性の低さ")
        
        if health.get('analysis', {}).get('health_score', 0) < 40:
            concerns.append("財務健全性の懸念")
        
        revenue_cagr = growth.get('growth_rates', {}).get('revenue_cagr', 0)
        if revenue_cagr < 0:
            concerns.append("売上の減少傾向")
        
        if efficiency.get('analysis', {}).get('efficiency_score', 0) < 40:
            concerns.append("資産効率の低さ")
        
        return concerns if concerns else ["特記すべき懸念なし"]
    
    def _analyze_margin_trend(self, income_statements: List[Dict]) -> Dict[str, Any]:
        """利益率トレンド分析"""
        if len(income_statements) < 3:
            return {"trend": "insufficient_data"}
        
        margins = [stmt.get('operating_margin', 0) for stmt in income_statements]
        
        # トレンド判定
        if margins[-1] > margins[0]:
            trend = "improving"
        elif margins[-1] < margins[0]:
            trend = "deteriorating"
        else:
            trend = "stable"
        
        # 安定性判定
        margin_volatility = statistics.stdev(margins) if len(margins) > 1 else 0
        stability = "stable" if margin_volatility < 0.02 else "volatile"
        
        return {
            "trend": trend,
            "stability": stability,
            "volatility": margin_volatility,
            "latest_margin": margins[-1],
            "average_margin": statistics.mean(margins)
        }
    
    def _analyze_roe_trend(self, income_statements: List[Dict], 
                          balance_sheets: List[Dict]) -> Dict[str, Any]:
        """ROEトレンド分析"""
        if len(income_statements) < 2 or len(balance_sheets) < 2:
            return {"trend": "insufficient_data"}
        
        roes = []
        for i in range(len(income_statements)):
            if i < len(balance_sheets):
                roe = self._div(income_statements[i].get('net_profit'), balance_sheets[i].get('total_equity'))
                roes.append(roe)
        
        if len(roes) < 2:
            return {"trend": "insufficient_data"}
        
        # 一貫性評価
        roe_volatility = statistics.stdev(roes)
        consistency = "consistent" if roe_volatility < 0.03 else "inconsistent"
        
        return {
            "consistency": consistency,
            "volatility": roe_volatility,
            "latest_roe": roes[-1],
            "average_roe": statistics.mean(roes)
        }
    
    
    
    
    
    def _assess_liquidity(self, current_ratio: float) -> str:
        """流動性評価。

        当座比率は棚卸資産の内訳が取得元に無いため算出せず、流動比率だけで見る。
        """
        if current_ratio > 1.5:
            return "良好"
        elif current_ratio > 1.2:
            return "普通"
        else:
            return "要注意"
    
    def _assess_leverage(self, debt_to_equity: float) -> str:
        """レバレッジ評価"""
        if debt_to_equity < 0.5:
            return "保守的"
        elif debt_to_equity < 1.0:
            return "適度"
        elif debt_to_equity < 2.0:
            return "やや高い"
        else:
            return "高リスク"
    
    def _assess_asset_utilization(self, asset_turnover: float) -> str:
        """資産活用度評価"""
        if asset_turnover > 1.5:
            return "効率的"
        elif asset_turnover > 1.0:
            return "普通"
        else:
            return "非効率"
    
    def _assess_working_capital_management(self, wc_turnover: float) -> str:
        """運転資本管理評価"""
        if wc_turnover > 10:
            return "優秀"
        elif wc_turnover > 5:
            return "良好"
        elif wc_turnover > 0:
            return "普通"
        else:
            return "要改善"
    
    def _assess_growth_sustainability(self, revenue_cagr: float, profit_cagr: float) -> str:
        """成長持続性評価"""
        if profit_cagr > revenue_cagr and revenue_cagr > 0.05:
            return "持続可能性高"
        elif revenue_cagr > 0.03:
            return "持続可能性中"
        else:
            return "持続可能性低"
    
    def _assess_growth_consistency(self, revenues: List[float]) -> str:
        """成長一貫性評価"""
        if len(revenues) < 3:
            return "データ不足"
        
        growth_rates = []
        for i in range(1, len(revenues)):
            if revenues[i-1] is not None and revenues[i-1] > 0:
                growth_rate = self._growth(revenues[i], revenues[i-1])
                growth_rates.append(growth_rate)
        
        if not growth_rates:
            return "データ不足"
        
        # 負の成長率の割合
        negative_count = sum(1 for rate in growth_rates if rate < 0)
        negative_ratio = self._div(negative_count, len(growth_rates))
        
        if negative_ratio == 0:
            return "一貫して成長"
        elif negative_ratio < 0.3:
            return "概ね一貫"
        else:
            return "不安定"