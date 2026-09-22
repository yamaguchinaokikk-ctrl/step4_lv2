"""テストデータ設計書（テスト仕様書/05_テストデータ設計書.md）準拠のシードスクリプト。

実行方法: backend/ ディレクトリで `python -m seed.seed_data`
"""
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.discount import Discount
from app.models.member import Member
from app.models.product import Product
from app.models.staff import Staff
from app.models.tax_rate import TaxRate


def seed():
    db = SessionLocal()
    try:
        # TD-PRODUCT: 商品マスタ
        products = [
            Product(product_code="4901301234567", product_name="標準税率の通常商品（13桁）", unit_price=1000, tax_category="standard"),
            Product(product_code="49012345", product_name="標準税率の通常商品（8桁）", unit_price=500, tax_category="standard"),
            Product(product_code="4902345678901", product_name="軽減税率対象商品（飲料食品）", unit_price=300, tax_category="reduced"),
            Product(product_code="4903456789012", product_name="値引き対象商品", unit_price=1000, tax_category="standard"),
            Product(product_code="4904567890123", product_name="端数計算確認用商品", unit_price=333, tax_category="standard"),
        ]
        for p in products:
            if db.get(Product, p.product_code) is None:
                db.add(p)
        db.commit()

        # TD-MEMBER: 会員マスタ
        members = [
            Member(member_id="M001", name="テスト太郎", phone_number="090-1111-1111", address="東京都千代田区1-1-1", gender="male", age=35),
            Member(member_id="M00000001234", name="テスト花子", phone_number="090-2222-2222", address="大阪府大阪市2-2-2", gender="female", age=28),
        ]
        for m in members:
            if db.get(Member, m.member_id) is None:
                db.add(m)
        db.commit()

        # TD-TAX: 消費税率マスタ
        tax_rates = [
            TaxRate(tax_category="standard", rate="0.08", effective_from=date(2019, 9, 30)),
            TaxRate(tax_category="standard", rate="0.10", effective_from=date(2019, 10, 1)),
            TaxRate(tax_category="reduced", rate="0.08", effective_from=date(2019, 10, 1)),
        ]
        for t in tax_rates:
            exists = (
                db.query(TaxRate)
                .filter(TaxRate.tax_category == t.tax_category, TaxRate.effective_from == t.effective_from)
                .first()
            )
            if exists is None:
                db.add(t)
        db.commit()

        # TD-DISCOUNT: 値引きマスタ（テスト基準日2026-06-15を含む期間で登録）
        discounts = [
            Discount(product_code="4903456789012", discount_type="rate", discount_value="10.00", start_date=date(2026, 6, 1), end_date=date(2026, 6, 30)),
            Discount(product_code="4901301234567", discount_type="amount", discount_value="100.00", start_date=date(2026, 6, 1), end_date=date(2026, 6, 30)),
        ]
        for d in discounts:
            exists = db.query(Discount).filter(Discount.product_code == d.product_code, Discount.start_date == d.start_date).first()
            if exists is None:
                db.add(d)
        db.commit()

        # TD-STAFF: レジ担当者マスタ
        now = datetime.utcnow()
        staff_list = [
            Staff(staff_id="stf1", password_hash=hash_password("Passw0rd"), name="山田一般", role="staff", failed_login_count=0, locked_until=None),
            Staff(staff_id="admin0012345", password_hash=hash_password("AdminPass99"), name="佐藤管理", role="admin", failed_login_count=0, locked_until=None),
            Staff(staff_id="stf2", password_hash=hash_password("Passw0rd"), name="鈴木テスト", role="staff", failed_login_count=4, locked_until=None),
            Staff(staff_id="stf3", password_hash=hash_password("Passw0rd"), name="高橋テスト", role="staff", failed_login_count=5, locked_until=now + timedelta(minutes=15)),
            Staff(staff_id="stf4", password_hash=hash_password("Passw0rd"), name="田中テスト", role="staff", failed_login_count=5, locked_until=now - timedelta(minutes=1)),
        ]
        for s in staff_list:
            if db.get(Staff, s.staff_id) is None:
                db.add(s)
        db.commit()

        print("Seed data inserted.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
