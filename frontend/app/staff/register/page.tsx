"use client";

import Link from "next/link";
import { useState } from "react";

/** SC-03 担当者登録画面（簡易）（設計仕様書4.2.3節、[AI提案]）。 */
export default function StaffRegisterPage() {
  const [staffId, setStaffId] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSubmitting(true);
    try {
      const res = await fetch("/api/staff", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ staff_id: staffId, password, name }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data?.error?.message || "登録に失敗しました");
        return;
      }
      setSuccess(`担当者「${data.staff_name}」（${data.staff_id}）を登録しました`);
      setStaffId("");
      setPassword("");
      setName("");
    } catch {
      setError("一時的なエラーが発生しました。しばらくしてから再度お試しください。");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page" style={{ maxWidth: 400, marginTop: 60 }}>
      <div className="card">
        <h1>担当者登録（簡易）</h1>
        {error && <div className="error-banner">{error}</div>}
        {success && <div className="error-banner" style={{ background: "#dcfce7", borderColor: "#86efac", color: "#166534" }}>{success}</div>}
        <form onSubmit={handleSubmit}>
          <label htmlFor="staffId">担当者ID（4〜12文字）</label>
          <input id="staffId" value={staffId} onChange={(e) => setStaffId(e.target.value)} minLength={4} maxLength={12} required />
          <label htmlFor="password">パスワード（8〜16文字・英数字両方含む）</label>
          <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} maxLength={16} required />
          <label htmlFor="name">氏名</label>
          <input id="name" value={name} onChange={(e) => setName(e.target.value)} required />
          <button type="submit" disabled={submitting} style={{ width: "100%" }}>
            {submitting ? "登録中..." : "登録"}
          </button>
        </form>
        <p style={{ marginTop: 16 }}>
          <Link href="/login">ログイン画面へ戻る</Link>
        </p>
      </div>
    </div>
  );
}
