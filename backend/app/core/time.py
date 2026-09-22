"""DB（MySQL DATETIME、タイムゾーン情報を持たない）とアプリ内部（UTC aware）の時刻変換を一元化する。

Phase5コードレビュー指摘：`datetime.now(timezone.utc)` と `.replace(tzinfo=...)` の
変換処理が複数ファイルに散在していたため、本モジュールに集約する。
"""
from datetime import datetime, timezone


def now_utc() -> datetime:
    """現在時刻をtimezone-aware（UTC）で取得する。アプリ内部の比較・演算はすべてこちらを使う。"""
    return datetime.now(timezone.utc)


def to_db(dt: datetime) -> datetime:
    """DB格納用にtimezone情報を落とす（DB側はUTCのnaive datetimeとして保持する前提）。"""
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def from_db(dt: datetime) -> datetime:
    """DBから読み出したnaive datetime（UTC想定）にtimezone情報を付与する。"""
    return dt.replace(tzinfo=timezone.utc)
