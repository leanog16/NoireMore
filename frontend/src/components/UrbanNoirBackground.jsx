import React, { useState } from "react";
import "../css/UrbanNoirBackground.css";
import "../css/About.css";
import Report from './Report';
import sidewalkImage from "../assets/sidewalk.jpeg"; 
import logo from "../assets/logo.png"; 
import about from "../assets/about.png"; 

export default function UrbanNoirBackground() {
  const [showAbout, setShowAbout] = useState(false);
  const [text, setText] = useState("");
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [hasNewReport, setHasNewReport] = useState(false);

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
      <div id="light-cone"></div>
      <div id="center">
        <img id="logo" src={logo}/>
        <img 
          id="about" 
          src={about} 
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
        <div id="tab" className={hasNewReport ? "new-report" : ""}>
          <p>
            RESULTS{hasNewReport && " !"}
          </p>
        </div>
        <div id="folder"> 
          <div id="paper-wrapper">
            <div id="bg-paper"></div>
            <div id="paper">
              {loading ? (
                <div style={{ textAlign: 'center', padding: '3rem' }}>
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