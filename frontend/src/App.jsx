import React, { useState } from "react";
import ScrapeForm from "./components/ScrapeForm";
import SectionsList from "./components/SectionsList";
import JsonBlock from "./components/JsonBlock";

export default function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-100 via-gray-50 to-gray-200 text-gray-800 p-6">
      <div className="max-w-5xl mx-auto">

        {/* HEADER */}
        <header className="mb-12 text-center animate-fade-in">
          <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight drop-shadow-sm">
            🌐 Lyftr.AI — Universal Web Scraper
          </h1>
          <p className="text-gray-600 mt-3 text-lg max-w-2xl mx-auto">
            Scrape static & dynamic websites with metadata, sections, media extraction
            and intelligent fallback handling — all in one interface.
          </p>
        </header>

        {/* FORM */}
        <ScrapeForm
          onStart={() => { setLoading(true); setError(null); setResult(null); }}
          onResult={(data) => { setResult(data); setLoading(false); }}
          onError={(e) => { setError(e); setLoading(false); }}
        />

        {/* STATUS */}
        {loading && (
          <div className="mt-6 text-blue-600 animate-pulse font-medium text-center">
            Scraping the website… ⏳ please wait.
          </div>
        )}

        {error && (
          <div className="mt-6 p-4 bg-red-100 border border-red-300 text-red-800 rounded-lg shadow text-center">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* RESULT */}
        {result && (
          <div className="animate-fade-in mt-10">

            {/* METADATA */}
            <JsonBlock title="Metadata" data={result.meta} />

            {/* INTERACTIONS */}
            <JsonBlock title="Interactions" data={result.interactions} />

            {/* SECTIONS */}
            <SectionsList sections={result.sections} />

            {/* SCRAPER ERRORS */}
            {result.errors?.length > 0 && (
              <JsonBlock title="Scraper Errors" data={result.errors} />
            )}

            {/* DOWNLOAD JSON */}
            <div className="text-center">
              <button
                className="mt-10 px-6 py-3 bg-blue-600 hover:bg-blue-700 
                text-white rounded-xl shadow-lg transition transform hover:scale-105"
                onClick={() => {
                  const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = "scrape-result.json";
                  a.click();
                  URL.revokeObjectURL(url);
                }}
              >
                ⬇️ Download Full JSON
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
