import React, { useState } from "react";

function SectionDetail({ sec }) {
  const c = sec.content || {};

  const [showAllLinks, setShowAllLinks] = useState(false);
  const [showAllImages, setShowAllImages] = useState(false);
  const [openJson, setOpenJson] = useState(false);

  // Limiters
  const linkLimit = 10;
  const imageLimit = 10;

  const visibleLinks = showAllLinks ? c.links : (c.links || []).slice(0, linkLimit);
  const visibleImages = showAllImages ? c.images : (c.images || []).slice(0, imageLimit);

  return (
    <div className="text-sm space-y-5">

      {/* HEADINGS */}
      {c.headings?.length > 0 && (
        <div>
          <strong className="text-gray-700">Headings:</strong>
          <div className="mt-1 text-gray-800">
            {c.headings.join(" • ")}
          </div>
        </div>
      )}

      {/* TEXT */}
      {c.text && (
        <div>
          <strong className="text-gray-700">Text:</strong>
          <pre className="bg-gray-50 p-3 rounded mt-1 whitespace-pre-wrap border border-gray-200 max-h-64 overflow-auto">
            {c.text}
          </pre>
        </div>
      )}

      {/* LINKS */}
      {c.links?.length > 0 && (
        <div>
          <strong className="text-gray-700">Links ({c.links.length}):</strong>
          <ul className="list-disc ml-6 mt-2 text-blue-700 space-y-1">
            {visibleLinks.map((l, i) => (
              <li key={i}>
                <a href={l.href} target="_blank" rel="noopener noreferrer" className="hover:underline">
                  {l.text || l.href}
                </a>
              </li>
            ))}
          </ul>

          {/* show more */}
          {c.links.length > linkLimit && !showAllLinks && (
            <button
              className="text-sm text-blue-600 mt-1 hover:underline cursor-pointer"
              onClick={() => setShowAllLinks(true)}
            >
              ...and {c.links.length - linkLimit} more
            </button>
          )}

          {/* collapse */}
          {showAllLinks && c.links.length > linkLimit && (
            <button
              className="text-sm text-blue-600 mt-1 hover:underline cursor-pointer"
              onClick={() => setShowAllLinks(false)}
            >
              Show less ▲
            </button>
          )}
        </div>
      )}

      {/* IMAGES */}
      {c.images?.length > 0 && (
        <div>
          <strong className="text-gray-700">Images ({c.images.length}):</strong>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2">
            {visibleImages.map((img, i) => (
              <img
                key={i}
                src={img.src}
                alt={img.alt}
                className="rounded border shadow-sm object-cover h-28 w-full"
              />
            ))}
          </div>

          {/* show more */}
          {c.images.length > imageLimit && !showAllImages && (
            <button
              className="text-sm text-blue-600 mt-1 hover:underline cursor-pointer"
              onClick={() => setShowAllImages(true)}
            >
              ...and {c.images.length - imageLimit} more
            </button>
          )}

          {/* collapse */}
          {showAllImages && c.images.length > imageLimit && (
            <button
              className="text-sm text-blue-600 mt-1 hover:underline cursor-pointer"
              onClick={() => setShowAllImages(false)}
            >
              Show less ▲
            </button>
          )}
        </div>
      )}

      {/* RAW HTML */}
      <div>
        <strong className="text-gray-700">Raw HTML (truncated):</strong>
        <pre className="bg-gray-50 p-3 rounded mt-1 whitespace-pre-wrap border border-gray-200 max-h-64 overflow-auto">
          {sec.rawHtml}
        </pre>
      </div>

      {/* JSON VIEWER */}
      <div>
        <button
          className="text-sm font-medium text-gray-700 flex items-center gap-1 hover:underline cursor-pointer"
          onClick={() => setOpenJson(!openJson)}
        >
          {openJson ? "▼" : "▶"} View Raw JSON
        </button>

        {openJson && (
          <pre className="bg-gray-100 p-4 rounded mt-2 text-xs overflow-auto border border-gray-300 max-h-80">
            {JSON.stringify(sec, null, 2)}
          </pre>
        )}
      </div>

    </div>
  );
}

export default SectionDetail;
