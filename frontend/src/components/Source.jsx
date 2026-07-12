import "../css/Source.css";

export default function Source({website, body, link}) {

    return (
        <div className="source">
            <h3 className="website">{website}</h3>
            <p className="body">{body}</p>
            <a target="_blank" className="link" href={link}>View Source➜</a>
        </div>
    )
}