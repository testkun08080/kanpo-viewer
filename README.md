# 官報ビューワー（バックエンド）

官報PDF取得API - 官報文書のPDFをダウンロードできるAPIサーバーです。

## 📁 プロジェクト構成

```
kanpo-viewer/
├── api/                          # FastAPI アプリケーション
│   ├── app/
│   │   ├── main.py              # メインアプリケーション
│   │   ├── core/                # 設定とセキュリティ
│   │   │   ├── config.py        # 環境設定
│   │   │   └── security.py      # セキュリティ機能
│   │   ├── api/                 # APIエンドポイント
│   │   │   └── pdf.py           # PDF関連API
│   │   ├── schemas/             # データスキーマ
│   │   │   └── pdf.py           # PDFスキーマ定義
│   │   ├── services/            # ビジネスロジック
│   │   │   └── simple_pdf_service.py  # PDF処理サービス
│   │   ├── models/              # データベースモデル
│   │   └── utils/               # 共通ユーティリティ
│   └── tests/                   # テストファイル
│       ├── unit/                # ユニットテスト
│       ├── integration/         # 統合テスト
│       └── fixtures/            # テスト用データ
├── requirements.txt             # 本番依存関係
├── requirements_test.txt        # テスト依存関係
├── pytest.ini                  # Pytestの設定
└── vercel.json                  # Vercelデプロイ設定
```

## ⚙️ 技術スタック

- **フレームワーク**: FastAPI (Python)
- **非同期処理**: aiohttp
- **設定管理**: Pydantic Settings
- **テスト**: pytest
- **デプロイ**: Vercel
- **ファイル処理**: aiofiles

## 🚀 セットアップ手順

1. **ローカルへクローンする**
    ```bash
    git clone https://github.com/testkun08080/kanpo-viewer.git
   ```

2. **仮想環境の構築**
    ```bash
    cd kanpo-viewer
    uv venv -p 3.12
    uv pip install -r requirements.txt
   ```
   
3. **起動**
    ```bash
    uv run -m api.app.main
   ```

## 🧪 Pytestを使ったテスト

1. **テスト用にモジュールをインストール**
    ```bash
    uv pip install -r requirements_test.txt
   ```
1. **Pytest実行**
    ```bash
    uv run pytest --html=report.html --self-contained-html --log-level=INFO
   ```


## 📡 API エンドポイント

### 基本情報
- **ベースURL**: `/api` (本番環境)
- **ドキュメント**: `/docs` (開発環境のみ)


## 🚀 デプロイメント

1. **ローカルでテスト**
    ```bash
    vercel dev
   ```

2. **vercelへデプロイ（プレビューとして）**
    ```bash
    vercel
   ```

3. **、vercelへデプロイ（プロダクトとして）**
    ```bash
    vercel --prod
   ```
