# 引継ぎ資料 - オリコン クリエイティブチェッカー

**作成日**: 2025-11-26
**作成者**: Claude Code + Tさん

---

## 1. プロジェクト概要

オリコン顧客満足度調査の表現規定準拠を、GPT-4o Visionで自動チェックするStreamlit Webアプリケーション。

### 主な機能
- ファイル形式を問わず対応（PNG, JPG, PDF等）
- PDF自動画像化（PyMuPDF）
- GPT-4o Visionによる判定
- 要確認事項の色分け表示
- JSON形式で結果エクスポート

---

## 2. 現在の状態

| 項目 | 状態 |
|------|------|
| ローカル開発 | 完了 |
| GitHubリポジトリ | 作成済み・プッシュ済み |
| セキュリティ監査 | 完了（問題なし） |
| Streamlit Cloudデプロイ | **未完了** |

---

## 3. リポジトリ情報

- **GitHub URL**: https://github.com/TTMK7777/oricon-creative-checker
- **ブランチ**: main
- **公開設定**: Public

---

## 4. 次のステップ: Streamlit Cloudデプロイ

### 手順

1. **Streamlit Cloudにログイン**
   - URL: https://share.streamlit.io/
   - GitHubアカウント（TTMK7777）でログイン

2. **新しいアプリをデプロイ**
   - 「New app」をクリック
   - Repository: `TTMK7777/oricon-creative-checker`
   - Branch: `main`
   - Main file path: `app.py`

3. **Secretsを設定**
   - 「Advanced settings」→「Secrets」に以下を入力:
   ```toml
   [openai]
   api_key = "実際のOpenAI APIキーをここに入力"
   ```

4. **Deploy!をクリック**

### デプロイ後のURL
デプロイ完了後、以下の形式でURLが発行されます:
```
https://oricon-creative-checker.streamlit.app
```
（実際のURLはデプロイ時に確定）

---

## 5. ファイル構成

```
oricon-creative-checker/
├── app.py                      # メインアプリケーション
├── core/
│   ├── __init__.py
│   ├── file_processor.py       # PDF/画像→Base64変換
│   └── openai_checker.py       # GPT-4o Vision API連携
├── config/
│   └── prompt.txt              # 判定プロンプト
├── .streamlit/
│   ├── config.toml             # テーマ・サーバー設定
│   └── secrets.toml.example    # Secrets設定サンプル
├── requirements.txt            # 依存関係
├── .env.example                # 環境変数サンプル
├── .gitignore                  # Git除外設定
├── README.md                   # 利用者向けドキュメント
├── HANDOVER.md                 # この引継ぎ資料
└── start.bat                   # ローカル起動用バッチ
```

---

## 6. APIキー管理

### 優先順位
1. **Streamlit Cloud Secrets** (デプロイ時)
   - `st.secrets["openai"]["api_key"]`
2. **環境変数** (ローカル実行時)
   - `~/.env.local` の `OPENAI_API_KEY`
3. **ユーザー手動入力** (フォールバック)
   - サイドバーのパスワード入力欄

### ローカル実行時の設定
`C:\Users\t-tsuji\.env.local` に以下が設定済み:
```
OPENAI_API_KEY=sk-proj-xxxxx...
```

---

## 7. セキュリティ監査結果

| チェック項目 | 結果 |
|-------------|------|
| APIキーハードコード | なし |
| 機密情報漏洩リスク | なし |
| .gitignore設定 | 適切 |
| XSRF保護 | 有効 |
| 依存関係 | 安全 |

**結論: パブリック公開OK**

---

## 8. ローカル実行方法

```bash
# プロジェクトフォルダに移動
cd "C:\Users\t-tsuji\★AI関連\trademark_converter\oricon-creative-checker"

# 起動
streamlit run app.py

# または
start.bat をダブルクリック
```

---

## 9. テストファイル

以下のテストファイルが利用可能:
```
C:\Users\t-tsuji\★AI関連\trademark_converter\テストファイル\
├── 1-1.png
├── 1-2.png
├── 2-1.png
├── 2-2.png
├── 3-1.pdf
└── 3-2.pdf
```

---

## 10. コスト目安

| 処理対象 | 概算コスト |
|----------|-----------|
| 画像1枚 | 約$0.01〜0.03 |
| PDF（5ページ） | 約$0.05〜0.15 |

---

## 11. 関連リソース

- **元のGPTプロンプト**: `C:\Users\t-tsuji\★AI関連\trademark_converter\GPTプロンプト.txt`
- **没プロジェクト**: `C:\Users\t-tsuji\★AI関連\trademark_converter\没プロジェクト\`
- **OpenAI APIドキュメント**: https://platform.openai.com/docs
- **Streamlit Cloudドキュメント**: https://docs.streamlit.io/streamlit-community-cloud

---

## 12. 注意事項

- AI判定は補助的なもの。最終確認は必ず担当者が行うこと
- (R)マークの検出精度は画像品質に依存
- 大量処理時はAPIコストに注意

---

**以上**
