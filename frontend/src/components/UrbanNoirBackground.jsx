import React, { useState, useEffect } from "react";
import "../css/UrbanNoirBackground.css";
import "../css/About.css";
import Report from './Report';
import sidewalkImage from "../assets/sidewalk.webp";
import logo from "../assets/logo.webp";
import about from "../assets/about.webp";

// Natural pixel size of sidewalk.webp, and the lamp bulb's fractional
// position within it. Used to keep the light-cone glow pinned to the
// lamp regardless of screen size/aspect ratio, matching how the CSS
// background (background-size: cover; background-position: top center)
// scales and crops the same image.
const BG_IMAGE_WIDTH = 2560;
const BG_IMAGE_HEIGHT = 1853;
const BULB_FRACTION_X = 0.113;
const BULB_FRACTION_Y = 0.095;

function computeBulbPosition() {
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const scale = Math.max(vw / BG_IMAGE_WIDTH, vh / BG_IMAGE_HEIGHT);
  const renderedWidth = BG_IMAGE_WIDTH * scale;
  const renderedHeight = BG_IMAGE_HEIGHT * scale;
  const offsetX = 0; // horizontal: left-anchored
  const offsetY = 0; // vertical: top-anchored

  return {
    left: offsetX + BULB_FRACTION_X * renderedWidth,
    top: offsetY + BULB_FRACTION_Y * renderedHeight,
  };
}

export default function UrbanNoirBackground() {
  const [showAbout, setShowAbout] = useState(false);
  const [text, setText] = useState("");
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hasNewReport, setHasNewReport] = useState(false);
  const [bulbPosition, setBulbPosition] = useState(computeBulbPosition);

  useEffect(() => {
    const handleResize = () => setBulbPosition(computeBulbPosition());
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleSubmit = async () => {
    console.log("Submitting text:", text);
    

    if (!text || text.trim() === "") {
      alert("Please enter a claim to investigate");
      return;
    }
    
    if (text.trim().length < 3) {
      alert("Claim must be at least 3 characters long");
      return;
    }
    
    setHasNewReport(false);
    setLoading(true);

    try {
      const response = await fetch("/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text.trim() })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        console.error("Server error:", data);
        alert(`Error: ${data.error || 'Unknown error'}`);
        setLoading(false);
        return;
      }
      
      console.log("Success! Server response:", data);
      
 
      setReportData(data);
      setHasNewReport(true);
      setLoading(false);
      
    } catch (error) {
      console.error("Error submitting:", error);
      alert("Failed to connect to server. Make sure the backend is running.");
      setLoading(false);
    }
  };

  const handleFolderHover = () => {
    setHasNewReport(false);
  };

  return (
    <div id="main" style={{ backgroundImage: `url(${sidewalkImage})` }}>
      <div
        id="light-cone"
        style={{ left: `${bulbPosition.left}px`, top: `${bulbPosition.top}px` }}
      ></div>
      <div id="center">
        <img id="logo" src={logo} fetchPriority="high" decoding="async"/>
        <img
          id="about"
          src={about}
          decoding="async"
          onClick={() => setShowAbout(true)}
          style={{ cursor: 'pointer' }}
        />
      </div>
      <div id="input-div">
        <input 
          id="search-bar" 
          type="text" 
          placeholder="Enter claim to investigate..." 
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              handleSubmit();
            }
          }}
        />
        <button 
          id="search-button" 
          onClick={handleSubmit}
          disabled={loading}
        ></button>
      </div>
      <div id="folder-div" onMouseEnter={handleFolderHover}>
        <div id="tab" className={hasNewReport ? "new-report" : loading ? "loading-tab" : ""}>
          <p>
            RESULTS{hasNewReport && " !"}
          </p>
          {loading && <div className="tab-spinner" aria-label="Investigating..." />}
        </div>
        <div id="folder"> 
          <div id="paper-wrapper">
            <div id="bg-paper"></div>
            <div id="paper">
              {loading ? (
                <div style={{ textAlign: 'center', padding: '3rem' }}>
                  <div className="paper-spinner" aria-label="Investigating..."></div>
                  <h2 className="casefile-placeholder">INVESTIGATING...</h2>
                  <p className="casefile-placeholder">Analyzing claim and gathering sources...</p>
                </div>
              ) : reportData ? (
                <Report 
                  topic={reportData.topic}
                  resolution={reportData.resolution}
                  confidence={reportData.confidence}
                  supporting={reportData.supporting}
                  contradicting={reportData.contradicting}
                  neutral={reportData.neutral}
                  source_list={reportData.sources}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: '3rem' }}>
                  <h2 className="casefile-placeholder">NO CASE FILE</h2>
                  <p className="casefile-placeholder">Enter a claim above to begin investigation</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      
      {showAbout && (
        <div id="modal-overlay" onClick={() => setShowAbout(false)}>
          <div id="modal-content" onClick={(e) => e.stopPropagation()}>
            <button id="modal-close" onClick={() => setShowAbout(false)}>✕</button>
            <h2>ABOUT THE PROJECT</h2>
            <hr />
            <div id="modal-body">
              <p>
                This is a fact-checking tool designed to help you investigate claims and 
                statements found online. Simply enter a claim, and our detective 
                system will analyze the content and provide you with a comprehensive report.
              </p>
              <p>
                The casefile will include:
              </p>
              <ul>
                <li>A confidence level assessment</li>
                <li>Supporting, contradicting, and neutral sources</li>
                <li>Detailed analysis of each source</li>
              </ul>
              <p>
                Navigate the digital streets with confidence. The truth is out there.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}