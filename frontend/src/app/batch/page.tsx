import BatchAnalysis from "../../components/BatchAnalysis";

export default function BatchPage() {
  return (
    <main className="min-h-screen bg-slate-950 p-6 text-white">
      <div className="mx-auto max-w-6xl">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">Batch SSS Analysis</h1>
          <p className="mt-2 text-slate-400">
            Analyze multiple Side-Scan Sonar images in a single mission workflow.
          </p>
        </div>

        <BatchAnalysis />
      </div>
    </main>
  );
}
