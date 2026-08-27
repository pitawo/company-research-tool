import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, Any, List
import numpy as np

class FinancialDashboard:
    """
    財務ダッシュボードを表示するコンポーネント
    """
    
    def __init__(self, financial_data: Dict[str, Any], analysis_results: Dict[str, Any]):
        self.financial_data = financial_data
        self.analysis_results = analysis_results
    
    def display(self):
        """財務ダッシュボードを表示"""
        self._display_summary_metrics()
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            self._display_profitability_analysis()
            
        with col2:
            self._display_financial_health()
        
        st.markdown("---")
        
        self._display_growth_trends()
        
        st.markdown("---")
        
        self._display_efficiency_metrics()
        
    
    def _display_summary_metrics(self):
        """主要指標サマリーを表示"""
        st.header("📊 財務サマリー")
        
        # 最新年度の財務データを取得
        latest_income = self.financial_data.get('income_statement', [])[-1] if self.financial_data.get('income_statement') else {}
        latest_balance = self.financial_data.get('balance_sheet', [])[-1] if self.financial_data.get('balance_sheet') else {}
        
        # 主要指標を表示
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            revenue = latest_income.get('revenue', 0)
            revenue_growth = self._get_latest_growth_rate('revenue')
            st.metric(
                "売上高",
                f"{revenue / 100:.0f}億円",
                delta=f"{revenue_growth:+.1f}%",
                help="前年同期比"
            )
        
        with col2:
            operating_profit = latest_income.get('operating_profit', 0)
            profit_growth = self._get_latest_growth_rate('operating_profit')
            st.metric(
                "営業利益",
                f"{operating_profit / 100:.0f}億円",
                delta=f"{profit_growth:+.1f}%",
                help="前年同期比"
            )
        
        with col3:
            operating_margin = latest_income.get('operating_margin', 0)
            st.metric(
                "営業利益率",
                f"{operating_margin * 100:.1f}%",
                help="営業利益/売上高"
            )
        
        with col4:
            profitability = self.analysis_results.get('profitability', {})
            roe = profitability.get('latest_metrics', {}).get('roe', 0)
            st.metric(
                "ROE",
                f"{roe * 100:.1f}%",
                help="自己資本利益率"
            )
        
        with col5:
            health = self.analysis_results.get('financial_health', {})
            equity_ratio = health.get('safety_metrics', {}).get('equity_ratio', 0)
            st.metric(
                "自己資本比率",
                f"{equity_ratio * 100:.1f}%",
                help="財務安全性指標"
            )
        
        # 総合スコア表示（投資判定は出さない。独自スコアを根拠にした助言になるため）
        overall_score = self.analysis_results.get('overall_analysis', {}).get('overall_score', 0)

        st.markdown("### 🎯 総合評価")
        st.metric("財務スコア", f"{overall_score:.1f}/100")
        st.caption("収益性・健全性・成長性・効率性から本ツールが独自に算出した参考値。"
                   "投資判断には使えない。")
    
    def _display_profitability_analysis(self):
        """収益性分析を表示"""
        st.subheader("💰 収益性分析")
        
        profitability = self.analysis_results.get('profitability', {})
        latest_metrics = profitability.get('latest_metrics', {})
        
        # 収益性指標
        metrics_data = {
            "指標": ["売上総利益率", "営業利益率", "当期利益率", "ROE", "ROA"],
            "値": [
                f"{latest_metrics.get('gross_margin', 0) * 100:.1f}%",
                f"{latest_metrics.get('operating_margin', 0) * 100:.1f}%",
                f"{latest_metrics.get('net_margin', 0) * 100:.1f}%",
                f"{latest_metrics.get('roe', 0) * 100:.1f}%",
                f"{latest_metrics.get('roa', 0) * 100:.1f}%"
            ]
        }
        
        df_metrics = pd.DataFrame(metrics_data)
        st.dataframe(df_metrics, use_container_width=True)
        
        # 収益性スコア
        profitability_score = profitability.get('analysis', {}).get('profitability_score', 0)
        st.progress(profitability_score / 100)
        st.caption(f"収益性スコア: {profitability_score:.1f}/100")
        
        # マージントレンド分析
        trends = profitability.get('trends', {})
        margin_trend = trends.get('margin_trend', {})
        
        if margin_trend.get('trend') == 'improving':
            st.success("📈 利益率は改善傾向")
        elif margin_trend.get('trend') == 'deteriorating':
            st.warning("📉 利益率は悪化傾向")
        else:
            st.info("📊 利益率は安定推移")
    
    def _display_financial_health(self):
        """財務健全性分析を表示"""
        st.subheader("🏥 財務健全性")
        
        health = self.analysis_results.get('financial_health', {})
        safety_metrics = health.get('safety_metrics', {})
        leverage_metrics = health.get('leverage_metrics', {})
        
        # 安全性指標
        safety_data = {
            "指標": ["自己資本比率", "流動比率", "負債比率（有利子負債 / 総資産）"],
            "値": [
                f"{safety_metrics.get('equity_ratio', 0) * 100:.1f}%",
                f"{safety_metrics.get('current_ratio', 0):.1f}",
                f"{safety_metrics.get('debt_ratio', 0) * 100:.1f}%"
            ]
        }
        
        df_safety = pd.DataFrame(safety_data)
        st.dataframe(df_safety, use_container_width=True)
        
        # 財務健全性スコア
        health_score = health.get('analysis', {}).get('health_score', 0)
        st.progress(health_score / 100)
        st.caption(f"財務健全性スコア: {health_score:.1f}/100")
        
        # 財務体力評価
        financial_strength = health.get('analysis', {}).get('financial_strength', '普通')
        strength_colors = {
            "非常に良好": "🟢",
            "良好": "🔵",
            "普通": "🟡", 
            "要注意": "🔴"
        }
        color = strength_colors.get(financial_strength, "⚪")
        st.markdown(f"**財務体力**: {color} {financial_strength}")
    
    def _display_growth_trends(self):
        """成長トレンド分析を表示"""
        st.subheader("📈 成長トレンド分析")
        
        growth = self.analysis_results.get('growth', {})
        growth_rates = growth.get('growth_rates', {})
        
        # 成長率指標
        col1, col2, col3 = st.columns(3)
        
        with col1:
            revenue_cagr = growth_rates.get('revenue_cagr', 0)
            st.metric(
                "売上CAGR",
                f"{revenue_cagr * 100:+.1f}%",
                help="年平均成長率"
            )
        
        with col2:
            profit_cagr = growth_rates.get('profit_cagr', 0)
            st.metric(
                "利益CAGR", 
                f"{profit_cagr * 100:+.1f}%",
                help="年平均成長率"
            )
        
        with col3:
            assets_cagr = growth_rates.get('assets_cagr', 0)
            st.metric(
                "資産CAGR",
                f"{assets_cagr * 100:+.1f}%",
                help="年平均成長率"
            )
        
        # 売上高・利益推移グラフ
        income_statements = self.financial_data.get('income_statement', [])
        if income_statements:
            years = [stmt['year'] for stmt in income_statements]
            revenues = [stmt['revenue'] / 100 for stmt in income_statements]  # 億円換算
            profits = [stmt['operating_profit'] / 100 for stmt in income_statements]
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(
                go.Scatter(x=years, y=revenues, name="売上高", line=dict(color='blue')),
                secondary_y=False,
            )
            
            fig.add_trace(
                go.Scatter(x=years, y=profits, name="営業利益", line=dict(color='red')),
                secondary_y=True,
            )
            
            fig.update_xaxes(title_text="年度")
            fig.update_yaxes(title_text="売上高 (億円)", secondary_y=False)
            fig.update_yaxes(title_text="営業利益 (億円)", secondary_y=True)
            
            fig.update_layout(
                title="売上高・営業利益推移",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # 成長質評価
        growth_analysis = growth.get('analysis', {})
        growth_quality = growth_analysis.get('growth_quality', '安定成長')
        
        quality_colors = {
            "高品質成長": "🟢",
            "安定成長": "🔵",
            "緩やかな成長": "🟡",
            "成長鈍化": "🔴"
        }
        color = quality_colors.get(growth_quality, "⚪")
        st.markdown(f"**成長質評価**: {color} {growth_quality}")
    
    def _display_efficiency_metrics(self):
        """効率性指標を表示"""
        st.subheader("⚡ 効率性指標")
        
        efficiency = self.analysis_results.get('efficiency', {})
        efficiency_metrics = efficiency.get('efficiency_metrics', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 回転率指標
            st.markdown("**📊 回転率指標**")
            
            turnover_data = {
                "指標": ["総資産回転率", "自己資本回転率"],
                "値": [
                    f"{efficiency_metrics.get('asset_turnover', 0):.2f}回",
                    f"{efficiency_metrics.get('equity_turnover', 0):.2f}回",

                ]
            }
            
            df_turnover = pd.DataFrame(turnover_data)
            st.dataframe(df_turnover, use_container_width=True)
        
        with col2:
            # DuPont分析
            st.markdown("**🔬 DuPont分析**")
            
            dupont = efficiency.get('dupont_analysis', {})
            
            dupont_data = {
                "要素": ["売上純利益率", "総資産回転率", "財務レバレッジ", "ROE"],
                "値": [
                    f"{dupont.get('net_margin', 0) * 100:.2f}%",
                    f"{dupont.get('asset_turnover', 0):.2f}回",
                    f"{dupont.get('equity_multiplier', 0):.2f}倍",
                    f"{dupont.get('roe_dupont', 0) * 100:.2f}%"
                ]
            }
            
            df_dupont = pd.DataFrame(dupont_data)
            st.dataframe(df_dupont, use_container_width=True)
        
        # 効率性スコア
        efficiency_score = efficiency.get('analysis', {}).get('efficiency_score', 0)
        st.progress(efficiency_score / 100)
        st.caption(f"効率性スコア: {efficiency_score:.1f}/100")
        
        # 資産活用度評価
        asset_utilization = efficiency.get('analysis', {}).get('asset_utilization', '普通')
        utilization_colors = {
            "効率的": "🟢",
            "普通": "🟡",
            "非効率": "🔴"
        }
        color = utilization_colors.get(asset_utilization, "⚪")
        st.markdown(f"**資産活用度**: {color} {asset_utilization}")
    
    
    def _get_latest_growth_rate(self, metric: str) -> float:
        """最新の成長率を取得"""
        income_statements = self.financial_data.get('income_statement', [])
        
        if len(income_statements) < 2:
            return 0.0
        
        current = income_statements[-1].get(metric, 0)
        previous = income_statements[-2].get(metric, 1)  # ゼロ除算回避
        
        if previous == 0:
            return 0.0
        
        return ((current - previous) / previous) * 100
    
    def display_financial_charts(self):
        """財務チャート集を表示"""
        st.subheader("📊 財務チャート集")
        
        # ROE・ROA推移
        self._display_roe_roa_chart()
        
        # 資本構成推移
        self._display_capital_structure_chart()
        
        # 利益率推移
        self._display_margin_trend_chart()
    
    def _display_roe_roa_chart(self):
        """ROE・ROA推移チャート"""
        ratios = self.financial_data.get('ratios', [])
        
        if ratios:
            years = [ratio['year'] for ratio in ratios]
            roe_values = [ratio['roe'] * 100 for ratio in ratios]
            roa_values = [ratio['roa'] * 100 for ratio in ratios]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=years, 
                y=roe_values, 
                name='ROE',
                line=dict(color='red', width=3)
            ))
            
            fig.add_trace(go.Scatter(
                x=years, 
                y=roa_values, 
                name='ROA',
                line=dict(color='blue', width=3)
            ))
            
            fig.update_layout(
                title="ROE・ROA推移",
                xaxis_title="年度",
                yaxis_title="比率 (%)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _display_capital_structure_chart(self):
        """資本構成推移チャート"""
        balance_sheets = self.financial_data.get('balance_sheet', [])
        
        if balance_sheets:
            years = [bs['year'] for bs in balance_sheets]
            equity_ratios = [(bs['total_equity'] / bs['total_assets']) * 100 for bs in balance_sheets]
            debt_ratios = [(bs['total_debt'] / bs['total_assets']) * 100 for bs in balance_sheets]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=years,
                y=equity_ratios,
                name='自己資本比率',
                line=dict(color='green', width=3)
            ))
            
            fig.add_trace(go.Scatter(
                x=years,
                y=debt_ratios,
                name='負債比率',
                line=dict(color='orange', width=3)
            ))
            
            fig.update_layout(
                title="資本構成推移",
                xaxis_title="年度",
                yaxis_title="比率 (%)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _display_margin_trend_chart(self):
        """利益率推移チャート"""
        income_statements = self.financial_data.get('income_statement', [])
        
        if income_statements:
            years = [stmt['year'] for stmt in income_statements]
            gross_margins = [stmt.get('gross_margin', 0) * 100 for stmt in income_statements]
            operating_margins = [stmt.get('operating_margin', 0) * 100 for stmt in income_statements]
            net_margins = [stmt.get('net_margin', 0) * 100 for stmt in income_statements]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=years,
                y=gross_margins,
                name='売上総利益率',
                line=dict(color='lightblue', width=2)
            ))
            
            fig.add_trace(go.Scatter(
                x=years,
                y=operating_margins,
                name='営業利益率',
                line=dict(color='blue', width=3)
            ))
            
            fig.add_trace(go.Scatter(
                x=years,
                y=net_margins,
                name='当期利益率',
                line=dict(color='darkblue', width=2)
            ))
            
            fig.update_layout(
                title="利益率推移",
                xaxis_title="年度",
                yaxis_title="利益率 (%)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)