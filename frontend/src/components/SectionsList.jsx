import React, { useState } from "react";
import SectionDetail from "./SectionDetails";

function SectionsList({ sections }) {
  const [openIndex, setOpenIndex] = useState(null);

  return (
    <div className="mt-8 p-6 bg-white/80 backdrop-blur shadow-lg rounded-xl border border-gray-200">
      <h2 className="text-2xl font-semibold mb-4">Sections ({sections.length})</h2>

      <div className="space-y-4">
        {sections.map((sec, i) => (
          <div
            key={i}
            className="border border-gray-300 rounded-xl overflow-hidden shadow-sm"
          >
            <button
              className="w-full text-left px-5 py-4 bg-gray-50 hover:bg-gray-100 flex justify-between items-center transition cursor-pointer"
              onClick={() => setOpenIndex(openIndex === i ? null : i)}
            >
              <div>
                <div className="font-semibold text-gray-900">{sec.label}</div>
                <div className="text-sm text-gray-500">{sec.type}</div>
              </div>
              <span className="text-gray-600 text-xl">
                {openIndex === i ? "−" : "+"}
              </span>
            </button>

            {openIndex === i && (
              <div className="px-5 py-4 bg-white border-t border-gray-200">
                <SectionDetail sec={sec} />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default SectionsList;
