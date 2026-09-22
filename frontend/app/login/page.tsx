"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

/** SC-01 ログイン画面（設計仕様書4.2.1節）。 */
export default function LoginPage() {
  const router = useRouter();
  const [staffId, setStaffId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ staff_id: staffId, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data?.error?.message || "ログインに失敗しました");
        return;
      }
      router.push("/pos");
      router.refresh();
    } catch {
      setError("一時的なエラーが発生しました。しばらくしてから再度お試しください。");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page" style={{ maxWidth: 360, marginTop: 80 }}>
      <div className="card">
        <h1 style={{ textAlign: "center" }}>ログイン</h1>
        {error && <div className="error-banner">{error}</div>}
        <form onSubmit={handleSubmit}>
          <label htmlFor="staffId">担当者ID</label>
          <input
            id="staffId"
            value={staffId}
            onChange={(e) => setStaffId(e.target.value)}
            minLength={4}
            maxLength={12}
            required
          />
          <label htmlFor="password">パスワード</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            maxLength={16}
            required
          />
          <button type="submit" disabled={submitting} style={{ width: "100%" }}>
            {submitting ? "ログイン中..." : "ログイン"}
          </button>
        </form>
      </div>
    </div>
  );
}
