"""
ファイル処理モジュール

PDF・画像ファイルを統一的に処理し、
OpenAI Vision APIに送信可能な形式に変換します。
"""

import base64
import io
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image

# PyMuPDF (PDFの画像変換用)
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("Warning: PyMuPDF not installed. PDF processing will be disabled.")


class FileProcessor:
    """ファイル処理エンジン

    対応フォーマット:
    - 画像: PNG, JPG, JPEG, GIF, WEBP, BMP
    - ドキュメント: PDF
    """

    SUPPORTED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
    SUPPORTED_DOC_EXTENSIONS = {'.pdf'}

    def __init__(self, pdf_dpi: int = 300, pdf_scale: float = 2.0):
        """初期化

        Args:
            pdf_dpi: PDF変換時のDPI
            pdf_scale: PDF変換時のスケール倍率
        """
        self.pdf_dpi = pdf_dpi
        self.pdf_scale = pdf_scale

    def is_supported(self, file_path: str) -> bool:
        """ファイルが対応形式かどうかを判定"""
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_IMAGE_EXTENSIONS or ext in self.SUPPORTED_DOC_EXTENSIONS

    def get_file_type(self, file_path: str) -> str:
        """ファイルタイプを取得"""
        ext = Path(file_path).suffix.lower()
        if ext in self.SUPPORTED_IMAGE_EXTENSIONS:
            return "image"
        elif ext in self.SUPPORTED_DOC_EXTENSIONS:
            return "pdf"
        else:
            return "unknown"

    def process_file(self, file_path: str) -> List[Tuple[str, str]]:
        """ファイルを処理してBase64エンコードされた画像リストを返す

        Args:
            file_path: ファイルパス

        Returns:
            List of (base64_image, media_type) tuples
        """
        file_type = self.get_file_type(file_path)

        if file_type == "image":
            return self._process_image(file_path)
        elif file_type == "pdf":
            return self._process_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")

    def process_uploaded_file(self, uploaded_file) -> List[Tuple[str, str]]:
        """Streamlitのアップロードファイルを処理

        Args:
            uploaded_file: StreamlitのUploadedFileオブジェクト

        Returns:
            List of (base64_image, media_type) tuples
        """
        file_name = uploaded_file.name
        file_bytes = uploaded_file.read()
        ext = Path(file_name).suffix.lower()

        if ext in self.SUPPORTED_IMAGE_EXTENSIONS:
            return self._process_image_bytes(file_bytes, ext)
        elif ext in self.SUPPORTED_DOC_EXTENSIONS:
            return self._process_pdf_bytes(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {file_name}")

    def _process_image(self, file_path: str) -> List[Tuple[str, str]]:
        """画像ファイルを処理"""
        with open(file_path, "rb") as f:
            image_bytes = f.read()

        ext = Path(file_path).suffix.lower()
        return self._process_image_bytes(image_bytes, ext)

    def _process_image_bytes(self, image_bytes: bytes, ext: str) -> List[Tuple[str, str]]:
        """画像バイトデータを処理"""
        # メディアタイプを決定
        media_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp'
        }
        media_type = media_type_map.get(ext, 'image/png')

        # Base64エンコード
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        return [(base64_image, media_type)]

    def _process_pdf(self, file_path: str) -> List[Tuple[str, str]]:
        """PDFファイルを処理"""
        if not PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF is not installed. Cannot process PDF files.")

        with open(file_path, "rb") as f:
            pdf_bytes = f.read()

        return self._process_pdf_bytes(pdf_bytes)

    def _process_pdf_bytes(self, pdf_bytes: bytes) -> List[Tuple[str, str]]:
        """PDFバイトデータを処理"""
        if not PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF is not installed. Cannot process PDF files.")

        results = []

        # PDFを開く
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]

                # 高解像度で画像に変換
                mat = fitz.Matrix(self.pdf_scale, self.pdf_scale)
                pix = page.get_pixmap(matrix=mat, alpha=False)

                # PNG形式でバイトデータに変換
                img_bytes = pix.tobytes("png")

                # Base64エンコード
                base64_image = base64.b64encode(img_bytes).decode('utf-8')

                results.append((base64_image, "image/png"))
        finally:
            doc.close()

        return results

    def get_pdf_page_count(self, file_path: str) -> int:
        """PDFのページ数を取得"""
        if not PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF is not installed.")

        doc = fitz.open(file_path)
        page_count = len(doc)
        doc.close()
        return page_count

    def get_pdf_page_count_from_bytes(self, pdf_bytes: bytes) -> int:
        """PDFバイトデータからページ数を取得"""
        if not PYMUPDF_AVAILABLE:
            raise RuntimeError("PyMuPDF is not installed.")

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = len(doc)
        doc.close()
        return page_count
