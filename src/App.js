import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [loadingUpload, setLoadingUpload] = useState(false);
  const [loadingQuery, setLoadingQuery] = useState(false);
  const [error, setError] = useState('');

  const uploadFile = async () => {
    if (!file) {
      setError("Please select a file to upload.");
      return;
    }
    setError('');
    setLoadingUpload(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      await axios.post("http://localhost:8000/upload/", formData);
      setResponse("File uploaded successfully!");
    } catch (err) {
      setError("Upload failed. Please try again.");
    }
    setLoadingUpload(false);
  };

  const sendQuery = async () => {
    if (!query.trim()) {
      setError("Please enter your question.");
      return;
    }
    setError('');
    setLoadingQuery(true);
    try {
      const formData = new FormData();
      formData.append("query", query);
      const res = await axios.post("http://localhost:8000/chat/", formData);
      setResponse(res.data.response);
      setQuery('');
    } catch (err) {
      setError("Failed to get response. Please try again.");
    }
    setLoadingQuery(false);
  };

  return (
    <div className="app-container">
      <h1>RAG Chatbot</h1>
      <div className="mb-4">
        <input type="file" onChange={(e) => setFile(e.target.files[0])} />
        {file && <span className="ml-2 text-sm text-gray-600">{file.name}</span>}
        <button
          onClick={uploadFile}
          className={`bg-blue-500 text-white px-4 py-2 mt-2 ml-2 rounded ${loadingUpload ? 'opacity-50 cursor-not-allowed' : ''}`}
          disabled={loadingUpload}
        >
          {loadingUpload ? "Uploading..." : "Upload"}
        </button>
      </div>
      <div className="mb-4">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full p-2 border rounded"
          rows="4"
          placeholder="Ask a question about your document..."
        />
        <button
          onClick={sendQuery}
          className={`bg-green-500 text-white px-4 py-2 mt-2 rounded ${loadingQuery ? 'opacity-50 cursor-not-allowed' : ''}`}
          disabled={loadingQuery}
        >
          {loadingQuery ? "Thinking..." : "Ask"}
        </button>
      </div>
      {error && <div className="error-message">{error}</div>}
      <div className="response-box">
        {response}
      </div>
    </div>
  );
}

export default App;
