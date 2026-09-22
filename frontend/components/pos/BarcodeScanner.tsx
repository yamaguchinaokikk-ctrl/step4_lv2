"use client";

import { BrowserMultiFormatReader, IScannerControls } from "@zxing/browser";
import { useEffect, useRef, useState } from "react";

/**
 * バーコードスキャンエリア（カメラ）（設計仕様書4.2.2節 No.4、FR-001）。
 * getUserMediaを使用するためHTTPS（またはlocalhost）環境が必須。
 * 読み取り失敗時の挙動はISS-009未解決のため、ここでは「継続してスキャンを試みる」動作のみとする。
 */
export default function BarcodeScanner({ onDetected }: { onDetected: (code: string) => void }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const controlsRef = useRef<IScannerControls | null>(null);
  const [active, setActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      controlsRef.current?.stop();
    };
  }, []);

  const start = async () => {
    setCameraError(null);
    const reader = new BrowserMultiFormatReader();
    try {
      const controls = await reader.decodeFromVideoDevice(undefined, videoRef.current!, (result) => {
        if (result) {
          onDetected(result.getText());
        }
      });
      controlsRef.current = controls;
      setActive(true);
    } catch (e) {
      setCameraError("カメラを起動できませんでした。カメラへのアクセス許可をご確認ください。");
    }
  };

  const stop = () => {
    controlsRef.current?.stop();
    controlsRef.current = null;
    setActive(false);
  };

  return (
    <div style={{ marginBottom: 12 }}>
      {cameraError && <div className="error-banner">{cameraError}</div>}
      <video ref={videoRef} style={{ width: "100%", maxHeight: 220, background: "#000", display: active ? "block" : "none" }} muted />
      {!active ? (
        <button type="button" onClick={start}>
          バーコードスキャン開始
        </button>
      ) : (
        <button type="button" className="secondary" onClick={stop}>
          スキャン停止
        </button>
      )}
    </div>
  );
}
