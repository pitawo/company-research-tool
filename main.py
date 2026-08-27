import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path
import yaml
from dotenv import load_dotenv
import os

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 環境変数を読み込み
load_dotenv(project_root / ".env")

# 設定ファイルを読み込み
def load_config():
    config_path = project_root / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

config = load_config()

from utils.data_sources import DataSourceManager
from utils.financial_analysis import FinancialAnalyzer
from utils.report_generator import ReportGenerator
from components.company_overview import CompanyOverview
from components.financial_dashboard import FinancialDashboard

# ページ設定（config.yamlから読み込み）
ui_config = config.get('ui', {}).get('page_config', {})
st.set_page_config(
    page_title=ui_config.get('page_title', "企業リサーチシステム"),
    page_icon=ui_config.get('page_icon', "📊"),
    layout=ui_config.get('layout', "wide"),
    initial_sidebar_state=ui_config.get('initial_sidebar_state', "expanded")
)

# セッション状態の初期化
def init_session_state():
    if 'current_company' not in st.session_state:
        st.session_state.current_company = None
    if 'company_data' not in st.session_state:
        st.session_state.company_data = None
    if 'financial_data' not in st.session_state:
        st.session_state.financial_data = None
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    if 'generated_report' not in st.session_state:
        st.session_state.generated_report = None

def main():
    init_session_state()
    
    # タイトル
    st.title("🏢 企業リサーチシステム")
    st.markdown("日本企業の包括的分析レポート作成システム")
    st.markdown("---")
    
    # サイドバー設定
    setup_sidebar()
    
    # メインコンテンツ
    if st.session_state.current_company:
        show_main_dashboard()
    else:
        show_welcome_screen()

def setup_sidebar():
    with st.sidebar:
        st.header("🔍 企業検索")
        
        # 企業検索方法の選択
        search_method = st.selectbox(
            "検索方法",
            ["企業名", "証券コード", "銘柄名"]
        )
        
        # 検索入力
        if search_method == "証券コード":
            search_input = st.text_input(
                "証券コードを入力",
                placeholder="例: 6758, 9843",
                help="収録5社以外の証券コードは Yahoo! Finance から取得します"
            )
        else:
            search_input = st.text_input(
                f"{search_method}を入力",
                placeholder="例: ソニーグループ, 味の素",
                help=f"{search_method}を入力してください"
            )
        
        # 検索ボタン
        if st.button("🔍 企業分析開始", type="primary"):
            if search_input:
                search_company(search_input, search_method)
            else:
                st.error("検索キーワードを入力してください")
        
        st.markdown("---")
        
        # 検索履歴
        st.subheader("📜 検索履歴")
        if st.session_state.search_history:
            history_options = ["選択してください"] + [
                f"{item['name']} ({item['code']})"
                for item in st.session_state.search_history[-10:]  # 直近10件
            ]
            
            selected_history = st.selectbox(
                "過去の検索から選択",
                options=history_options
            )
            
            if selected_history != "選択してください":
                if st.button("🔄 再読み込み"):
                    history_item = next(
                        item for item in st.session_state.search_history
                        if f"{item['name']} ({item['code']})" == selected_history
                    )
                    load_from_history(history_item)
        else:
            st.info("検索履歴がありません")
        
        if st.button("🗑️ 履歴クリア"):
            st.session_state.search_history.clear()
            st.success("履歴をクリアしました")
        
        st.markdown("---")
        
        # 設定オプション
        st.subheader("⚙️ 分析設定")
        
        analysis_period = st.selectbox(
            "分析期間",
            ["過去3年", "過去5年", "過去10年"],
            index=1
        )
        
        
        
        # 設定をセッション状態に保存
        st.session_state.analysis_period = analysis_period

def get_data_manager():
    """DataSourceManager をセッションに持たせる（ライブ取得の結果を持ち越すため）。"""
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataSourceManager()
    return st.session_state.data_manager

def search_company(search_input, search_method):
    try:
        with st.spinner("企業情報を検索中..."):
            data_manager = get_data_manager()

            if search_method == "証券コード":
                company_info = data_manager.get_company_by_code(search_input)
                if company_info is None:
                    # 同梱データに無い証券コードは Yahoo! Finance から取りに行く
                    fetched, message = data_manager.fetch_live(search_input)
                    if fetched:
                        company_info = data_manager.get_company_by_code(search_input)
                        st.info(message)
                    else:
                        st.warning(message)
            else:
                company_info = data_manager.get_company_by_name(search_input)

            if company_info:
                st.session_state.current_company = company_info
                
                # 財務データも取得
                financial_data = data_manager.get_financial_data(
                    company_info['code'],
                    periods=get_periods_from_setting()
                )
                st.session_state.financial_data = financial_data
                
                # 履歴に追加
                add_to_search_history(company_info)
                
                st.success(f"✅ {company_info['name']} の分析データを取得しました")
                st.rerun()
            else:
                st.error("❌ 企業が見つかりませんでした")
                
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")

def get_periods_from_setting():
    period_map = {
        "過去3年": 3,
        "過去5年": 5,
        "過去10年": 10
    }
    return period_map.get(st.session_state.get('analysis_period', '過去5年'), 5)

def add_to_search_history(company_info):
    # 重複チェック
    existing = next(
        (h for h in st.session_state.search_history 
         if h['code'] == company_info['code']), 
        None
    )
    
    if existing:
        # 既存項目を更新
        existing['timestamp'] = datetime.now()
    else:
        # 新規追加
        st.session_state.search_history.append({
            'name': company_info['name'],
            'code': company_info['code'],
            'timestamp': datetime.now()
        })
    
    # 最大50件まで保持
    if len(st.session_state.search_history) > 50:
        st.session_state.search_history = st.session_state.search_history[-50:]

def load_from_history(history_item):
    search_company(history_item['code'], "証券コード")

def show_welcome_screen():
    st.markdown("""
    ## 👋 企業リサーチシステムへようこそ
    
    このシステムでは、日本企業の包括的な分析レポートを自動生成できます。
    
    ### 📋 分析できること
    
    1. **企業概要** - 商号・業種・従業員数・時価総額・直近期の成長率
    2. **財務分析** - 直近5期の損益／貸借対照表／キャッシュフローと財務比率（ROE・ROA・自己資本比率ほか）
    
    数値は Yahoo! Finance の公開データを取得したもので、乱数やサンプルは含まない。
    取得できなかった項目は「-」と表示する。決算期に飛びがある場合や、
    非継続事業の影響で最終利益が実態とずれる場合は、画面に注記を出す。
    
    ### 🚀 使い方
    
    1. サイドバーで企業名または証券コードを入力
    2. 「🔍 企業分析開始」ボタンをクリック
    3. 企業概要・財務分析のタブで内容を確認
    4. 必要に応じてレポートを生成・ダウンロード
    
    ---
    
    **👈 左のサイドバーから企業検索を開始してください**
    """)
    
    # 同梱データに収録している企業
    st.subheader("📇 収録企業")
    
    data_manager = get_data_manager()
    meta = data_manager.snapshot_meta()
    sample_companies = data_manager.list_companies()

    st.caption("出典: %s ／ 取得日時: %s ／ 金額の単位: %s"
               % (meta.get('source') or '—', meta.get('generated_at') or '—', meta.get('unit') or '—'))

    if not sample_companies:
        st.warning("同梱データが見つかりません。`python tools/fetch_financials.py` を実行してください。")
        return
    
    cols = st.columns(len(sample_companies))
    
    for i, company in enumerate(sample_companies):
        with cols[i]:
            if st.button(
                f"{company['name']}\n({company['code']})",
                key=f"sample_{i}",
                help=f"業種: {company['sector']}"
            ):
                search_company(company['code'], "証券コード")

def show_main_dashboard():
    company = st.session_state.current_company
    
    # 企業名とコードを表示
    st.subheader(f"📊 {company['name']} ({company['code']}) 分析レポート")
    
    # レポート生成ボタン
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        if st.button("📄 完全レポート生成", type="primary"):
            generate_full_report()
    
    with col2:
        if st.session_state.generated_report:
            st.download_button(
                label="📥 レポートダウンロード",
                data=st.session_state.generated_report,
                file_name=f"{company['name']}_analysis_report_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )
    
    # タブ形式でコンテンツを表示
    tab1, tab2 = st.tabs([
        "🏢 企業概要",
        "💰 財務分析"
    ])

    with tab1:
        company_overview = CompanyOverview(st.session_state.current_company)
        company_overview.display()

    with tab2:
        if st.session_state.financial_data:
            # 業界ベンチマークは出どころを示せないので sector は渡さない（業界比較は行わない）
            analyzer = FinancialAnalyzer()
            analysis_results = analyzer.comprehensive_analysis(st.session_state.financial_data)
            financial_dashboard = FinancialDashboard(
                st.session_state.financial_data, analysis_results)
            financial_dashboard.display()
        else:
            st.info("財務データがありません")

def generate_full_report():
    try:
        with st.spinner("包括的レポートを生成中..."):
            report_generator = ReportGenerator()
            
            report = report_generator.generate_comprehensive_report(
                st.session_state.current_company,
                st.session_state.financial_data
            )
            
            st.session_state.generated_report = report
            st.success("✅ レポートが生成されました！ダウンロードボタンからダウンロードできます。")
            
    except Exception as e:
        st.error(f"❌ レポート生成エラー: {str(e)}")

if __name__ == "__main__":
    main()