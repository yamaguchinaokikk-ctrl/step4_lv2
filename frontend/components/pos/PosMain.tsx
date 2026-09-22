"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { calculateDiscountAmount, calculateListSubtotal } from "@/lib/posCalc";
import { ApiErrorBody, MemberInfo, ProductLookupResult, PurchaseItem, TaxCategory } from "@/types/pos";

import BarcodeScanner from "./BarcodeScanner";
import ConfirmModal from "./ConfirmModal";
import PurchaseList from "./PurchaseList";

const IDLE_TIMEOUT_MS = 10 * 60 * 1000; // 7.4.1節：アイドルタイムアウト10分（[AI提案]の暫定値）

async function lookupProduct(code: string): Promise<{ ok: true; data: ProductLookupResult } | { ok: false; message: string }> {
  const res = await fetch(`/api/products/${encodeURIComponent(code)}`);
  if (res.ok) return { ok: true, data: await res.json() };
  const body: ApiErrorBody = await res.json().catch(() => null as unknown as ApiErrorBody);
  return { ok: false, message: body?.error?.message || "商品情報の取得に失敗しました" };
}

export default function PosMain({ staffId, staffName }: { staffId: string; staffName: string | null }) {
  const [items, setItems] = useState<PurchaseItem[]>([]);
  const [selectedLineId, setSelectedLineId] = useState<string | null>(null);

  const [memberIdInput, setMemberIdInput] = useState("");
  const [memberInfo, setMemberInfo] = useState<MemberInfo | null>(null);

  const [manualCode, setManualCode] = useState("");
  const [manualPreview, setManualPreview] = useState<ProductLookupResult | null>(null);

  const [error, setError] = useState<string | null>(null);
  const [quantityError, setQuantityError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [confirmResult, setConfirmResult] = useState<{ incl: number; excl: number } | null>(null);
  const [locked, setLocked] = useState(false);

  const idleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const resetIdleTimer = useCallback(() => {
    if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
    idleTimerRef.current = setTimeout(() => setLocked(true), IDLE_TIMEOUT_MS);
  }, []);

  useEffect(() => {
    resetIdleTimer();
    const events = ["click", "keydown", "mousemove"];
    const handler = () => resetIdleTimer();
    events.forEach((ev) => window.addEventListener(ev, handler));
    return () => {
      events.forEach((ev) => window.removeEventListener(ev, handler));
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
    };
  }, [resetIdleTimer]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 1500);
    return () => clearTimeout(t);
  }, [toast]);

  const addOrIncrementItem = useCallback(
    (product: ProductLookupResult) => {
      setError(null);
      setQuantityError(null);
      setItems((prev) => {
        const existingIndex = prev.findIndex((i) => i.productCode === product.product_code);
        if (existingIndex >= 0) {
          const existing = prev[existingIndex];
          if (existing.quantity >= 99) {
            setQuantityError("数量の上限（99個）に達しています");
            return prev;
          }
          const next = [...prev];
          next[existingIndex] = { ...existing, quantity: existing.quantity + 1 };
          return next;
        }
        // ISS-006：会員ID入力前にスキャンした商品への値引き遡及適用は行わない。追加時点の会員ID状態のみで判定する。
        const discountApplicable = memberInfo !== null && product.applicable_discount !== null;
        const newItem: PurchaseItem = {
          lineId: `${product.product_code}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
          productCode: product.product_code,
          productName: product.product_name,
          unitPrice: product.unit_price,
          taxCategory: product.tax_category,
          quantity: 1,
          discount: discountApplicable ? product.applicable_discount : null,
        };
        return [...prev, newItem];
      });
      setToast("1件追加されました");
    },
    [memberInfo],
  );

  const handleScanDetected = useCallback(
    async (code: string) => {
      const result = await lookupProduct(code);
      if (!result.ok) {
        setError(result.message);
        return;
      }
      addOrIncrementItem(result.data);
    },
    [addOrIncrementItem],
  );

  const handleManualLookup = async () => {
    if (!manualCode) return;
    setError(null);
    const result = await lookupProduct(manualCode);
    if (!result.ok) {
      setError(result.message);
      setManualPreview(null);
      return;
    }
    setManualPreview(result.data);
  };

  const handleManualAdd = () => {
    if (!manualPreview) return;
    addOrIncrementItem(manualPreview);
    setManualPreview(null);
    setManualCode("");
  };

  const handleMemberLookup = async () => {
    if (!memberIdInput) return;
    setError(null);
    const res = await fetch(`/api/members/${encodeURIComponent(memberIdInput)}`);
    if (!res.ok) {
      const body: ApiErrorBody = await res.json().catch(() => null as unknown as ApiErrorBody);
      setError(body?.error?.message || "会員IDが見つかりません");
      return;
    }
    const data: MemberInfo = await res.json();
    setMemberInfo(data);
    setMemberIdInput("");
  };

  const handleChangeQuantity = (lineId: string, quantity: number) => {
    setQuantityError(null);
    if (quantity > 99) {
      setQuantityError("数量の上限（99個）に達しています");
      return;
    }
    if (quantity < 1) return;
    setItems((prev) => prev.map((i) => (i.lineId === lineId ? { ...i, quantity } : i)));
  };

  const handleDelete = (lineId: string) => {
    setItems((prev) => prev.filter((i) => i.lineId !== lineId));
    if (selectedLineId === lineId) setSelectedLineId(null);
  };

  const resetTransactionState = () => {
    setItems([]);
    setSelectedLineId(null);
    setMemberInfo(null);
    setMemberIdInput("");
    setManualCode("");
    setManualPreview(null);
  };

  const handleConfirmPurchase = async () => {
    if (items.length === 0) return;
    setError(null);
    setConfirming(true);
    try {
      const clientSubtotal = calculateListSubtotal(items);

      const categories = Array.from(new Set(items.map((i) => i.taxCategory)));
      const rates: Record<TaxCategory, number> = { standard: 0, reduced: 0 };
      for (const category of categories) {
        const r = await fetch(`/api/tax-rates/current?tax_category=${category}`);
        if (r.ok) {
          const data = await r.json();
          rates[category] = data.rate;
        }
      }

      let clientTotalInclTax = 0;
      for (const category of categories) {
        const excl = items.filter((i) => i.taxCategory === category).reduce((sum, i) => sum + (i.unitPrice * i.quantity - calculateDiscountAmount(i)), 0);
        clientTotalInclTax += excl + Math.round(excl * rates[category]);
      }

      const res = await fetch("/api/transactions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          idempotency_key: crypto.randomUUID(),
          member_id: memberInfo?.member_id ?? null,
          items: items.map((i) => ({
            product_code: i.productCode,
            quantity: i.quantity,
            client_unit_price: i.unitPrice,
            client_discount_amount: calculateDiscountAmount(i),
          })),
          client_subtotal: clientSubtotal,
          client_total_incl_tax: clientTotalInclTax,
          client_total_excl_tax: clientSubtotal,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data?.error?.message || "購入確定に失敗しました");
        return;
      }
      setConfirmResult({ incl: data.total_amount_incl_tax, excl: data.total_amount_excl_tax });
    } catch {
      setError("一時的なエラーが発生しました。しばらくしてから再度お試しください。");
    } finally {
      setConfirming(false);
    }
  };

  const handleLogout = async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    window.location.href = "/login";
  };

  return (
    <div className="page">
      <div className="topbar">
        <div>
          担当者：{staffName || staffId}
          {memberInfo && <span style={{ marginLeft: 16 }}>会員：{memberInfo.member_name}（{memberInfo.member_id}）</span>}
        </div>
        <button type="button" className="secondary" onClick={handleLogout}>
          ログアウト
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="card">
        <h3>会員ID読み込み</h3>
        <div className="row">
          <input placeholder="会員ID" value={memberIdInput} onChange={(e) => setMemberIdInput(e.target.value)} minLength={4} maxLength={12} />
          <button type="button" onClick={handleMemberLookup} style={{ flex: "0 0 auto" }}>
            お客様ID読み込み
          </button>
        </div>
      </div>

      <div className="card">
        <h3>商品登録</h3>
        <BarcodeScanner onDetected={handleScanDetected} />
        <div className="row">
          <input
            placeholder="商品コードを入力してEnter"
            value={manualCode}
            onChange={(e) => setManualCode(e.target.value)}
            minLength={8}
            maxLength={13}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handleManualLookup();
              }
            }}
          />
        </div>
        {manualPreview && (
          <div className="row" style={{ alignItems: "center" }}>
            <div>名称：{manualPreview.product_name}</div>
            <div>単価：¥{manualPreview.unit_price.toLocaleString()}</div>
            <button type="button" onClick={handleManualAdd} style={{ flex: "0 0 auto" }}>
              追加
            </button>
          </div>
        )}
      </div>

      <div className="card">
        <PurchaseList
          items={items}
          selectedLineId={selectedLineId}
          onSelect={setSelectedLineId}
          onChangeQuantity={handleChangeQuantity}
          onDelete={handleDelete}
          quantityError={quantityError}
        />
      </div>

      <div className="card">
        <p style={{ fontSize: 18 }}>小計（税抜・値引後）：¥{calculateListSubtotal(items).toLocaleString()}</p>
        <button type="button" disabled={items.length === 0 || confirming} onClick={handleConfirmPurchase} style={{ width: "100%", padding: "12px", fontSize: 16 }}>
          {confirming ? "処理中..." : "購入確定"}
        </button>
      </div>

      {confirmResult && (
        <ConfirmModal
          totalInclTax={confirmResult.incl}
          totalExclTax={confirmResult.excl}
          onClose={() => {
            setConfirmResult(null);
            resetTransactionState();
          }}
        />
      )}

      {toast && <div className="toast">{toast}</div>}

      {locked && (
        <div className="modal-backdrop">
          <div className="modal" style={{ textAlign: "center" }}>
            <h2>離席中のためロックしています</h2>
            <p>操作を再開するにはボタンを押してください（ログインセッション自体は維持されています）。</p>
            <button
              type="button"
              onClick={() => {
                setLocked(false);
                resetIdleTimer();
              }}
            >
              操作を再開する
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
