export type TaxCategory = "standard" | "reduced";
export type DiscountType = "rate" | "amount";

export interface ApplicableDiscount {
  discount_id: number;
  discount_type: DiscountType;
  discount_value: number;
}

export interface ProductLookupResult {
  product_code: string;
  product_name: string;
  unit_price: number;
  tax_category: TaxCategory;
  applicable_discount: ApplicableDiscount | null;
}

/** 購入リストの1行（DR-002相当、フロントエンド状態管理のみでDBテーブルを持たない、D-ISS-02）。 */
export interface PurchaseItem {
  lineId: string;
  productCode: string;
  productName: string;
  unitPrice: number;
  taxCategory: TaxCategory;
  quantity: number;
  discount: ApplicableDiscount | null;
}

export interface MemberInfo {
  member_id: string;
  member_name: string;
}

export interface ApiErrorBody {
  error: {
    type: "validation_error" | "business_error" | "system_error";
    code: string;
    message: string;
    details?: unknown;
  };
}
