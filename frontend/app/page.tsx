"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type PalmPoint = [number, number];
type UserHand = "left" | "right";
type CaptureSource = "camera" | "upload";

type SuggestedLine = {
  label: string;
  color: string;
  points: PalmPoint[];
};

const READING_LABELS: Record<string, string> = {
  heart_line: "ความรักและความสัมพันธ์",
  head_line: "ความคิดและการตัดสินใจ",
  life_line: "พลังชีวิตและจังหวะชีวิต",
  fate_line: "เส้นทางวาสนาและโอกาส",
};

type ScanResponse = {
  status: string;
  data: {
    user_hand: UserHand;
    processing: {
      mode: string;
      mediapipe_hand_enabled: boolean;
      hand_detected: boolean;
      handedness: string | null;
      error: string | null;
      landmarks: Array<{
        id: number;
        x: number;
        y: number;
        z: number;
      }>;
    };
    reading_engine: {
      name: string;
      image_hash: string;
      features: {
        brightness: number;
        contrast: number;
        edge_density: number;
        palm_spread: number;
        image_valid: boolean;
      };
    };
    image: {
      filename: string;
      content_type: string;
      size_bytes: number;
    };
    coordinate_space: {
      width: number;
      height: number;
    };
    suggested_lines: Record<string, SuggestedLine>;
    analysis: Record<
      string,
      {
        type_id: string;
        title: string;
        description: string;
      }
    >;
  };
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8089";

export default function Home() {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [selectedFileName, setSelectedFileName] = useState("palm-capture.jpg");
  const [captureSource, setCaptureSource] = useState<CaptureSource>("camera");
  const [userHand, setUserHand] = useState<UserHand>("right");
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);

  const attachCameraStream = useCallback(async () => {
    try {
      const activeStream = streamRef.current;
      const hasLiveTrack = activeStream
        ?.getVideoTracks()
        .some((track) => track.readyState === "live");

      if (activeStream && hasLiveTrack) {
        if (videoRef.current) {
          videoRef.current.srcObject = activeStream;
          await videoRef.current.play().catch(() => undefined);
        }
        return;
      }

      const nextStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "environment",
          width: { ideal: 1280 },
          height: { ideal: 1600 },
        },
        audio: false,
      });

      streamRef.current = nextStream;

      if (videoRef.current) {
        videoRef.current.srcObject = nextStream;
        await videoRef.current.play().catch(() => undefined);
      }
      setCameraError(null);
    } catch {
      setCameraError("ไม่สามารถเปิดกล้องได้ กรุณาอนุญาตการใช้งานกล้องหรือเปิดผ่าน HTTPS");
    }
  }, []);

  useEffect(() => {
    attachCameraStream();

    return () => {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    };
  }, [attachCameraStream]);

  useEffect(() => {
    if (!capturedImage) {
      attachCameraStream();
    }
  }, [attachCameraStream, capturedImage]);

  function bindVideoElement(node: HTMLVideoElement | null) {
    videoRef.current = node;

    if (node && streamRef.current) {
      node.srcObject = streamRef.current;
      node.play().catch(() => undefined);
    }
  }

  function capturePalm() {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas) {
      return;
    }

    const width = video.videoWidth;
    const height = video.videoHeight;

    if (!width || !height) {
      setCameraError("กล้องยังไม่พร้อม กรุณารอสักครู่แล้วลองถ่ายใหม่");
      return;
    }

    canvas.width = width;
    canvas.height = height;

    const context = canvas.getContext("2d");
    context?.drawImage(video, 0, 0, width, height);
    setCapturedImage(canvas.toDataURL("image/jpeg", 0.92));
    setSelectedFileName("palm-capture.jpg");
    setCaptureSource("camera");
    setScanResult(null);
    setScanError(null);
  }

  function openUploadPicker() {
    fileInputRef.current?.click();
  }

  function uploadPalm(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    if (!file.type.startsWith("image/")) {
      setScanError("กรุณาเลือกไฟล์รูปภาพเท่านั้น");
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      setCapturedImage(String(reader.result));
      setSelectedFileName(file.name || "palm-upload.jpg");
      setCaptureSource("upload");
      setScanResult(null);
      setScanError(null);
    };
    reader.onerror = () => {
      setScanError("อ่านไฟล์รูปภาพไม่สำเร็จ กรุณาลองใหม่อีกครั้ง");
    };
    reader.readAsDataURL(file);

    event.target.value = "";
  }

  async function scanPalm() {
    if (!capturedImage) {
      return;
    }

    setIsScanning(true);
    setScanError(null);

    try {
      const blob = await (await fetch(capturedImage)).blob();
      const formData = new FormData();
      formData.append("image", blob, selectedFileName);
      formData.append("user_hand", userHand);

      const response = await fetch(`${API_BASE_URL}/api/v1/scan-palm`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("scan failed");
      }

      setScanResult((await response.json()) as ScanResponse);
    } catch {
      setScanError(`สแกนไม่สำเร็จ กรุณาตรวจว่า backend ทำงานอยู่ที่ ${API_BASE_URL}`);
    } finally {
      setIsScanning(false);
    }
  }

  function resetScan() {
    setCapturedImage(null);
    setSelectedFileName("palm-capture.jpg");
    setCaptureSource("camera");
    setScanResult(null);
    setScanError(null);
  }

  return (
    <main className="app-shell">
      <section className="scanner-panel">
        <div className="brand-row">
          <div>
            <p className="eyebrow">PalmVerse MVP</p>
            <h1>ดูดวงลายมือ</h1>
          </div>
        </div>

        <div className="hand-picker" aria-label="เลือกมือที่ต้องการสแกน">
          <p>เลือกมือที่ต้องการสแกน</p>
          <div className="hand-options">
            <button
              className={userHand === "left" ? "hand-option active" : "hand-option"}
              type="button"
              onClick={() => setUserHand("left")}
            >
              มือซ้าย
            </button>
            <button
              className={userHand === "right" ? "hand-option active" : "hand-option"}
              type="button"
              onClick={() => setUserHand("right")}
            >
              มือขวา
            </button>
          </div>
          <span>หงายฝ่ามือเข้าหากล้อง วางให้เต็มกรอบ และถ่ายในที่มีแสงพอ</span>
        </div>

        <div className="camera-stage">
          {capturedImage ? (
            <img className="palm-preview" src={capturedImage} alt="Captured palm" />
          ) : (
            <video ref={bindVideoElement} className="palm-preview" autoPlay muted playsInline />
          )}

          {isScanning && (
            <div className="scan-overlay" aria-hidden="true">
              <div className="scan-line" />
            </div>
          )}

        </div>

        <canvas ref={canvasRef} hidden />
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="file-input"
          onChange={uploadPalm}
        />

        {cameraError && <p className="message error">{cameraError}</p>}
        {scanError && <p className="message error">{scanError}</p>}

        <div className="action-row">
          {!capturedImage ? (
            <>
              <button className="secondary-button" onClick={openUploadPicker}>
                อัปโหลดรูป
              </button>
              <button className="primary-button" onClick={capturePalm}>
                ถ่ายภาพฝ่ามือ
              </button>
            </>
          ) : (
            <>
              <button className="secondary-button" onClick={resetScan}>
                ถ่ายใหม่
              </button>
              <button className="primary-button" onClick={scanPalm} disabled={isScanning}>
                {isScanning ? "กำลังสแกน" : "เริ่มสแกน"}
              </button>
            </>
          )}
        </div>
      </section>

      <section className="result-panel">
        <div className="result-header">
          <p className="eyebrow">Reading</p>
          <h2>ผลลัพธ์คำทำนาย</h2>
        </div>

        {scanResult ? (
          <div className="reading-list">
            {Object.entries(scanResult.data.analysis).map(([id, reading]) => (
              <article className="reading-card" key={id}>
                <p className="reading-id">{READING_LABELS[id] ?? "คำทำนาย"}</p>
                <h3>{reading.title}</h3>
                <p>{reading.description}</p>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <p>ถ่ายภาพหรืออัปโหลดรูป แล้วกดเริ่มสแกนเพื่อดูผลลัพธ์ mock จาก backend</p>
          </div>
        )}

        <p className="disclaimer">
          ผลลัพธ์นี้จัดทำเพื่อความบันเทิงและการทดลอง MVP เท่านั้น
        </p>
      </section>
    </main>
  );
}
