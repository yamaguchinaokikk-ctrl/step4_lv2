"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

interface DiscountRow {
  discount_id: number;
  product_code: string;
  discount_type: "rate" | "amount";
  discount_value: number;
  start_date: string;
  end_date: string;
}

interface TaxRateRow {
  tax_rate_id: number;
  rate: number;
  tax_category: "standard" | "reduced";
  effective_from: string;
}

/** SC-04 値引き・税率管理画面（設計仕様書4.2.4節、管理者ロール限定）。 */
export default function AdminDiscounts() {
  const [discounts, setDiscounts] = useState<DiscountRow[]>([]);
  const [taxRates, setTaxRates] = useState<TaxRateRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [productCode, setProductCode] = useState("");
  const [discountType, setDiscountType] = useState<"rate" | "amount">("rate");
  const [discountValue, setDiscountValue] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const [rate, setRate] = useState("");
  const [taxCategory, setTaxCategory] = useState<"standard" | "reduced">("standard");
  const [effectiveFrom, setEffectiveFrom] = useState("");

  const loadDiscounts = async () => {
    const res = await fetch("/api/discounts");
    if (res.ok) setDiscounts((await res.json()).discounts);
  };
  const loadTaxRates = async () => {
    const res = await fetch("/api/tax-rates");
    if (res.ok) setTaxRates((await res.json()).tax_rates);
  };

  useEffect(() => {
    loadDiscounts();
    loadTaxRates();
  }, []);

  const handleCreateDiscount = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const res = await fetch("/api/discounts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_code: productCode,
        discount_type: discountType,
        discount_value: Number(discountValue),
        start_date: startDate,
        end_date: endDate,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      setError(data?.error?.message || "値引きの登録に失敗しました");
      return;
    }
    setProductCode("");
    setDiscountValue("");
    setStartDate("");
    setEndDate("");
    loadDiscounts();
  };

  const handleCreateTaxRate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const res = await fetch("/api/tax-rates", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        rate: Number(rate),
        tax_category: taxCategory,
        effective_from: effectiveFrom,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      setError(data?.error?.message || "消費税率の登録に失敗しました");
      return;
    }
    setRate("");
    setEffectiveFrom("");
    loadTaxRates();
  };

  return (
    <div className="page">
      <div className="topbar">
        <h1>値引き・税率管理（管理者限定）</h1>
        <Link href="/pos">POS画面へ戻る</Link>
      </div>
      {error && <div className="error-banner">{error}</div>}

      <div className="card">
        <h2>値引き一覧</h2>
        <table>
          <thead>
            <tr>
              <th>商品コード</th>
              <th>種別</th>
              <th>値</th>
              <th>開始日</th>
              <th>終了日</th>
            </tr>
          </thead>
          <tbody>
            {discounts.map((d) => (
              <tr key={d.discount_id}>
                <td>{d.product_code}</td>
                <td>{d.discount_type}</td>
                <td>{d.discount_value}</td>
                <td>{d.start_date}</td>
                <td>{d.end_date}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <form onSubmit={handleCreateDiscount}>
          <div className="row">
            <div>
              <label htmlFor="discount-product-code">商品コード</label>
              <input id="discount-product-code" value={productCode} onChange={(e) => setProductCode(e.target.value)} minLength={8} maxLength={13} required />
            </div>
            <div>
              <label htmlFor="discount-type">種別</label>
              <select id="discount-type" value={discountType} onChange={(e) => setDiscountType(e.target.value as "rate" | "amount")}>
                <option value="rate">rate（割合%）</option>
                <option value="amount">amount（金額円/個）</option>
              </select>
            </div>
            <div>
              <label htmlFor="discount-value">値</label>
              <input id="discount-value" type="number" value={discountValue} onChange={(e) => setDiscountValue(e.target.value)} required />
            </div>
            <div>
              <label htmlFor="discount-start-date">開始日</label>
              <input id="discount-start-date" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} required />
            </div>
            <div>
              <label htmlFor="discount-end-date">終了日</label>
              <input id="discount-end-date" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} required />
            </div>
          </div>
          <button type="submit">値引きを登録</button>
        </form>
      </div>

      <div className="card">
        <h2>消費税率一覧</h2>
        <table>
          <thead>
            <tr>
              <th>税率</th>
              <th>税区分</th>
              <th>適用開始日</th>
            </tr>
          </thead>
          <tbody>
            {taxRates.map((t) => (
              <tr key={t.tax_rate_id}>
                <td>{(t.rate * 100).toFixed(2)}%</td>
                <td>{t.tax_category}</td>
                <td>{t.effective_from}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <form onSubmit={handleCreateTaxRate}>
          <div className="row">
            <div>
              <label htmlFor="tax-rate-value">税率（0〜0.20、例：0.10）</label>
              <input id="tax-rate-value" type="number" step="0.0001" min={0} max={0.2} value={rate} onChange={(e) => setRate(e.target.value)} required />
            </div>
            <div>
              <label htmlFor="tax-rate-category">税区分</label>
              <select id="tax-rate-category" value={taxCategory} onChange={(e) => setTaxCategory(e.target.value as "standard" | "reduced")}>
                <option value="standard">standard（標準）</option>
                <option value="reduced">reduced（軽減）</option>
              </select>
            </div>
            <div>
              <label htmlFor="tax-rate-effective-from">適用開始日</label>
              <input id="tax-rate-effective-from" type="date" value={effectiveFrom} onChange={(e) => setEffectiveFrom(e.target.value)} required />
            </div>
          </div>
          <button type="submit">消費税率を登録</button>
        </form>
      </div>
    </div>
  );
}
