import os
import json
import time
from datetime import datetime
from urllib.parse import quote_plus, unquote, urlparse

import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
if not groq_client:
    print("WARNING: GROQ_API_KEY is not set. Claim analysis will fall back to a basic heuristic.")

ANALYSIS_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["LIKELY_TRUE", "LIKELY_FALSE", "DISPUTED", "INSUFFICIENT_DATA"],
        },
        "confidence": {"type": "integer"},
        "summary": {"type": "string"},
        "supporting": {"type": "integer"},
        "contradicting": {"type": "integer"},
        "neutral": {"type": "integer"},
    },
    "required": ["verdict", "confidence", "summary", "supporting", "contradicting", "neutral"],
    "additionalProperties": False,
}

FRIENDLY_SOURCE_NAMES = {
    'wikipedia.org': 'Wikipedia',
    'britannica.com': 'Britannica',
    'nature.com': 'Nature',
    'science.org': 'Science',
    'nih.gov': 'NIH',
    'cdc.gov': 'CDC',
    'who.int': 'WHO',
    'nasa.gov': 'NASA',
    'reuters.com': 'Reuters',
    'apnews.com': 'AP News',
    'bbc.com': 'BBC',
    'nytimes.com': 'The New York Times',
    'wsj.com': 'The Wall Street Journal',
    'economist.com': 'The Economist',
    'scientificamerican.com': 'Scientific American',
    'youtube.com': 'YouTube',
}


class FactChecker:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        self.trusted_domains = [
            'wikipedia.org', 'britannica.com', 'nature.com', 'science.org',
            'nih.gov', 'cdc.gov', 'who.int', 'nasa.gov', 'edu',
            'reuters.com', 'apnews.com', 'bbc.com', 'nytimes.com',
            'wsj.com', 'economist.com', 'scientificamerican.com'
        ]

    def extract_real_url(self, duckduckgo_url):
        """Extract real URL from DuckDuckGo redirect"""
        try:
            if 'uddg=' in duckduckgo_url:
                uddg_param = duckduckgo_url.split('uddg=')[1]
                if '&' in uddg_param:
                    uddg_param = uddg_param.split('&')[0]
                real_url = unquote(uddg_param)
                return real_url
            return duckduckgo_url
        except Exception:
            return duckduckgo_url

    def fetch_article_content(self, url, max_chars=5000):
        """Fetch and extract main content from an article URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
                    tag.decompose()

                content = ""

                article_selectors = [
                    'article',
                    '[role="main"]',
                    '.article-content',
                    '.article-body',
                    '.story-body',
                    '.entry-content',
                    'main'
                ]

                for selector in article_selectors:
                    article_elem = soup.select_one(selector)
                    if article_elem:
                        paragraphs = article_elem.find_all('p')
                        content = ' '.join([p.get_text(strip=True) for p in paragraphs])
                        if len(content) > 200:
                            break

                if len(content) < 200:
                    paragraphs = soup.find_all('p')
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs])

                return content[:max_chars]
        except Exception as e:
            print(f"Error fetching article content from {url}: {e}")
            return ""

        return ""

    def search_google_scholar(self, query, limit=5):
        """Search Google Scholar for academic articles"""
        results = []
        try:
            url = f"https://scholar.google.com/scholar?q={quote_plus(query)}&hl=en"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                articles = soup.find_all('div', class_='gs_ri', limit=limit)

                for article in articles:
                    title_elem = article.find('h3', class_='gs_rt')
                    snippet_elem = article.find('div', class_='gs_rs')

                    if title_elem:
                        link_elem = title_elem.find('a')
                        url_link = link_elem.get('href', '') if link_elem else ''
                        title_text = title_elem.get_text(strip=True)
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''

                        results.append({
                            'source': 'Google Scholar',
                            'title': title_text,
                            'url': url_link,
                            'snippet': snippet,
                            'full_content': '',
                            'reliability_score': 9
                        })
        except Exception as e:
            print(f"Google Scholar search error: {e}")

        return results

    def search_wikipedia(self, query):
        """Search Wikipedia API"""
        results = []
        try:
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': query,
                'format': 'json',
                'srlimit': 3
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                searches = data.get('query', {}).get('search', [])

                for item in searches:
                    page_title = item.get('title', '')
                    wiki_url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"

                    content_params = {
                        'action': 'query',
                        'prop': 'extracts',
                        'exintro': True,
                        'explaintext': True,
                        'titles': page_title,
                        'format': 'json'
                    }

                    content_response = requests.get(url, params=content_params, timeout=10)
                    full_content = ""

                    if content_response.status_code == 200:
                        content_data = content_response.json()
                        pages = content_data.get('query', {}).get('pages', {})
                        for page_id, page_data in pages.items():
                            full_content = page_data.get('extract', '')[:5000]

                    results.append({
                        'source': 'Wikipedia',
                        'title': page_title,
                        'url': wiki_url,
                        'snippet': BeautifulSoup(item.get('snippet', ''), 'html.parser').get_text(),
                        'full_content': full_content,
                        'reliability_score': 8
                    })

                    time.sleep(0.3)

        except Exception as e:
            print(f"Wikipedia search error: {e}")

        return results

    def friendly_source_name(self, url):
        """Derive a human-readable site name (e.g. 'BBC', 'Reuters') from a URL"""
        try:
            netloc = urlparse(url).netloc.lower().split('@')[-1].split(':')[0]
            if netloc.startswith('www.'):
                netloc = netloc[4:]
            if not netloc:
                return 'Web'

            for domain, name in FRIENDLY_SOURCE_NAMES.items():
                if netloc == domain or netloc.endswith('.' + domain):
                    return name

            label = netloc.split('.')[0]
            return label.replace('-', ' ').replace('_', ' ').title()
        except Exception:
            return 'Web'

    def search_web(self, query, limit=5):
        """Search the open web (DuckDuckGo) for reputable news/reference articles"""
        results = []
        try:
            url = "https://html.duckduckgo.com/html/"
            response = requests.post(url, data={'q': query}, headers=self.headers, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                links = soup.find_all('a', class_='result__a', limit=limit)

                seen_urls = set()
                for link in links:
                    raw_url = link.get('href', '')
                    real_url = self.extract_real_url(raw_url)
                    title = link.get_text(strip=True)

                    if not real_url or not title or real_url in seen_urls:
                        continue
                    seen_urls.add(real_url)

                    reliability = 5
                    for trusted_domain in self.trusted_domains:
                        if trusted_domain in real_url.lower():
                            reliability = 8
                            break

                    full_content = self.fetch_article_content(real_url)

                    results.append({
                        'source': self.friendly_source_name(real_url),
                        'title': title,
                        'url': real_url,
                        'snippet': '',
                        'full_content': full_content,
                        'reliability_score': reliability
                    })
        except Exception as e:
            print(f"Web search error: {e}")

        return results

    def analyze_with_groq(self, claim, all_results):
        """Ask Groq's LLM to reason over the gathered sources and produce a verdict"""
        if not groq_client:
            return self._fallback_analysis(claim, all_results)

        digest_parts = []
        for i, r in enumerate(all_results):
            text = (r.get('full_content') or r.get('snippet') or '').strip()
            if not text:
                continue
            digest_parts.append(
                f"[Source {i + 1}] {r.get('source', 'Unknown')} "
                f"(reliability {r.get('reliability_score', 5)}/10)\n"
                f"Title: {r.get('title', '')}\n"
                f"URL: {r.get('url', '')}\n"
                f"Content: {text[:1500]}"
            )

        sources_block = "\n\n".join(digest_parts) if digest_parts else "No source content was retrieved."

        prompt = f"""You are a rigorous, impartial fact-checking analyst. Evaluate the claim below using ONLY the provided sources.

Claim: "{claim}"

Sources:
{sources_block}

Instructions:
- Weigh each source by its stated reliability and by how directly it addresses the claim.
- Classify each source's relevant stance as supporting, contradicting, or neutral/unclear with respect to the claim, then report the totals.
- Read casual, everyday claims the way a reasonable person would, not as a strict logical universal, UNLESS the claim itself uses absolute language ("all", "every", "always", "only", "never"). A generalization like "apples are red" or "the sky is blue" is describing a common/typical/iconic case, not asserting there are zero exceptions. Do not mark such a claim LIKELY_FALSE just because other variants exist (e.g. green apples, orange sunsets) — that only makes it LIKELY_FALSE if the stated case is actually rare, outdated, or misleading as commonly understood. For example: "apples are red" should be LIKELY_TRUE or at most DISPUTED (red is a common, iconic apple color), even though green and yellow apples also exist — it should NOT be LIKELY_FALSE.
- Be conservative: only choose LIKELY_TRUE or LIKELY_FALSE when the evidence clearly leans that way; use DISPUTED when sources conflict, and INSUFFICIENT_DATA when there isn't enough relevant evidence.
- confidence is an integer 0-100 reflecting how strong and consistent the evidence is.
- summary must be 2-4 sentences, written in plain language, explaining the reasoning behind the verdict and noting any caveats or disagreement between sources.
- supporting + contradicting + neutral should add up to the number of sources you were able to draw a conclusion from (it is fine if some sources are irrelevant and excluded).

Respond with JSON matching the required schema only."""

        try:
            data = self._call_groq_json(prompt)

            valid_verdicts = {'LIKELY_TRUE', 'LIKELY_FALSE', 'DISPUTED', 'INSUFFICIENT_DATA'}
            verdict = data.get('verdict', 'INSUFFICIENT_DATA')
            if verdict not in valid_verdicts:
                verdict = 'DISPUTED'

            confidence = int(data.get('confidence', 0))
            confidence = max(0, min(100, confidence))

            return {
                'verdict': verdict,
                'confidence': confidence,
                'summary': data.get('summary', '').strip() or 'Groq did not provide a summary for this claim.',
                'stats': {
                    'supporting': max(0, int(data.get('supporting', 0))),
                    'contradicting': max(0, int(data.get('contradicting', 0))),
                    'neutral': max(0, int(data.get('neutral', 0))),
                    'total': len(all_results)
                }
            }
        except Exception as e:
            print(f"Groq analysis error: {e}")
            return self._fallback_analysis(claim, all_results)

    def _call_groq_json(self, prompt):
        """Call Groq chat completions and return a parsed JSON dict.

        Tries strict JSON-schema structured output first (supported by the
        openai/gpt-oss models); falls back to plain JSON-object mode for
        models/configs that don't support schema-constrained output.
        """
        messages = [
            {
                "role": "system",
                "content": "You are a rigorous, impartial fact-checking analyst. Always respond with valid JSON only."
            },
            {"role": "user", "content": prompt}
        ]

        try:
            response = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "fact_check_analysis",
                        "strict": True,
                        "schema": ANALYSIS_JSON_SCHEMA,
                    },
                },
                temperature=0.1,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Groq structured output failed, falling back to JSON object mode: {e}")

        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return json.loads(response.choices[0].message.content)

    def _fallback_analysis(self, claim, all_results):
        """Safety net used only when Groq is unavailable or errors out"""
        if not all_results:
            return {
                'verdict': 'INSUFFICIENT_DATA',
                'confidence': 0,
                'summary': 'Not enough information found to verify this claim.',
                'stats': {'supporting': 0, 'contradicting': 0, 'neutral': 0, 'total': 0}
            }

        return {
            'verdict': 'INSUFFICIENT_DATA',
            'confidence': 0,
            'summary': (
                f"Found {len(all_results)} source(s) but the Groq analysis engine is "
                f"unavailable right now (check GROQ_API_KEY), so no verdict could be computed."
            ),
            'stats': {'supporting': 0, 'contradicting': 0, 'neutral': len(all_results), 'total': len(all_results)}
        }

    def check_claim(self, claim):
        """Main method to check a claim"""
        print(f"\n{'=' * 60}")
        print(f"Checking claim: {claim}")
        print(f"{'=' * 60}\n")

        all_results = []

        print("Searching Wikipedia...")
        wiki_results = self.search_wikipedia(claim)
        all_results.extend(wiki_results)

        print("Searching academic sources (Google Scholar)...")
        scholar_results = self.search_google_scholar(claim)
        all_results.extend(scholar_results)

        print("Searching news/web sources...")
        web_results = self.search_web(claim)
        all_results.extend(web_results)

        print(f"\nFound {len(all_results)} total sources")

        analysis = self.analyze_with_groq(claim, all_results)

        return {
            'claim': claim,
            'analysis': analysis,
            'sources': all_results,
            'timestamp': datetime.now().isoformat(),
            'source_count': len(all_results)
        }


# Initialize fact checker
fact_checker = FactChecker()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'groq_configured': groq_client is not None
    })


@app.route('/api/verify', methods=['POST'])
def verify_claim():
    """Main endpoint to verify a claim (original format)"""
    try:
        data = request.get_json()

        if not data or 'claim' not in data:
            return jsonify({'error': 'Missing claim in request body'}), 400

        claim = data['claim'].strip()

        if not claim:
            return jsonify({'error': 'Claim cannot be empty'}), 400

        if len(claim) < 3:
            return jsonify({'error': 'Claim too short. Please provide a meaningful statement.'}), 400

        result = fact_checker.check_claim(claim)

        return jsonify(result), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/submit', methods=['POST'])
def submit_claim():
    """New endpoint to verify a claim with simplified input/output format"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No JSON data received'}), 400

        if 'message' not in data:
            return jsonify({'error': 'Missing "message" field in request body'}), 400

        message = data['message'].strip()

        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400

        if len(message) < 3:
            return jsonify({'error': 'Message too short. Please provide at least 3 characters.'}), 400

        result = fact_checker.check_claim(message)

        formatted_result = {
            'topic': result['claim'],
            'resolution': result['analysis']['verdict'],
            'confidence': f"{result['analysis']['confidence']}%",
            'supporting': result['analysis']['stats']['supporting'],
            'contradicting': result['analysis']['stats']['contradicting'],
            'neutral': result['analysis']['stats']['neutral'],
            'sources': [
                {
                    'website': source.get('source', 'Unknown'),
                    'body': source.get('snippet', ''),
                    'link': source.get('url', '')
                }
                for source in result['sources']
            ]
        }

        return jsonify(formatted_result), 200

    except Exception as e:
        print(f"Error in /submit: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/sources', methods=['GET'])
def get_sources():
    """Endpoint to list available sources"""
    return jsonify({
        'sources': [
            {'name': 'Google Scholar', 'type': 'academic', 'status': 'active', 'reliability': 9},
            {'name': 'Wikipedia', 'type': 'encyclopedia', 'status': 'active', 'reliability': 8},
            {'name': 'Web Search', 'type': 'search', 'status': 'active', 'reliability': 6},
            {
                'name': 'Groq AI Analysis',
                'type': 'ai-reasoning',
                'status': 'active' if groq_client else 'unavailable',
                'reliability': 9
            }
        ]
    }), 200


if __name__ == '__main__':
    print("Fact Checker API Starting...")
    print("Available endpoints:")
    print("   - POST /submit         - Verify a claim (new format)")
    print("   - POST /api/verify     - Verify a claim (original format)")
    print("   - GET  /api/health     - Health check")
    print("   - GET  /api/sources    - List sources")
    app.run(debug=True, host='0.0.0.0', port=5050)
