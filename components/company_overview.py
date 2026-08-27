import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List
from datetime import datetime

class CompanyOverview:
    """
    企業概要を表示するコンポーネント
    """
    
    def __init__(self, company_data: Dict[str, Any]):
        self.company_data = company_data
    
    def display(self):
        """企業概要を表示"""
        self._display_basic_info()
        
        st.markdown("---")
        
        self._display_business_segments()
        
        st.markdown("---")
        
        self._display_key_metrics()
        
        st.markdown("---")
        
    
    def _display_basic_info(self):
        """基本情報を表示"""
        st.header("🏢 企業基本情報")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 会社概要")
            
            # 基本情報を表形式で表示
            basic_info = {
                "項目": [
                    "会社名",
                    "証券コード", 
                    "本社所在地",
                    "設立年月日",
                    "代表者",
                    "従業員数",
                    "業種",
                    "上場市場"
                ],
                "内容": [
                    self.company_data.get('name', '不明'),
                    self.company_data.get('code', '不明'),
                    self.company_data.get('headquarters', '不明'),
                    self.company_data.get('establishment', '不明'),
                    self.company_data.get('representative', '不明'),
                    f"{self.company_data.get('employees', 0):,}人" if self.company_data.get('employees', 0) > 0 else '不明',
                    self.company_data.get('sector', '不明'),
                    self.company_data.get('market', '不明')
                ]
            }
            
            df_basic = pd.DataFrame(basic_info)
            st.table(df_basic)
        
        with col2:
            st.subheader("🌐 企業情報")
            
            # ウェブサイト
            website = self.company_data.get('website', '')
            if website:
                st.markdown(f"**ウェブサイト**: [{website}]({website})")
            else:
                st.markdown("**ウェブサイト**: 不明")
            
            # 英語名
            name_en = self.company_data.get('name_en', '')
            if name_en:
                st.markdown(f"**英語名**: {name_en}")
            
            # 設立からの経過年数
            establishment = self.company_data.get('establishment', '')
            if establishment:
                try:
                    est_year = int(establishment.split('-')[0])
                    years_since = datetime.now().year - est_year
                    st.metric("設立からの年数", f"{years_since}年")
                except:
                    pass
            
            # 時価総額（推定値）
            market_cap = self.company_data.get('market_cap', 0)
            if market_cap > 0:
                if market_cap >= 1000000:  # 1兆円以上
                    market_cap_formatted = f"{market_cap / 1000000:.1f}兆円"
                else:
                    market_cap_formatted = f"{market_cap / 10000:.0f}億円"
                st.metric("時価総額", market_cap_formatted)

        # 事業内容は取得元の原文（英語）で長いため、
        # 狭いカラムに入れず全幅の折りたたみに置く
        business_desc = self.company_data.get('business_description')
        if business_desc:
            with st.expander("📝 事業内容（出典: Yahoo! Finance・原文のまま）"):
                st.write(business_desc)

    def _display_business_segments(self):
        """事業セグメント情報を表示"""
        st.header("📊 事業セグメント")
        
        segments = self.company_data.get('segments', [])
        
        if not segments:
            st.info("事業セグメント情報がありません")
            return
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("セグメント別売上構成")
            
            # セグメントデータをDataFrameに変換
            segment_data = []
            for segment in segments:
                segment_data.append({
                    "セグメント": segment.get('name', '不明'),
                    "売上高(百万円)": segment.get('sales', 0),
                    "構成比(%)": segment.get('ratio', 0)
                })
            
            df_segments = pd.DataFrame(segment_data)
            st.dataframe(df_segments, use_container_width=True, hide_index=True)
        
        with col2:
            st.subheader("売上構成比")
            
            # 円グラフを作成
            if segments:
                fig = px.pie(
                    values=[s.get('ratio', 0) for s in segments],
                    names=[s.get('name', '不明') for s in segments],
                    title="事業セグメント別売上構成比"
                )
                
                fig.update_traces(
                    textposition='inside',
                    textinfo='percent+label'
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # セグメント分析
        if segments:
            st.subheader("📈 セグメント分析")
            
            # 最大セグメント
            max_segment = max(segments, key=lambda x: x.get('ratio', 0))
            st.info(f"**主力事業**: {max_segment.get('name', '不明')} (構成比: {max_segment.get('ratio', 0):.1f}%)")
            
            # セグメント数による分散度評価
            num_segments = len(segments)
            if num_segments >= 4:
                diversification = "高い"
            elif num_segments >= 2:
                diversification = "中程度"
            else:
                diversification = "低い"
            
            st.markdown(f"**事業多角化度**: {diversification} ({num_segments}セグメント)")
            
            # 集中度分析（上位2セグメントの合計比率）
            sorted_segments = sorted(segments, key=lambda x: x.get('ratio', 0), reverse=True)
            if len(sorted_segments) >= 2:
                top2_ratio = sorted_segments[0].get('ratio', 0) + sorted_segments[1].get('ratio', 0)
                st.markdown(f"**上位2事業集中度**: {top2_ratio:.1f}%")
    
    def _display_key_metrics(self):
        """主要指標を表示（取得できなかった項目は 0 ではなく「-」を出す）"""
        st.header("📊 主要指標")

        performance = self.company_data.get('recent_performance') or {}

        def pct(value, signed=False):
            if value is None:
                return "-"
            return ("%+.1f%%" if signed else "%.1f%%") % value

        period_label = performance.get('period')
        period_help = "前期比（%s年3月期など直近期）" % period_label if period_label else "前期比"

        # 4列だと本番の幅で数値が省略されるため 2列×2行にする
        col1, col2 = st.columns(2)

        with col1:
            employees = self.company_data.get('employees') or 0
            st.metric(
                "従業員数",
                f"{employees:,}人" if employees else "-",
                help="連結従業員数"
            )

        with col2:
            market_cap = self.company_data.get('market_cap') or 0
            if market_cap >= 1000000:
                cap_formatted = f"{market_cap / 1000000:.1f}兆円"
            elif market_cap > 0:
                cap_formatted = f"{market_cap / 10000:.0f}億円"
            else:
                cap_formatted = "-"
            st.metric("時価総額", cap_formatted, help="Yahoo! Finance の取得値")

        col3, col4 = st.columns(2)

        with col3:
            st.metric(
                "売上成長率",
                pct(performance.get('revenue_growth'), signed=True),
                help=period_help
            )

        with col4:
            st.metric(
                "ROE",
                pct(performance.get('roe')),
                help="自己資本利益率（純利益 / 自己資本）"
            )

        # 追加指標
        st.subheader("🎯 経営効率指標")

        col1, col2, col3 = st.columns(3)

        with col1:
            revenue = performance.get('revenue')
            employees = self.company_data.get('employees') or 0
            if revenue and employees:
                # revenue は百万円単位
                st.metric(
                    "従業員一人当たり売上",
                    f"{revenue / employees:.1f}百万円",
                    help="最新期の売上 / 連結従業員数"
                )
            else:
                st.metric("従業員一人当たり売上", "-")

        with col2:
            st.metric(
                "利益成長率",
                pct(performance.get('profit_growth'), signed=True),
                help=period_help + "・純利益"
            )

        with col3:
            debt_ratio = performance.get('debt_ratio')
            st.metric(
                "負債比率",
                "-" if debt_ratio is None else "%.1f%%" % (debt_ratio * 100),
                help="有利子負債 / 総資産"
            )

        notes = self.company_data.get('data_notes') or []
        if notes:
            with st.expander("⚠️ このデータに関する注記（%d件）" % len(notes)):
                for note in notes:
                    st.write("- " + note)

    def _display_company_history(self):
        """企業沿革を表示"""
        st.header("📜 企業沿革")
        
        # サンプル沿革データ（実際の実装では外部データから取得）
        company_name = self.company_data.get('name', '企業名不明')
        establishment = self.company_data.get('establishment', '不明')
        
        history_events = [
            {
                "年": establishment,
                "出来事": f"{company_name}設立"
            },
            {
                "年": "上場年",
                "出来事": f"{self.company_data.get('market', '東証')}に株式上場"
            },
            {
                "年": "事業拡大期",
                "出来事": "主力事業の拡大・多角化"
            },
            {
                "年": "現在",
                "出来事": f"{self.company_data.get('sector', '当該業界')}での事業展開"
            }
        ]
        
        # タイムライン形式で表示
        for i, event in enumerate(history_events):
            with st.container():
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    st.markdown(f"**{event['年']}**")
                
                with col2:
                    st.markdown(f"• {event['出来事']}")
                
                if i < len(history_events) - 1:
                    st.markdown("　　　↓")
        
        # 主要マイルストーン
        st.subheader("🏆 主要マイルストーン")
        
        milestones = [
            f"✅ {establishment}: 会社設立",
            f"✅ 上場: {self.company_data.get('market', '東証')}への株式上場",
            f"✅ 事業拡大: {self.company_data.get('sector', '業界')}での地位確立",
            "✅ 現在: 持続的成長とESG経営の推進"
        ]
        
        for milestone in milestones:
            st.markdown(milestone)
        
        # 企業文化・価値観
        st.subheader("💼 企業文化・価値観")
        
        # サンプル企業価値観
        values = [
            "**顧客第一**: お客様のニーズに応える製品・サービスの提供",
            "**技術革新**: 継続的な技術開発とイノベーションの創出", 
            "**社会貢献**: 持続可能な社会の実現への貢献",
            "**人材育成**: 従業員の成長と働きがいのある職場づくり"
        ]
        
        for value in values:
            st.markdown(f"• {value}")
    
    def display_quick_summary(self):
        """クイックサマリーを表示（他のコンポーネントから呼び出し可能）"""
        """企業の要約情報を簡潔に表示"""
        
        company_name = self.company_data.get('name', '企業名不明')
        code = self.company_data.get('code', '不明')
        sector = self.company_data.get('sector', '不明')
        
        st.markdown(f"""
        ### 📋 {company_name} ({code}) サマリー
        
        - **業種**: {sector}
        - **本社**: {self.company_data.get('headquarters', '不明')}
        - **従業員**: {self.company_data.get('employees', 0):,}人
        - **設立**: {self.company_data.get('establishment', '不明')}
        """)
        
        # 主力事業
        segments = self.company_data.get('segments', [])
        if segments:
            main_business = max(segments, key=lambda x: x.get('ratio', 0))
            st.markdown(f"- **主力事業**: {main_business.get('name', '不明')} ({main_business.get('ratio', 0):.1f}%)")
    
    def get_company_profile_data(self) -> Dict[str, Any]:
        """企業プロファイルデータを返す（他のコンポーネントで使用）"""
        return {
            "basic_info": {
                "name": self.company_data.get('name', '不明'),
                "code": self.company_data.get('code', '不明'),
                "sector": self.company_data.get('sector', '不明'),
                "headquarters": self.company_data.get('headquarters', '不明'),
                "employees": self.company_data.get('employees', 0),
                "establishment": self.company_data.get('establishment', '不明')
            },
            "business_info": {
                "segments": self.company_data.get('segments', []),
                "main_business": self._get_main_business(),
                "business_description": self.company_data.get('business_description', '不明')
            },
            "financial_highlights": {
                "market_cap": self.company_data.get('market_cap', 0),
                "recent_performance": self.company_data.get('recent_performance', {})
            }
        }
    
    def _get_main_business(self) -> str:
        """主力事業を特定"""
        segments = self.company_data.get('segments', [])
        if segments:
            main_segment = max(segments, key=lambda x: x.get('ratio', 0))
            return main_segment.get('name', '不明')
        return '不明'