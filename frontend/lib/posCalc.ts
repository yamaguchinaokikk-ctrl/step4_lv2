import { PurchaseItem } from "@/types/pos";

/** 設計仕様書5.3節 Discount.calculateAmount() と同一のロジック（表示用プレビュー。確定額はサーバー側で再計算される）。 */
export function calculateDiscountAmount(item: PurchaseItem): number {
  if (!item.discount) return 0;
  if (item.discount.discount_type === "amount") {
    return item.discount.discount_value * item.quantity;
  }
  return Math.round(item.unitPrice * item.quantity * (item.discount.discount_value / 100));
}

export function calculateSubtotal(item: PurchaseItem): number {
  return item.unitPrice * item.quantity - calculateDiscountAmount(item);
}

export function calculateListSubtotal(items: PurchaseItem[]): number {
  return items.reduce((sum, item) => sum + calculateSubtotal(item), 0);
}
