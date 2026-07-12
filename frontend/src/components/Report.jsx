import "../css/Report.css";
import Source from './Source';

export default function Report ({topic, resolution, confidence, supporting, contradicting, neutral, source_list}) {

  const getResolutionClass = () => {
    if (resolution === 'LIKELY_FALSE') return 'resolution-false';
    if (resolution === 'LIKELY_TRUE') return 'resolution-true';
    if (resolution === 'DISPUTED') return 'resolution-disputed';
    return '';
  };


  const getConfidenceClass = () => {
    const confidenceNum = parseInt(confidence);
    if (confidenceNum <= 40) return 'confidence-low';
    if (confidenceNum <= 60) return 'confidence-medium';
    return 'confidence-high';
  };

  return (
    <div>
      <h1 id="topic">CASEFILE: {topic}</h1>
      <div id="resolution" className={getResolutionClass()}>
        <h2>{resolution}</h2>
      </div>
      <h2 id="confidence" className={getConfidenceClass()}>CONFIDENCE LEVEL: {confidence}</h2>
      <div id="source-cats">
        <div id='supportingg'>
          <h3>{supporting}</h3>
          <p>SUPPORTING</p>
        </div>
        <div id="contradicting">
          <h3>{contradicting}</h3>
          <p>CONTRADICTING</p>
        </div>
        <div id="neutral">
          <h3>{neutral}</h3>
          <p>NEUTRAL</p>
        </div>
      </div>
      <div id="sources">
        {source_list.map((source, index) => (
          <Source
            key={index}
            website={source.website}
            body={source.body}
            link={source.link}
          />
        ))}
      </div>
    </div>
  );
}