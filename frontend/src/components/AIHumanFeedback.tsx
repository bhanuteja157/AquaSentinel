"use client";

import { useState } from "react";

type VerificationStatus =
  | "NEEDS REVIEW"
  | "CONFIRMED"
  | "REJECTED";

type AIHumanFeedbackProps = {
  detectionClass: string;
  confidence: number;
  status: VerificationStatus;
  onStatusChange: (status: VerificationStatus) => void;
  onCorrection: (correctedClass: string) => void;
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

export default function AIHumanFeedback({
  detectionClass,
  confidence,
  status,
  onStatusChange,
  onCorrection,
}: AIHumanFeedbackProps) {
  const [showCorrection, setShowCorrection] = useState(false);
  const [correctedClass, setCorrectedClass] = useState("");

  const confidencePercent = (confidence * 100).toFixed(1);

  let aiMessage: string;

  if (confidence >= 0.8) {
    aiMessage = `A ${formatClassName(
      detectionClass
    )} has been detected with ${confidencePercent}% confidence.`;
  } else if (confidence >= 0.5) {
    aiMessage = `A possible ${formatClassName(
      detectionClass
    )} has been detected with ${confidencePercent}% confidence. Human verification is recommended.`;
  } else {
    aiMessage = `A possible ${formatClassName(
      detectionClass
    )} has been detected with ${confidencePercent}% confidence. This result is uncertain and requires human review.`;
  }

  function handleConfirm() {
    setShowCorrection(false);
    onStatusChange("CONFIRMED");
  }

  function handleReject() {
    setShowCorrection(true);
    onStatusChange("REJECTED");
  }

  function handleNeedsReview() {
    setShowCorrection(false);
    onStatusChange("NEEDS REVIEW");
  }

  function handleCorrectionChange(value: string) {
    setCorrectedClass(value);
    onCorrection(value);
  }

  return (
    <div className="mt-5 rounded-2xl border border-cyan-400/20 bg-slate-950/70 p-5">
      <div className="mb-4">
        <div className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-cyan-300">
          AquaSentinel AI
        </div>

        <p className="text-sm leading-6 text-slate-200">
          {aiMessage}
        </p>
      </div>

      {status === "NEEDS REVIEW" && (
        <div className="mb-4 rounded-xl border border-amber-400/20 bg-amber-400/5 p-4">
          <p className="text-sm font-medium text-amber-200">
            Do you confirm that this AI detection is correct?
          </p>

          <p className="mt-1 text-xs text-slate-400">
            Your response will be recorded as human verification feedback.
          </p>
        </div>
      )}

      {status === "CONFIRMED" && (
        <div className="mb-4 rounded-xl border border-emerald-400/20 bg-emerald-400/5 p-4">
          <p className="text-sm font-medium text-emerald-300">
            Human confirmation recorded.
          </p>

          <p className="mt-1 text-xs text-slate-400">
            The {formatClassName(detectionClass)} detection was confirmed by
            the operator.
          </p>
        </div>
      )}

      {status === "REJECTED" && (
        <div className="mb-4 rounded-xl border border-red-400/20 bg-red-400/5 p-4">
          <p className="text-sm font-medium text-red-300">
            AI detection rejected.
          </p>

          <p className="mt-1 text-xs text-slate-400">
            Please provide the classification you believe is correct.
          </p>
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={handleConfirm}
          className="rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-4 py-2 text-sm font-semibold text-emerald-300 transition hover:bg-emerald-400/20"
        >
          ✓ Confirm Detection
        </button>

        <button
          type="button"
          onClick={handleReject}
          className="rounded-xl border border-red-400/30 bg-red-400/10 px-4 py-2 text-sm font-semibold text-red-300 transition hover:bg-red-400/20"
        >
          ✕ Reject Detection
        </button>

        <button
          type="button"
          onClick={handleNeedsReview}
          className="rounded-xl border border-amber-400/30 bg-amber-400/10 px-4 py-2 text-sm font-semibold text-amber-300 transition hover:bg-amber-400/20"
        >
          ⚠ Needs Review
        </button>
      </div>

      {showCorrection && (
        <div className="mt-5 border-t border-slate-800 pt-5">
          <label
            htmlFor="corrected-class"
            className="mb-2 block text-sm font-medium text-slate-200"
          >
            What do you believe this target is?
          </label>

          <select
            id="corrected-class"
            value={correctedClass}
            onChange={(event) =>
              handleCorrectionChange(event.target.value)
            }
            className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-slate-200 outline-none focus:border-cyan-400"
          >
            <option value="">Select a classification</option>

            {availableClasses.map((item) => (
              <option key={item} value={item}>
                {formatClassName(item)}
              </option>
            ))}
          </select>

          <p className="mt-2 text-xs text-slate-500">
            This correction is human feedback. It does not automatically
            retrain or modify the AI model.
          </p>
        </div>
      )}
    </div>
  );
}