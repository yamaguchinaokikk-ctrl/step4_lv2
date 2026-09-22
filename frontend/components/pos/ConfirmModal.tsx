"use client";

interface Props {
  totalInclTax: number;
  totalExclTax: number;
  onClose: () => void;
}

/** 購入確定後のポップアップ（設計仕様書4.2.2節 No.16、FR-017）。税込・税抜合計金額を両方提示する。 */
export default function ConfirmModal({ totalInclTax, totalExclTax, onClose }: Props) {
  return (
    <div className="modal-backdrop">
      <div className="modal" style={{ textAlign: "center", minWidth: 280 }}>
        <h2>購入確定</h2>
        <p style={{ fontSize: 20, margin: "16px 0 4px" }}>合計（税込）：¥{totalInclTax.toLocaleString()}</p>
        <p style={{ fontSize: 15, color: "#555", margin: "0 0 20px" }}>合計（税抜）：¥{totalExclTax.toLocaleString()}</p>
        <button type="button" onClick={onClose} style={{ width: "100%" }}>
          次の取引へ
        </button>
      </div>
    </div>
  );
}
