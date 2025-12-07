import React, { useState } from "react";
import { scrapeUrl } from "../api";
import { LinkIcon, GlobeAltIcon, ArrowDownTrayIcon } from "@heroicons/react/24/outline";

export default function ScrapeForm({ onStart, onResult, onError, result, onDownload}) {
  const [url, setUrl] = useState("");

  const exampleUrls = [
    "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
    "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "https://nextjs.org/docs",
    "https://vercel.com/",
    "https://news.ycombinator.com/",
  ];

  async function handleSubmit(e) {
    e.preventDefault();

    if (!url.startsWith("http")) {
      return onError("Please enter a valid URL starting with http or https.");
    }

    onStart();

    try {
      const data = await scrapeUrl(url);
      onResult(data);
    } catch (err) {
      onError(err?.response?.data?.detail || "Failed to scrape website.");
    }
  }

  return (
    <div className="bg-white/70 backdrop-blur-xl p-6 rounded-2xl shadow-lg border border-gray-200 animate-fade-in">
      <form onSubmit={handleSubmit} className="space-y-6 flex flex-col">

        {/* Input Box */}
        <div className="relative">
          <LinkIcon className="h-5 w-5 absolute left-3 top-3 text-gray-500" />

          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Enter URL (e.g. https://example.com)"
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl shadow-sm 
                       bg-white/80 focus:ring-2 focus:ring-blue-500 outline-none transition peer"
          />
        </div>

        {/* Example URLs */}
        <div>
          <p className="text-sm text-gray-600 mb-2 flex items-center gap-1">
            <GlobeAltIcon className="h-4 w-4 text-blue-600" />
            Try an example:
          </p>

          <div className="flex flex-wrap gap-2">
            {exampleUrls.map((u) => (
              <button
                key={u}
                type="button"
                onClick={() => setUrl(u)}
                className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 border border-gray-300
                           text-xs rounded-full shadow-sm transition flex items-center gap-1"
              >
                {new URL(u).hostname}
              </button>
            ))}
          </div>
        </div>

        {/* Two Buttons scrape & download */}
        <div className="flex gap-4">

          {/* Scrape Button */}
          <button
            type="submit"
            className="w-1/2 px-6 py-3 bg-blue-600 hover:bg-blue-700 
                       text-white rounded-xl shadow-lg transition transform 
                       hover:scale-[1.03] active:scale-[0.98]"
          >
            Scrape Data
          </button>

          {/* Download JSON Button */}
          <button
            type="button"
            onClick={onDownload}
            disabled={!result}
            className={`w-1/2 px-3 py-3 rounded-xl shadow-lg transition transform 
                        hover:scale-[1.03] active:scale-[0.98] flex items-center justify-center gap-2
                        ${
                          result
                            ? "bg-green-600 hover:bg-green-700 text-white"
                            : "bg-gray-300 text-gray-500 cursor-not-allowed"
                        }`}
          >
            <ArrowDownTrayIcon className="h-5 w-5" />
            Download JSON
          </button>
        </div>

      </form>
    </div>
  );
}
