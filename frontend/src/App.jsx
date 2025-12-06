import React, { useState } from "react";
import ScrapeForm from "./components/ScrapeForm";
import SectionsList from "./components/SectionsList";
import JsonBlock from "./components/JsonBlock";

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const downloadJson = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "scrape-result.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-100 via-gray-50 to-gray-200 text-gray-800 p-6">

      <div className="max-w-6xl mx-auto">

        {/* ---------- Sticky Header w/ Download Button ---------- */}
        <header className="mb-12 text-center animate-fade-in relative">

          <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight drop-shadow-sm">
            Lyftr.AI — Universal Web Scraper
          </h1>

          <p className="text-gray-600 mt-3 text-lg max-w-2xl mx-auto leading-relaxed">
            Scrape static & dynamic websites with intelligent fallback handling,
            structured metadata, clean content sections & interaction tracking.
          </p>
        </header>

        {/* ---------- SCRAPE FORM ---------- */}
        <ScrapeForm
          onStart={() => {
            setLoading(true);
            setError(null);
            setResult(null);
          }}
          onResult={(data) => {
            setResult(data);
            setLoading(false);
          }}
          onError={(e) => {
            setError(e);
            setLoading(false);
          }}
          result={result}
          onDownload={downloadJson} 
        />

        {/* ---------- STATUS ---------- */}
        {loading && (
          <div className="mt-6 text-blue-600 animate-pulse font-medium text-center">
            Scraping the website… ⏳ please wait.
          </div>
        )}

        {error && (
          <div className="mt-6 p-4 bg-red-100 border border-red-300 
              text-red-800 rounded-lg shadow text-center animate-fade-in">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* ---------- RESULTS ---------- */}
        {result && (
          <div className="animate-fade-in mt-10 space-y-10">

            {/* Metadata */}
            <JsonBlock title="Metadata" data={result.meta} />

            {/* Interactions */}
            <JsonBlock title="Interactions" data={result.interactions} />

            {/* Sections */}
            <SectionsList sections={result.sections} />

            {/* Scraper Errors */}
            {result.errors?.length > 0 && (
              <JsonBlock title="Scraper Errors" data={result.errors} />
            )}

            {/* Mobile Download Button
            <div className="text-center md:hidden">
              <button
                onClick={downloadJson}
                className="mt-6 px-6 py-3 bg-blue-600 hover:bg-blue-700 
                text-white rounded-xl shadow-lg transition transform hover:scale-105"
              >
                ⬇️ Download JSON
              </button>
            </div> */}
          </div>
        )}
      </div>
    </div>
  );
}
