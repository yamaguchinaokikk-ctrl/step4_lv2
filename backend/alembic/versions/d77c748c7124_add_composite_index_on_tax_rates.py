"""add composite index on tax_rates(tax_category, effective_from)

Phase5コードレビュー指摘：「現在有効な税率」選定クエリ（tax_category絞り込み＋effective_from降順）を
高速化する複合インデックスが、Phase2計画時点の想定に反して未実装だった。

手書きの理由：`alembic revision --autogenerate`は、モデルの`__tablename__`を大文字→小文字に
是正した際、SQLAlchemyが自動生成するインデックス名（テーブル名を含む）も追随して変化するため、
tax_rates以外の全テーブルの既存インデックスまで「リネーム対象」として検出してしまった。
検証の結果、本サーバー（MySQL 8.4、lower_case_table_names=1）はインデックス名の重複判定が
大文字小文字を区別しないため、同名を大文字/小文字違いで新規作成できず（名前の実体は同一と
みなされる）、機械的な「先に作成→後で削除」も成立しなかった。インデックス名の大文字/小文字は
機能に影響しないため、既存インデックスのリネームは行わず、本来の目的である複合インデックスの
追加のみを行う。

Revision ID: d77c748c7124
Revises: 37836aab4070
Create Date: 2026-09-23 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "d77c748c7124"
down_revision: Union[str, None] = "37836aab4070"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_tax_rates_category_effective_from",
        "tax_rates",
        ["tax_category", "effective_from"],
        unique=False,
    )
    # tax_categoryのみの単一列インデックスは複合インデックスの先頭列で代替できるため削除する。
    # tax_categoryはFK対象カラムではないため直接DROPしてよい。
    op.drop_index("ix_TAX_RATES_tax_category", table_name="tax_rates")


def downgrade() -> None:
    op.create_index("ix_TAX_RATES_tax_category", "tax_rates", ["tax_category"], unique=False)
    op.drop_index("ix_tax_rates_category_effective_from", table_name="tax_rates")
