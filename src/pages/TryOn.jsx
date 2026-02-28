import React, { useState, useRef } from "react";
import axios from "axios";

const TryOn = () => {
  const [selfieFile, setSelfieFile] = useState(null);
  const [selfiePreview, setSelfiePreview] = useState(null);
  const [resultUrl, setResultUrl] = useState(null);
  const [selectedAccessory, setSelectedAccessory] = useState("accessories/glasses/images.png");
  const [loading, setLoading] = useState(false);

  const accessories = [
    { label: "Glasses 1",  path: "accessories/glasses/images.png" },
    { label: "Glasses 2",  path: "accessories/glasses/images-2.jpeg" },
    { label: "Glasses 3",  path: "accessories/glasses/images-3.jpeg" },
    { label: "Glasses 4",  path: "accessories/glasses/images-4.jpeg" },
    { label: "Glasses 5",  path: "accessories/glasses/images-5.jpeg" },
    { label: "Glasses 6",  path: "accessories/glasses/images-6.jpeg" },
    { label: "Glasses 7",  path: "accessories/glasses/images-7.jpeg" },
    { label: "Glasses 8",  path: "accessories/glasses/images-8.jpeg" },
    { label: "Glasses 9",  path: "accessories/glasses/images-9.jpeg" },
    { label: "Glasses 10", path: "accessories/glasses/images-10.jpeg" },
    { label: "Glasses 11", path: "accessories/glasses/images-11.jpeg" },
    { label: "Glasses 12", path: "accessories/glasses/images-12.jpeg" },
  ];

  const handleSelfieChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setSelfieFile(file);
    setSelfiePreview(URL.createObjectURL(file));
    setResultUrl(null);
  };

  const handleTryOn = async () => {
    if (!selfieFile) {
      alert("Please upload a selfie first.");
      return;
    }

    const formData = new FormData();
    formData.append("image", selfieFile);
    formData.append("accessory_path", selectedAccessory);

    try {
      setLoading(true);
      setResultUrl(null);
      const res = await axios.post("http://localhost:5000/tryon", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const { result_path } = res.data;
      // Cache bust so browser doesn't show stale result
      setResultUrl(`http://localhost:5000${result_path}?t=${Date.now()}`);
    } catch (err) {
      console.error(err);
      alert("Try-on failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-pink-50 px-6 py-10">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-6">Virtual Try-On</h2>
        <p className="text-center text-gray-600 mb-8">
          Upload a selfie and see how accessories look on you.
        </p>

        {/* Accessory selector */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Choose Accessory</label>
          <select
            value={selectedAccessory}
            onChange={(e) => setSelectedAccessory(e.target.value)}
            className="border rounded px-3 py-2"
          >
            {accessories.map((a) => (
              <option key={a.path} value={a.path}>
                {a.label}
              </option>
            ))}
          </select>
        </div>

        {/* Selfie upload */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Upload Selfie</label>
          <input type="file" accept="image/*" onChange={handleSelfieChange} />
        </div>

        {/* Try On button */}
        <div className="mb-6 text-center">
          <button
            onClick={handleTryOn}
            disabled={loading || !selfieFile}
            className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Processing..." : "Try On"}
          </button>
        </div>

        <div className="grid md:grid-cols-2 gap-8 mt-6">
          {/* Original selfie */}
          <div className="text-center">
            <h3 className="font-semibold mb-2">Your Selfie</h3>
            {selfiePreview ? (
              <img
                src={selfiePreview}
                alt="Selfie preview"
                className="w-full max-w-xs mx-auto rounded-lg shadow"
              />
            ) : (
              <p className="text-gray-500 text-sm">No image uploaded yet.</p>
            )}
          </div>

          {/* Result */}
          <div className="text-center">
            <h3 className="font-semibold mb-2">Try-On Result</h3>
            {loading && <p className="text-gray-500">Processing...</p>}
            {resultUrl && !loading && (
              <img
                src={resultUrl}
                alt="Try-on result"
                className="w-full max-w-xs mx-auto rounded-lg shadow"
              />
            )}
            {!resultUrl && !loading && (
              <p className="text-gray-500 text-sm">
                Upload a selfie and click Try On.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TryOn;