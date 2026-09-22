"use client";

import { calculateDiscountAmount, calculateSubtotal } from "@/lib/posCalc";
import { PurchaseItem } from "@/types/pos";

interface Props {
  items: PurchaseItem[];
  selectedLineId: string | null;
  onSelect: (lineId: string) => void;
  onChangeQuantity: (lineId: string, quantity: number) => void;
  onDelete: (lineId: string) => void;
  quantityError: string | null;
}

/** 購入品目リスト（設計仕様書4.2.2節 No.9〜13、F-04）。 */
export default function PurchaseList({ items, selectedLineId, onSelect, onChangeQuantity, onDelete, quantityError }: Props) {
  return (
    <div>
      <h3>購入品目リスト</h3>
      {quantityError && <div className="error-banner">{quantityError}</div>}
      <table>
        <thead>
          <tr>
            <th>商品名</th>
            <th>単価</th>
            <th>数量</th>
            <th>値引き</th>
            <th>小計</th>
          </tr>
        </thead>
        <tbody>
          {items.length === 0 && (
            <tr>
              <td colSpan={5} style={{ textAlign: "center", color: "#888" }}>
                購入リストは空です
              </td>
            </tr>
          )}
          {items.map((item) => {
            const selected = item.lineId === selectedLineId;
            const discountAmount = calculateDiscountAmount(item);
            return (
              <tr key={item.lineId} className={selected ? "selected-row" : ""} onClick={() => onSelect(item.lineId)} style={{ cursor: "pointer" }}>
                <td>{item.productName}</td>
                <td>¥{item.unitPrice.toLocaleString()}</td>
                <td>
                  {selected ? (
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onChangeQuantity(item.lineId, item.quantity - 1);
                        }}
                      >
                        -
                      </button>
                      <span>{item.quantity}</span>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onChangeQuantity(item.lineId, item.quantity + 1);
                        }}
                      >
                        +
                      </button>
                    </div>
                  ) : (
                    item.quantity
                  )}
                </td>
                <td>{discountAmount > 0 ? `-¥${discountAmount.toLocaleString()}` : "-"}</td>
                <td>¥{calculateSubtotal(item).toLocaleString()}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <button type="button" className="danger" disabled={!selectedLineId} onClick={() => selectedLineId && onDelete(selectedLineId)}>
        選択商品を削除
      </button>
    </div>
  );
}
