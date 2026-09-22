import { calculateDiscountAmount, calculateListSubtotal, calculateSubtotal } from "@/lib/posCalc";
import { PurchaseItem } from "@/types/pos";

function item(overrides: Partial<PurchaseItem> = {}): PurchaseItem {
  return {
    lineId: "line-1",
    productCode: "4901301234567",
    productName: "テスト商品",
    unitPrice: 1000,
    taxCategory: "standard",
    quantity: 1,
    discount: null,
    ...overrides,
  };
}

describe("calculateDiscountAmount（フロントエンド側プレビュー計算、UT-BE-CALC相当の踏襲）", () => {
  test("UT-FE-CALC-001 rate 10% quantity 1 -> 100", () => {
    const it = item({ discount: { discount_id: 1, discount_type: "rate", discount_value: 10 } });
    expect(calculateDiscountAmount(it)).toBe(100);
  });

  test("UT-FE-CALC-002 rate quantity 99 -> 9900", () => {
    const it = item({ quantity: 99, discount: { discount_id: 1, discount_type: "rate", discount_value: 10 } });
    expect(calculateDiscountAmount(it)).toBe(9900);
  });

  test("UT-FE-CALC-003 amount discount per unit x quantity", () => {
    const it = item({ quantity: 99, discount: { discount_id: 1, discount_type: "amount", discount_value: 999 } });
    expect(calculateDiscountAmount(it)).toBe(98901);
  });

  test("no discount -> 0", () => {
    expect(calculateDiscountAmount(item())).toBe(0);
  });
});

describe("UT-FE-CART-010相当: calculateListSubtotal（複数行の合計再計算）", () => {
  test("値引きなし1行＋値引きあり2行の合計", () => {
    const items: PurchaseItem[] = [
      item({ lineId: "a", unitPrice: 1000, quantity: 1 }),
      item({ lineId: "b", unitPrice: 1000, quantity: 1, discount: { discount_id: 1, discount_type: "rate", discount_value: 10 } }),
      item({ lineId: "c", unitPrice: 500, quantity: 2, discount: { discount_id: 2, discount_type: "amount", discount_value: 50 } }),
    ];
    // a: 1000, b: 900, c: 1000-100=900 => 合計2800
    expect(calculateListSubtotal(items)).toBe(2800);
  });

  test("空リストは0", () => {
    expect(calculateListSubtotal([])).toBe(0);
  });
});

describe("UT-FE-CART-008相当: 行削除後の合計再計算（配列操作そのものはコンポーネント側のためsubtotal計算のみ検証）", () => {
  test("該当行を除いた配列のsubtotalが正しく再計算される", () => {
    const items: PurchaseItem[] = [item({ lineId: "a" }), item({ lineId: "b", unitPrice: 500 })];
    const afterDelete = items.filter((i) => i.lineId !== "a");
    expect(calculateListSubtotal(afterDelete)).toBe(500);
  });
});

test("calculateSubtotal: 単価×数量-値引き額", () => {
  const it = item({ unitPrice: 1000, quantity: 3, discount: { discount_id: 1, discount_type: "amount", discount_value: 100 } });
  expect(calculateSubtotal(it)).toBe(1000 * 3 - 100 * 3);
});
