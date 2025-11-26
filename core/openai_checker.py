"""
OpenAI GPT-4o Vision ベースのクリエイティブチェッカー

画像をGPT-4o Visionに送信し、オリコン商標規定に基づいた判定を行います。
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from openai import OpenAI


class OpenAICreativeChecker:
    """OpenAI GPT-4o Visionベースのクリエイティブチェッカー"""

    def __init__(self, api_key: Optional[str] = None):
        """初期化

        Args:
            api_key: OpenAI APIキー（省略時は環境変数から取得）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")

        self.client = OpenAI(api_key=self.api_key)
        self.prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        """プロンプトファイルを読み込む"""
        # 複数の可能なパスを試行
        possible_paths = [
            Path(__file__).parent.parent / "config" / "prompt.txt",
            Path("config/prompt.txt"),
            Path("./config/prompt.txt"),
        ]

        for prompt_path in possible_paths:
            if prompt_path.exists():
                with open(prompt_path, "r", encoding="utf-8") as f:
                    return f.read()

        # デフォルトプロンプト（フォールバック）
        return self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """デフォルトプロンプトを返す"""
        return """
# オリコン顧客満足度調査 クリエイティブチェックAI

この画像を分析し、オリコン顧客満足度(R)調査の表現規定に準拠しているかを検証してください。

## チェック項目

1. **禁止表現**: 「オリコンランキング」「オリコン1位」「オリコンNo.1」などの禁止表現
2. **必須要素**: 年度、発行元（(R)マーク付き）、ランキング名、順位の4要素
3. **フォーマット**: 半角スペース区切り、(R)マークの存在
4. **ロゴ**: 変形・色変更・装飾などの禁止加工

## 出力フォーマット（JSON）

```json
{
  "file_name": "ファイル名",
  "company_name": "企業名（クリエイティブから判別）",
  "judgment": "問題なし / 問題あり / 要確認",
  "issues": [
    {
      "severity": "critical / warning / info",
      "category": "禁止表現 / 必須要素 / フォーマット / ロゴ / 視認性",
      "description": "具体的な問題内容"
    }
  ],
  "detected_elements": {
    "year": "検出された年度",
    "issuer": "検出された発行元表記",
    "ranking_name": "検出されたランキング名",
    "position": "検出された順位",
    "trademark_symbol": true/false
  },
  "notes": "その他の気づき・確認推奨事項"
}
```
"""

    def check_image(
        self,
        base64_image: str,
        media_type: str,
        file_name: str = "unknown",
        page_num: Optional[int] = None
    ) -> Dict[str, Any]:
        """画像をチェックして判定結果を返す

        Args:
            base64_image: Base64エンコードされた画像データ
            media_type: メディアタイプ（例: "image/png"）
            file_name: ファイル名
            page_num: ページ番号（PDFの場合）

        Returns:
            判定結果の辞書
        """
        # ページ情報を含むファイル名
        display_name = f"{file_name} (ページ {page_num + 1})" if page_num is not None else file_name

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": self.prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"このクリエイティブ画像を分析してください。ファイル名: {display_name}\n\n必ずJSON形式で結果を出力してください。"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1  # 低温度で一貫性のある判定
            )

            # レスポンスからJSONを抽出
            content = response.choices[0].message.content
            result = self._parse_response(content, display_name)

            return result

        except Exception as e:
            return {
                "file_name": display_name,
                "company_name": "不明",
                "judgment": "エラー",
                "issues": [
                    {
                        "severity": "critical",
                        "category": "システムエラー",
                        "description": f"API呼び出しエラー: {str(e)}"
                    }
                ],
                "detected_elements": {
                    "year": None,
                    "issuer": None,
                    "ranking_name": None,
                    "position": None,
                    "trademark_symbol": False
                },
                "notes": "APIエラーが発生しました。再試行してください。"
            }

    def _parse_response(self, content: str, file_name: str) -> Dict[str, Any]:
        """APIレスポンスをパースしてJSONに変換

        Args:
            content: APIからのレスポンステキスト
            file_name: ファイル名

        Returns:
            判定結果の辞書
        """
        try:
            # JSONブロックを抽出
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                # JSONブロックがない場合、全体をJSONとして解釈
                json_str = content.strip()

            result = json.loads(json_str)

            # ファイル名を上書き（正確性のため）
            result["file_name"] = file_name

            return result

        except json.JSONDecodeError:
            # JSONパースに失敗した場合、テキストから情報を抽出
            return self._create_fallback_result(content, file_name)

    def _create_fallback_result(self, content: str, file_name: str) -> Dict[str, Any]:
        """JSONパース失敗時のフォールバック結果を作成"""
        # 判定を推測
        judgment = "要確認"
        if "問題なし" in content:
            judgment = "問題なし"
        elif "問題あり" in content or "禁止" in content or "不合格" in content:
            judgment = "問題あり"

        return {
            "file_name": file_name,
            "company_name": "不明",
            "judgment": judgment,
            "issues": [
                {
                    "severity": "info",
                    "category": "パースエラー",
                    "description": "JSON形式での解析に失敗しました。以下の生テキストを確認してください。"
                }
            ],
            "detected_elements": {
                "year": None,
                "issuer": None,
                "ranking_name": None,
                "position": None,
                "trademark_symbol": False
            },
            "notes": content,
            "raw_response": content
        }

    def check_multiple_images(
        self,
        images: List[tuple],
        file_name: str
    ) -> List[Dict[str, Any]]:
        """複数画像（PDFの各ページなど）をチェック

        Args:
            images: (base64_image, media_type) のタプルのリスト
            file_name: 元のファイル名

        Returns:
            各ページの判定結果リスト
        """
        results = []

        for i, (base64_image, media_type) in enumerate(images):
            result = self.check_image(
                base64_image=base64_image,
                media_type=media_type,
                file_name=file_name,
                page_num=i if len(images) > 1 else None
            )
            results.append(result)

        return results
