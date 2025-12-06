import React, { useState } from "react";
import { scrapeUrl } from "../api";

function ScrapeForm({ onStart, onResult, onError }) {
  const [url, setUrl] = useState("");

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
    <form onSubmit={handleSubmit} className="flex gap-3">
      <input
        type="text"
        placeholder="Enter Your URL, e.g. -> https://example.com"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        className="flex-1 border border-gray-300 rounded-xl px-4 py-3 bg-white shadow-sm focus:ring focus:ring-blue-300 outline-none transition"
      />

      <button
        type="submit"
        className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-lg transition transform hover:scale-105"
      >
        Scrape
      </button>
    </form>
  );
}

export default ScrapeForm;
