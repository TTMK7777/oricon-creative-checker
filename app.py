"""
オリコン クリエイティブチェッカー - Streamlit Web アプリケーション

ファイル形式を問わず、オリコン顧客満足度(R)調査の表現規定準拠を
GPT-4o Visionで自動チェックします。
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

import streamlit as st
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from core.file_processor import FileProcessor
from core.openai_checker import OpenAICreativeChecker

# 環境変数読み込み（ローカル実行時はグローバルの.env.localを参照）
env_path = Path.home() / ".env.local"
load_dotenv(env_path)


def get_api_key() -> str:
    """APIキーを取得（優先順位: Streamlit Secrets > 環境変数 > 空文字）"""
    # 1. Streamlit Cloud Secrets（デプロイ時）
    try:
        if hasattr(st, 'secrets') and 'openai' in st.secrets:
            return st.secrets["openai"]["api_key"]
    except Exception:
        pass

    # 2. 環境変数（ローカル実行時）
    env_key = os.getenv("OPENAI_API_KEY", "")
    if env_key:
        return env_key

    # 3. 見つからない場合は空文字（ユーザー入力を求める）
    return ""


# ページ設定
st.set_page_config(
    page_title="オリコン クリエイティブチェッカー",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .stApp {
        max-width: 1400px;
        margin: 0 auto;
    }
    .result-card {
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 5px solid;
    }
    .result-ok {
        background-color: #d4edda;
        border-left-color: #28a745;
    }
    .result-ng {
        background-color: #f8d7da;
        border-left-color: #dc3545;
    }
    .result-warning {
        background-color: #fff3cd;
        border-left-color: #ffc107;
    }
    .result-error {
        background-color: #f5f5f5;
        border-left-color: #6c757d;
    }
    .issue-critical {
        color: #dc3545;
        font-weight: bold;
    }
    .issue-warning {
        color: #856404;
    }
    .issue-info {
        color: #0c5460;
    }
    .detected-element {
        background-color: #e9ecef;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.25rem 0;
    }
    .header-title {
        color: #1e3a5f;
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .header-subtitle {
        color: #6c757d;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """セッション状態を初期化"""
    if "results" not in st.session_state:
        st.session_state.results = []
    if "processing" not in st.session_state:
        st.session_state.processing = False


def get_judgment_color(judgment: str) -> str:
    """判定結果に応じた色クラスを返す"""
    if judgment == "問題なし":
        return "result-ok"
    elif judgment == "問題あり":
        return "result-ng"
    elif judgment == "要確認":
        return "result-warning"
    else:
        return "result-error"


def get_judgment_emoji(judgment: str) -> str:
    """判定結果に応じた絵文字を返す"""
    if judgment == "問題なし":
        return "✅"
    elif judgment == "問題あり":
        return "❌"
    elif judgment == "要確認":
        return "⚠️"
    else:
        return "🔄"


def get_severity_class(severity: str) -> str:
    """重要度に応じたCSSクラスを返す"""
    if severity == "critical":
        return "issue-critical"
    elif severity == "warning":
        return "issue-warning"
    else:
        return "issue-info"


def display_result(result: Dict[str, Any]):
    """判定結果を表示"""
    judgment = result.get("judgment", "不明")
    color_class = get_judgment_color(judgment)
    emoji = get_judgment_emoji(judgment)

    with st.container():
        st.markdown(f"""
        <div class="result-card {color_class}">
            <h3>{emoji} {result.get('file_name', '不明')}</h3>
            <p><strong>企業名:</strong> {result.get('company_name', '不明')}</p>
            <p><strong>判定結果:</strong> <span style="font-size: 1.2rem; font-weight: bold;">{judgment}</span></p>
        </div>
        """, unsafe_allow_html=True)

        # 問題点の表示
        issues = result.get("issues", [])
        if issues:
            st.markdown("#### 🔍 検出された問題")
            for issue in issues:
                severity = issue.get("severity", "info")
                category = issue.get("category", "その他")
                description = issue.get("description", "")
                severity_class = get_severity_class(severity)

                severity_label = {
                    "critical": "🔴 重大",
                    "warning": "🟡 警告",
                    "info": "🔵 情報"
                }.get(severity, "ℹ️")

                st.markdown(f"""
                <p class="{severity_class}">
                    <strong>{severity_label} [{category}]</strong>: {description}
                </p>
                """, unsafe_allow_html=True)

        # 検出された要素の表示
        detected = result.get("detected_elements", {})
        if detected:
            st.markdown("#### 📋 検出された要素")
            col1, col2 = st.columns(2)

            with col1:
                year = detected.get("year")
                st.markdown(f'<div class="detected-element"><strong>年度:</strong> {year if year else "❌ 未検出"}</div>', unsafe_allow_html=True)

                issuer = detected.get("issuer")
                st.markdown(f'<div class="detected-element"><strong>発行元:</strong> {issuer if issuer else "❌ 未検出"}</div>', unsafe_allow_html=True)

            with col2:
                ranking = detected.get("ranking_name")
                st.markdown(f'<div class="detected-element"><strong>ランキング名:</strong> {ranking if ranking else "❌ 未検出"}</div>', unsafe_allow_html=True)

                position = detected.get("position")
                st.markdown(f'<div class="detected-element"><strong>順位:</strong> {position if position else "❌ 未検出"}</div>', unsafe_allow_html=True)

            trademark = detected.get("trademark_symbol", False)
            trademark_status = "✅ あり" if trademark else "❌ なし"
            st.markdown(f'<div class="detected-element"><strong>(R)マーク:</strong> {trademark_status}</div>', unsafe_allow_html=True)

        # 備考の表示
        notes = result.get("notes")
        if notes:
            st.markdown("#### 📝 備考・確認事項")
            st.info(notes)

        st.markdown("---")


def main():
    """メインアプリケーション"""
    init_session_state()

    # ヘッダー
    st.markdown('<p class="header-title">🏆 オリコン クリエイティブチェッカー</p>', unsafe_allow_html=True)
    st.markdown('<p class="header-subtitle">ファイルをアップロードするだけで、オリコン顧客満足度®調査の表現規定準拠を自動チェック</p>', unsafe_allow_html=True)

    # サイドバー
    with st.sidebar:
        st.header("⚙️ 設定")

        # APIキー取得（Secrets > 環境変数 > ユーザー入力）
        default_api_key = get_api_key()

        if default_api_key:
            st.success("APIキー設定済み")
            api_key = default_api_key
        else:
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                help="OpenAI APIキーを入力してください"
            )

        st.markdown("---")

        st.header("📖 対応ファイル形式")
        st.markdown("""
        - **画像**: PNG, JPG, JPEG, GIF, WEBP, BMP
        - **ドキュメント**: PDF（全ページを画像化して判定）
        """)

        st.markdown("---")

        st.header("⚠️ 注意事項")
        st.warning("""
        - AI判定は補助的なものです
        - 最終確認は必ず担当者が行ってください
        - (R)マークの検出精度は環境依存です
        """)

        st.markdown("---")

        st.header("💰 コスト目安")
        st.info("""
        - 画像1枚: 約$0.01〜0.03
        - PDF(5ページ): 約$0.05〜0.15
        """)

    # メインエリア
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📤 ファイルアップロード")

        uploaded_files = st.file_uploader(
            "クリエイティブファイルをアップロード",
            type=["png", "jpg", "jpeg", "gif", "webp", "bmp", "pdf"],
            accept_multiple_files=True,
            help="複数ファイルを同時にアップロードできます"
        )

        if uploaded_files:
            st.success(f"{len(uploaded_files)} 件のファイルがアップロードされました")

            # ファイルリスト表示
            for uploaded_file in uploaded_files:
                file_size = len(uploaded_file.getvalue()) / 1024  # KB
                st.text(f"📄 {uploaded_file.name} ({file_size:.1f} KB)")

        # チェック実行ボタン
        if st.button("🔍 チェック実行", type="primary", disabled=not uploaded_files or not api_key):
            if not api_key:
                st.error("OpenAI APIキーを入力してください")
            else:
                st.session_state.processing = True
                st.session_state.results = []

                try:
                    # プロセッサとチェッカーを初期化
                    processor = FileProcessor()
                    checker = OpenAICreativeChecker(api_key=api_key)

                    # プログレスバー
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    total_files = len(uploaded_files)

                    for i, uploaded_file in enumerate(uploaded_files):
                        status_text.text(f"処理中: {uploaded_file.name} ({i + 1}/{total_files})")

                        try:
                            # ファイルを処理
                            uploaded_file.seek(0)  # ファイルポインタをリセット
                            images = processor.process_uploaded_file(uploaded_file)

                            # 画像をチェック
                            results = checker.check_multiple_images(images, uploaded_file.name)
                            st.session_state.results.extend(results)

                        except Exception as e:
                            st.session_state.results.append({
                                "file_name": uploaded_file.name,
                                "company_name": "不明",
                                "judgment": "エラー",
                                "issues": [{
                                    "severity": "critical",
                                    "category": "処理エラー",
                                    "description": str(e)
                                }],
                                "detected_elements": {},
                                "notes": "ファイル処理中にエラーが発生しました"
                            })

                        # プログレス更新
                        progress_bar.progress((i + 1) / total_files)

                    status_text.text("✅ チェック完了！")
                    st.session_state.processing = False

                except Exception as e:
                    st.error(f"エラーが発生しました: {str(e)}")
                    st.session_state.processing = False

    with col2:
        st.header("📊 判定結果")

        if st.session_state.results:
            # サマリー
            total = len(st.session_state.results)
            ok_count = sum(1 for r in st.session_state.results if r.get("judgment") == "問題なし")
            ng_count = sum(1 for r in st.session_state.results if r.get("judgment") == "問題あり")
            warn_count = sum(1 for r in st.session_state.results if r.get("judgment") == "要確認")

            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("合計", total)
            col_b.metric("問題なし", ok_count)
            col_c.metric("問題あり", ng_count)
            col_d.metric("要確認", warn_count)

            st.markdown("---")

            # 結果一覧
            for result in st.session_state.results:
                display_result(result)

            # JSON エクスポート
            st.download_button(
                label="📥 結果をJSONでダウンロード",
                data=json.dumps(st.session_state.results, ensure_ascii=False, indent=2),
                file_name=f"creative_check_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

        else:
            st.info("ファイルをアップロードして「チェック実行」をクリックしてください")

    # フッター
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6c757d; font-size: 0.9rem;">
        <p>オリコン クリエイティブチェッカー v1.0.0</p>
        <p>⚠️ AI判定は補助的なものです。最終確認は必ず担当者が行ってください。</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
