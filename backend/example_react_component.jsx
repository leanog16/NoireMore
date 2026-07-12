// Example React component for integrating with the NEW /submit endpoint
// Save this as FactChecker.jsx in your React project

import React, { useState } from 'react';

const FactChecker = () => {
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const API_URL = 'http://localhost:5000';

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!message.trim()) {
      setError('Please enter a claim to verify');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message.trim() }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to verify claim');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message || 'An error occurred while verifying the claim');
    } finally {
      setLoading(false);
    }
  };

  const getResolutionColor = (resolution) => {
    switch (resolution) {
      case 'LIKELY_TRUE':
        return 'text-green-600 bg-green-100 border-green-300';
      case 'LIKELY_FALSE':
        return 'text-red-600 bg-red-100 border-red-300';
      case 'DISPUTED':
        return 'text-yellow-600 bg-yellow-100 border-yellow-300';
      case 'INSUFFICIENT_DATA':
        return 'text-gray-600 bg-gray-100 border-gray-300';
      default:
        return 'text-gray-600 bg-gray-100 border-gray-300';
    }
  };

  const getResolutionIcon = (resolution) => {
    switch (resolution) {
      case 'LIKELY_TRUE':
        return '✓';
      case 'LIKELY_FALSE':
        return '✗';
      case 'DISPUTED':
        return '⚠';
      case 'INSUFFICIENT_DATA':
        return '?';
      default:
        return '';
    }
  };

  const getResolutionText = (resolution) => {
    return resolution.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2 text-gray-800">Fact Checker</h1>
        <p className="text-gray-600">Enter a claim to verify it against multiple trusted sources</p>
      </div>
      
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="flex flex-col gap-4">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Enter a claim to verify (e.g., 'The Earth revolves around the Sun')"
            className="w-full p-4 border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows="4"
            disabled={loading}
          />
          
          <button
            type="submit"
            disabled={loading || !message.trim()}
            className={`px-8 py-4 rounded-lg font-semibold text-lg transition-all ${
              loading || !message.trim()
                ? 'bg-gray-300 cursor-not-allowed text-gray-500'
                : 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl'
            }`}
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                </svg>
                Verifying...
              </span>
            ) : (
              'Verify Claim'
            )}
          </button>
        </div>
      </form>

      {error && (
        <div className="p-4 mb-6 bg-red-100 border-2 border-red-400 text-red-700 rounded-lg flex items-start">
          <span className="text-xl mr-3">⚠️</span>
          <div>
            <p className="font-semibold">Error</p>
            <p>{error}</p>
          </div>
        </div>
      )}

      {result && (
        <div className="space-y-6 animate-fadeIn">
          {/* Main Result Card */}
          <div className="p-6 bg-white border-2 border-gray-200 rounded-xl shadow-lg">
            <h2 className="text-2xl font-bold mb-4 text-gray-800">Verification Result</h2>
            
            {/* Topic */}
            <div className="mb-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">Claim:</p>
              <p className="text-lg font-medium text-gray-800">{result.topic}</p>
            </div>
            
            {/* Resolution Badge */}
            <div className={`inline-flex items-center gap-2 px-6 py-3 rounded-lg font-bold text-lg border-2 ${getResolutionColor(result.resolution)}`}>
              <span className="text-2xl">{getResolutionIcon(result.resolution)}</span>
              <span>{getResolutionText(result.resolution)}</span>
            </div>
            
            {/* Confidence */}
            <div className="mt-4">
              <p className="text-sm text-gray-600 mb-2">Confidence Level</p>
              <div className="flex items-center gap-3">
                <div className="flex-1 bg-gray-200 rounded-full h-4 overflow-hidden">
                  <div 
                    className="bg-blue-600 h-full rounded-full transition-all duration-500"
                    style={{ width: result.confidence }}
                  />
                </div>
                <span className="text-xl font-bold text-blue-600">{result.confidence}</span>
              </div>
            </div>

            {/* Statistics Grid */}
            <div className="mt-6 grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-green-50 rounded-lg border-2 border-green-200">
                <div className="text-3xl font-bold text-green-600">
                  {result.supporting}
                </div>
                <div className="text-sm font-medium text-gray-700 mt-1">Supporting</div>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg border-2 border-red-200">
                <div className="text-3xl font-bold text-red-600">
                  {result.contradicting}
                </div>
                <div className="text-sm font-medium text-gray-700 mt-1">Contradicting</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg border-2 border-gray-200">
                <div className="text-3xl font-bold text-gray-600">
                  {result.neutral}
                </div>
                <div className="text-sm font-medium text-gray-700 mt-1">Neutral</div>
              </div>
            </div>
          </div>

          {/* Sources Section */}
          {result.sources && result.sources.length > 0 && (
            <div className="p-6 bg-white border-2 border-gray-200 rounded-xl shadow-lg">
              <h2 className="text-2xl font-bold mb-4 text-gray-800">
                Sources ({result.sources.length})
              </h2>
              
              <div className="space-y-4">
                {result.sources.map((source, index) => (
                  <div 
                    key={index} 
                    className="p-4 border-2 border-gray-200 rounded-lg hover:shadow-md hover:border-blue-300 transition-all"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        {/* Source Website Badge */}
                        <div className="flex items-center gap-2 mb-3">
                          <span className="px-3 py-1 text-sm font-semibold bg-blue-100 text-blue-800 rounded-full">
                            {source.website}
                          </span>
                        </div>
                        
                        {/* Source Body/Snippet */}
                        {source.body && (
                          <p className="text-gray-700 mb-3 leading-relaxed">
                            {source.body}
                          </p>
                        )}
                        
                        {/* Source Link */}
                        {source.link && (
                          <a
                            href={source.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-800 font-medium text-sm transition-colors"
                          >
                            <span>View Source</span>
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                            </svg>
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FactChecker;
