"use client";

import { useState } from "react";

const API_URL = "http://127.0.0.1:8000";

type VerificationStatus =
  | "NEEDS REVIEW"
  | "CONFIRMED"
  | "REJECTED";

type BatchDetection = {
  class: string;
  confidence: number;
  bbox?: number[];
};

type BatchResult = {
  filename: string;
  status: string;
  detection_count?: number;
  detections?: BatchDetection[];
  error?: string;
};

type BatchResponse = {
  total_files: number;
  successful_files: number;
  failed_files: number;
  results: BatchResult[];
};

type VerificationState = {
  status: VerificationStatus;
  correctedClass?: string;
  saving?: boolean;
  saved?: boolean;
  error?: string;
};

const availableClasses = [
  "shipwreck",
  "ghost_net",
  "crab_pot",
  "submarine_pipeline",
  "mine_cylinder",
  "unknown_anomaly",
];

function formatClassName(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

export default function BatchAnalysis() {
  const [files, setFiles] = useState<File[]>([]);
  const [result, setResult] = useState<BatchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [verification, setVerification] = useState<
    Record<string, VerificationState>
  >({});

  function handleFileChange(
    event: React.ChangeEvent<HTMLInputElement>
  ) {
    const selectedFiles = Array.from(event.target.files || []);

    setFiles(selectedFiles);
    setResult(null);
    setError("");
    setVerification({});
  }

  async function handleAnalyze() {
    if (files.length === 0) {
      setError("Please select at least one sonar image.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);
    setVerification({});

    try {
      const formData = new FormData();

      files.forEach((file) => {
        formData.append("files", file);
      });

      const response = await fetch(`${API_URL}/analyze-batch`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const data: BatchResponse = await response.json();
      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Batch analysis failed."
      );
    } finally {
      setLoading(false);
    }
  }

  function clearFiles() {
    setFiles([]);
    setResult(null);
    setError("");
    setVerification({});
  }

  function getVerificationKey(
    resultIndex: number,
    detectionIndex: number
  ) {
    return `${resultIndex}-${detectionIndex}`;
  }

  async function saveFeedback(
    resultIndex: number,
    detectionIndex: number,
    detection: BatchDetection,
    status: VerificationStatus,
    correctedClass?: string
  ) {
    if (status === "REJECTED" && !correctedClass) {
      setVerification((previous) => ({
        ...previous,
        [getVerificationKey(resultIndex, detectionIndex)]: {
          status,
          error: "Please select the corrected classification.",
        },
      }));

      return;
    }

    const key = getVerificationKey(
      resultIndex,
      detectionIndex
    );

    setVerification((previous) => ({
      ...previous,
      [key]: {
        status,
        correctedClass,
        saving: true,
      },
    }));

    try {
      const response = await fetch(`${API_URL}/feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          detection_index: detectionIndex,
          ai_class: detection.class,
          ai_confidence: detection.confidence,
          human_decision: status,
          corrected_class:
            status === "REJECTED"
              ? correctedClass
              : null,
          timestamp: new Date().toISOString(),
        }),
      });

      if (!response.ok) {
        throw new Error(`Feedback API returned ${response.status}`);
      }

      setVerification((previous) => ({
        ...previous,
        [key]: {
          status,
          correctedClass,
          saving: false,
          saved: true,
        },
      }));
    } catch (err) {
      setVerification((previous) => ({
        ...previous,
        [key]: {
          status,
          correctedClass,
          saving: false,
          error:
            err instanceof Error
              ? err.message
              : "Could not save feedback.",
        },
      }));
    }
  }

  return (
    <section className="rounded-2xl border border-slate-700 bg-slate-900 p-6">
      <h2 className="text-2xl font-semibold">
        Batch SSS Analysis
      </h2>

      <p className="mt-2 text-sm text-slate-400">
        Select multiple Side-Scan Sonar images and analyze them
        together.
      </p>

      <div className="mt-6">
        <input
          type="file"
          multiple
          accept=".jpg,.jpeg,.png,.bmp,.tif,.tiff"
          onChange={handleFileChange}
          className="block w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm"
        />
      </div>

      {files.length > 0 && (
        <div className="mt-4">
          <p className="font-medium">
            Selected files: {files.length}
          </p>

          <ul className="mt-2 space-y-1 text-sm text-slate-400">
            {files.map((file, index) => (
              <li key={`${file.name}-${index}`}>
                {file.name}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-6 flex gap-3">
        <button
          onClick={handleAnalyze}
          disabled={loading || files.length === 0}
          className="rounded-lg bg-blue-600 px-5 py-2.5 font-medium hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Analyzing..." : "Analyze Batch"}
        </button>

        <button
          onClick={clearFiles}
          disabled={loading}
          className="rounded-lg border border-slate-600 px-5 py-2.5 font-medium hover:bg-slate-800 disabled:opacity-50"
        >
          Clear
        </button>
      </div>

      {error && (
        <div className="mt-5 rounded-lg border border-red-800 bg-red-950/40 p-4 text-red-300">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-8">
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-xl bg-slate-800 p-4">
              <p className="text-sm text-slate-400">
                Total Files
              </p>
              <p className="mt-1 text-2xl font-bold">
                {result.total_files}
              </p>
            </div>

            <div className="rounded-xl bg-slate-800 p-4">
              <p className="text-sm text-slate-400">
                Successful
              </p>
              <p className="mt-1 text-2xl font-bold text-green-400">
                {result.successful_files}
              </p>
            </div>

            <div className="rounded-xl bg-slate-800 p-4">
              <p className="text-sm text-slate-400">
                Failed
              </p>
              <p className="mt-1 text-2xl font-bold text-red-400">
                {result.failed_files}
              </p>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            {result.results.map((item, resultIndex) => (
              <div
                key={`${item.filename}-${resultIndex}`}
                className="rounded-xl border border-slate-700 bg-slate-950 p-4"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="font-medium">
                    {item.filename}
                  </h3>

                  <span
                    className={
                      item.status === "success"
                        ? "rounded-full bg-green-900 px-3 py-1 text-xs text-green-300"
                        : "rounded-full bg-red-900 px-3 py-1 text-xs text-red-300"
                    }
                  >
                    {item.status}
                  </span>
                </div>

                {item.status === "success" &&
                  item.detections && (
                    <div className="mt-4">
                      <p className="text-sm text-slate-400">
                        Detections: {item.detection_count ?? 0}
                      </p>

                      {item.detections.length === 0 && (
                        <div className="mt-3 rounded-lg border border-slate-800 bg-slate-900 p-4 text-sm text-slate-400">
                          No AI detections found in this image.
                        </div>
                      )}

                      <div className="mt-3 space-y-4">
                        {item.detections.map(
                          (detection, detectionIndex) => {
                            const key =
                              getVerificationKey(
                                resultIndex,
                                detectionIndex
                              );

                            const current =
                              verification[key];

                            return (
                              <div
                                key={detectionIndex}
                                className="rounded-xl border border-slate-800 bg-slate-900 p-4"
                              >
                                <div className="flex flex-wrap items-center justify-between gap-3">
                                  <div>
                                    <p className="font-semibold">
                                      {formatClassName(
                                        detection.class
                                      )}
                                    </p>

                                    <p className="mt-1 text-sm text-slate-400">
                                      AI confidence:{" "}
                                      {(
                                        detection.confidence *
                                        100
                                      ).toFixed(1)}
                                      %
                                    </p>
                                  </div>

                                  {current && (
                                    <span
                                      className={
                                        current.status ===
                                        "CONFIRMED"
                                          ? "rounded-full bg-green-900 px-3 py-1 text-xs text-green-300"
                                          : current.status ===
                                              "REJECTED"
                                            ? "rounded-full bg-red-900 px-3 py-1 text-xs text-red-300"
                                            : "rounded-full bg-yellow-900 px-3 py-1 text-xs text-yellow-300"
                                      }
                                    >
                                      {current.status}
                                    </span>
                                  )}
                                </div>

                                <div className="mt-4 rounded-lg border border-slate-800 bg-slate-950 p-3 text-sm">
                                  <p className="text-slate-300">
                                    A{" "}
                                    <strong>
                                      {formatClassName(
                                        detection.class
                                      )}
                                    </strong>{" "}
                                    has been detected with{" "}
                                    <strong>
                                      {(
                                        detection.confidence *
                                        100
                                      ).toFixed(1)}
                                      %
                                    </strong>{" "}
                                    confidence.
                                  </p>

                                  <p className="mt-2 text-slate-400">
                                    Do you confirm that this AI
                                    detection is correct?
                                  </p>
                                </div>

                                <div className="mt-4 flex flex-wrap gap-2">
                                  <button
                                    onClick={() =>
                                      saveFeedback(
                                        resultIndex,
                                        detectionIndex,
                                        detection,
                                        "CONFIRMED"
                                      )
                                    }
                                    disabled={current?.saving}
                                    className="rounded-lg bg-green-700 px-4 py-2 text-sm font-medium hover:bg-green-600 disabled:opacity-50"
                                  >
                                    Confirm
                                  </button>

                                  <button
                                    onClick={() =>
                                      saveFeedback(
                                        resultIndex,
                                        detectionIndex,
                                        detection,
                                        "NEEDS REVIEW"
                                      )
                                    }
                                    disabled={current?.saving}
                                    className="rounded-lg bg-yellow-700 px-4 py-2 text-sm font-medium hover:bg-yellow-600 disabled:opacity-50"
                                  >
                                    Needs Review
                                  </button>

                                  <button
                                    onClick={() =>
                                      setVerification(
                                        (previous) => ({
                                          ...previous,
                                          [key]: {
                                            status: "REJECTED",
                                          },
                                        })
                                      )
                                    }
                                    disabled={current?.saving}
                                    className="rounded-lg bg-red-700 px-4 py-2 text-sm font-medium hover:bg-red-600 disabled:opacity-50"
                                  >
                                    Reject
                                  </button>
                                </div>

                                {current?.status ===
                                  "REJECTED" && (
                                  <div className="mt-4 rounded-lg border border-red-900 bg-red-950/30 p-4">
                                    <label className="text-sm font-medium text-slate-300">
                                      What should this target
                                      be classified as?
                                    </label>

                                    <select
                                      value={
                                        current.correctedClass ??
                                        ""
                                      }
                                      onChange={(event) =>
                                        setVerification(
                                          (previous) => ({
                                            ...previous,
                                            [key]: {
                                              ...previous[key],
                                              status: "REJECTED",
                                              correctedClass:
                                                event.target
                                                  .value,
                                            },
                                          })
                                        )
                                      }
                                      className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm"
                                    >
                                      <option value="">
                                        Select corrected class
                                      </option>

                                      {availableClasses.map(
                                        (className) => (
                                          <option
                                            key={className}
                                            value={className}
                                          >
                                            {formatClassName(
                                              className
                                            )}
                                          </option>
                                        )
                                      )}
                                    </select>

                                    <button
                                      onClick={() =>
                                        saveFeedback(
                                          resultIndex,
                                          detectionIndex,
                                          detection,
                                          "REJECTED",
                                          current.correctedClass
                                        )
                                      }
                                      disabled={
                                        current.saving ||
                                        !current.correctedClass
                                      }
                                      className="mt-3 rounded-lg bg-red-700 px-4 py-2 text-sm font-medium hover:bg-red-600 disabled:cursor-not-allowed disabled:opacity-50"
                                    >
                                      {current.saving
                                        ? "Saving..."
                                        : "Save Rejection"}
                                    </button>
                                  </div>
                                )}

                                {current?.saving && (
                                  <p className="mt-3 text-sm text-blue-400">
                                    Saving human feedback...
                                  </p>
                                )}

                                {current?.saved && (
                                  <p className="mt-3 text-sm text-green-400">
                                    Human feedback recorded
                                    successfully.
                                  </p>
                                )}

                                {current?.error && (
                                  <p className="mt-3 text-sm text-red-400">
                                    {current.error}
                                  </p>
                                )}
                              </div>
                            );
                          }
                        )}
                      </div>
                    </div>
                  )}

                {item.error && (
                  <p className="mt-3 text-sm text-red-400">
                    {item.error}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
