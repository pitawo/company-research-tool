from datetime import datetime
from typing import Dict, Any, List
from .financial_analysis import FinancialAnalyzer

class ReportGenerator:
    """
    企業分析レポートを生成するクラス
    Markdown形式で包括的なレポートを作成
    """
    
    def __init__(self):
        self.financial_analyzer = FinancialAnalyzer()
    
    def generate_comprehensive_report(self, company_data: Dict[str, Any],
                                      financial_data: Dict[str, Any]) -> str:
        """企業分析レポートを生成する。

        実データで裏付けられる章だけを出力する（企業概要・財務分析）。
        """
        report_sections = []

        # レポートヘッダー
        report_sections.append(self._generate_header(company_data))

        # 1. 企業概要
        report_sections.append(self._generate_company_overview(company_data))

        # 2. 財務分析
        if financial_data:
            report_sections.append(
                self._generate_financial_analysis(company_data, financial_data))

        # レポートフッター
        report_sections.append(self._generate_footer())

        return "\n\n".join(report_sections)
    
    def _generate_header(self, company_data: Dict[str, Any]) -> str:
        """レポートヘッダー生成"""
        company_name = company_data.get('name', '企業名不明')
        company_code = company_data.get('code', '0000')
        
        return f"""# 企業分析レポート: {company_name} ({company_code})

**作成日**: {datetime.now().strftime('%Y年%m月%d日')}  
**作成者**: 企業リサーチシステム  
**対象企業**: {company_name} (証券コード: {company_code})

---"""
    
    def _generate_company_overview(self, company_data: Dict[str, Any]) -> str:
        """企業概要セクション（取得できた項目だけを書く）"""
        employees = company_data.get('employees')
        rows = [
            ("社名 / 証券コード", "%s / %s" % (company_data.get('name') or "不明",
                                               company_data.get('code') or "不明")),
            ("業種", company_data.get('sector')),
            ("上場市場", company_data.get('market')),
            ("本社所在地", company_data.get('headquarters')),
            ("従業員数", "{:,}人".format(employees) if employees else None),
            ("ウェブサイト", company_data.get('website')),
        ]

        lines = ["## 1. 企業概要（Company Snapshot）", ""]
        lines += ["* **%s**: %s" % (label, value) for label, value in rows if value]

        description = company_data.get('business_description')
        if description:
            lines += ["", "### 事業内容", "", description]

        notes = company_data.get('data_notes') or []
        if notes:
            lines += ["", "### このデータに関する注記", ""]
            lines += ["* " + note for note in notes]

        return "\n".join(lines)
    
    
    
    
    def _generate_financial_analysis(self, company_data: Dict[str, Any], 
                                   financial_data: Dict[str, Any]) -> str:
        """財務分析セクション生成"""
        company_name = company_data.get('name', '企業名不明')
        
        # 財務分析を実行
        analysis = self.financial_analyzer.comprehensive_analysis(
            financial_data, 
            company_data.get('sector')
        )
        
        income_statements = financial_data.get('income_statement', [])
        period_count = len(income_statements)
        financial_section = f"""## 2. 財務分析

### 過去{period_count}期の財務サマリー

#### 損益計算書（単位: 百万円）
| 年度 | 売上高 | 営業利益 | 当期利益 | 営業利益率 |
|------|--------|----------|----------|------------|"""
        
        # 損益データの追加
        for stmt in income_statements[-5:]:  # 直近5年
            year = stmt.get('year', '-')
            revenue = stmt.get('revenue', 0)
            operating_profit = stmt.get('operating_profit', 0)
            net_profit = stmt.get('net_profit', 0)
            operating_margin = stmt.get('operating_margin', 0) * 100
            
            financial_section += f"\n| {year} | {revenue:,} | {operating_profit:,} | {net_profit:,} | {operating_margin:.1f}% |"
        
        financial_section += """

#### 貸借対照表（単位: 百万円）
| 年度 | 総資産 | 純資産 | 負債 | 自己資本比率 |
|------|--------|--------|------|--------------|"""
        
        # 貸借対照表データの追加
        balance_sheets = financial_data.get('balance_sheet', [])
        for bs in balance_sheets[-5:]:  # 直近5年
            year = bs.get('year', '-')
            total_assets = bs.get('total_assets', 0)
            total_equity = bs.get('total_equity', 0)
            total_debt = bs.get('total_debt', 0)
            equity_ratio = (total_equity / total_assets * 100) if total_assets > 0 else 0
            
            financial_section += f"\n| {year} | {total_assets:,} | {total_equity:,} | {total_debt:,} | {equity_ratio:.1f}% |"
        
        # 財務比率分析
        profitability = analysis.get('profitability', {})
        health = analysis.get('financial_health', {})
        growth = analysis.get('growth', {})
        
        latest_metrics = profitability.get('latest_metrics', {})
        safety_metrics = health.get('safety_metrics', {})
        growth_rates = growth.get('growth_rates', {})
        
        financial_section += f"""

### 成長指標
* **売上CAGR**: {growth_rates.get('revenue_cagr', 0) * 100:.1f}%
* **利益CAGR**: {growth_rates.get('profit_cagr', 0) * 100:.1f}%

### 収益性指標
* **売上総利益率**: {latest_metrics.get('gross_margin', 0) * 100:.1f}%
* **営業利益率**: {latest_metrics.get('operating_margin', 0) * 100:.1f}%
* **ROE**: {latest_metrics.get('roe', 0) * 100:.1f}%
* **ROA**: {latest_metrics.get('roa', 0) * 100:.1f}%

### 安全性指標
* **自己資本比率**: {safety_metrics.get('equity_ratio', 0) * 100:.1f}%
* **流動比率**: {safety_metrics.get('current_ratio', 0):.1f}
* **負債比率**: {safety_metrics.get('debt_ratio', 0) * 100:.1f}%

### 総合評価
* **総合スコア**: {analysis.get('overall_analysis', {}).get('overall_score', 0):.1f}/100
  （収益性・健全性・成長性・効率性から本ツールが独自に算出した参考値。投資判断には使わないこと）"""
        
        return financial_section
    
    
    
    
    
    
    def _generate_footer(self) -> str:
        """レポートフッター生成"""
        return f"""---

## 免責事項

本レポートは公開データを機械的に集計したものです。各社の有価証券報告書と完全に一致することを保証せず、投資判断には使用できません。数値は必ず一次情報（有価証券報告書・決算短信）で確認してください。

**作成システム**: 企業リサーチシステム  
**作成日時**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}  
**データソース**: Yahoo! Finance（yfinance 経由で取得）

*このレポートは情報提供を目的としており、投資勧誘を意図するものではありません。*"""
    
    
