import React from "react";

function JsonBlock({ title, data, readOnly = false }) {
  const [open, setOpen] = React.useState(false);

  // Handle invalid/null data safely
  if (data === undefined || data === null) {
    data = {};
  }

  const isSimpleObject = typeof data === "object" && !Array.isArray(data);

  return (
    <div className="mt-8 p-6 bg-white/90 backdrop-blur shadow-lg rounded-xl border border-gray-200">
      <h2 className="text-2xl font-semibold mb-3">{title}</h2>

      {/* Readable Summary (default view) */}
      {!open && isSimpleObject && (
        <div className="space-y-2 text-gray-700 text-sm">
          {Object.entries(data).map(([key, val]) => (
            <div key={key} className="">
              <strong className="capitalize">{key}:</strong>{" "}
              <span className="text-gray-700 wrap-break-word">
                {typeof val === "string"
                  ? val
                  : Array.isArray(val)
                  ? `${val.length} items`
                  : JSON.stringify(val)}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* JSON Viewer */}
      {open && (
        <pre className="bg-gray-50 p-4 rounded text-sm overflow-auto border border-gray-200 max-h-64">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}

      {/* Toggle Button */}
      {!readOnly && (
        <button
          onClick={() => setOpen(!open)}
          className="mt-3 text-blue-600 hover:text-blue-800 font-medium text-sm"
        >
          {open ? "▲ Hide Raw JSON" : "▶ View Raw JSON"}
        </button>
      )}
    </div>
  );
}

export default JsonBlock;
