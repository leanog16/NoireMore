from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from urllib.parse import quote_plus, unquote
import time
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

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
        except:
            return duckduckgo_url
    
    def fetch_article_content(self, url, max_chars=5000):
        """Fetch and extract main content from an article URL"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                    script.decompose()
                
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
    
    def search_news_api(self, query, limit=8):
        """Search for news articles across multiple news sites"""
        results = []
        
        news_queries = [
            ('site:reuters.com', 'Reuters'),
            ('site:apnews.com', 'Associated Press'),
            ('site:bbc.com', 'BBC News'),
            ('site:npr.org', 'NPR'),
        ]
        
        try:
            for site_query, source_name in news_queries:
                search_query = f"{query} {site_query}"
                url = f"https://html.duckduckgo.com/html/?q={quote_plus(search_query)}"
                response = requests.get(url, headers=self.headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    search_results = soup.find_all('div', class_='result', limit=2)
                    
                    for result in search_results:
                        title_elem = result.find('a', class_='result__a')
                        snippet_elem = result.find('a', class_='result__snippet')
                        
                        if title_elem:
                            raw_url = title_elem.get('href', '')
                            url_link = self.extract_real_url(raw_url)
                            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ''
                            
                            print(f"Fetching content from: {url_link}")
                            full_content = self.fetch_article_content(url_link)
                            
                            results.append({
                                'source': source_name,
                                'title': title_elem.get_text(strip=True),
                                'url': url_link,
                                'snippet': snippet,
                                'full_content': full_content,
                                'reliability_score': 9
                            })
                            
                            time.sleep(1)
                
                time.sleep(0.5)
                
        except Exception as e:
            print(f"News API search error: {e}")
        
        return results
    
    def search_duckduckgo(self, query, limit=5):
        """Search using DuckDuckGo HTML scraping"""
        results = []
        try:
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                search_results = soup.find_all('div', class_='result', limit=limit)
                
                for result in search_results:
                    title_elem = result.find('a', class_='result__a')
                    snippet_elem = result.find('a', class_='result__snippet')
                    
                    if title_elem:
                        raw_url = title_elem.get('href', '')
                        url_link = self.extract_real_url(raw_url)
                        
                        reliability = 5
                        for trusted_domain in self.trusted_domains:
                            if trusted_domain in url_link.lower():
                                reliability = 8
                                break
                        
                        full_content = ""
                        if reliability >= 8:
                            print(f"Fetching content from: {url_link}")
                            full_content = self.fetch_article_content(url_link)
                            time.sleep(1)
                        
                        results.append({
                            'source': 'Web Search',
                            'title': title_elem.get_text(strip=True),
                            'url': url_link,
                            'snippet': snippet_elem.get_text(strip=True) if snippet_elem else '',
                            'full_content': full_content,
                            'reliability_score': reliability
                        })
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
        
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
    
    def extract_claim_keywords(self, claim):
        """Extract the main subject/keywords from the claim"""
        stop_words = {'the', 'is', 'are', 'was', 'were', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 
                      'of', 'and', 'or', 'but', 'that', 'this', 'these', 'those', 'it', 'be'}
        claim_lower = claim.lower()
        words = re.findall(r'\b\w+\b', claim_lower)
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        return keywords
    
    def find_claim_context_sentences(self, claim, content):
        """Find sentences in content that actually discuss the claim subject"""
        claim_keywords = self.extract_claim_keywords(claim)
        content_lower = content.lower()
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', content_lower)
        
        relevant_sentences = []
        for sentence in sentences:
            # Check if sentence contains at least 2 claim keywords
            keyword_count = sum(1 for keyword in claim_keywords if keyword in sentence)
            if keyword_count >= min(2, len(claim_keywords)):
                relevant_sentences.append(sentence.strip())
        
        return relevant_sentences
    
    def analyze_results(self, claim, all_results):
        """Analyze only sentences that actually discuss the claim"""
        if not all_results:
            return {
                'verdict': 'INSUFFICIENT_DATA',
                'confidence': 0,
                'summary': 'Not enough information found to verify this claim.',
                'stats': {
                    'supporting': 0,
                    'contradicting': 0,
                    'neutral': 0,
                    'total': 0
                }
            }
        
        # Agreement/support patterns - MUST be about the claim
        support_patterns = [
            r'\b(is|are|was|were)\s+(true|correct|accurate|valid|confirmed|verified)\b',
            r'\b(proves?|shows?|demonstrates?|confirms?|validates?)\s+that\b',
            r'\b(evidence|research|studies|data)\s+(shows?|suggests?|indicates?|proves?)\b',
            r'\b(indeed|in fact|actually|truly)\b',
            r'\b(established|proven|documented)\s+(fact|truth)\b'
        ]
        
        # Disagreement/contradiction patterns
        contradict_patterns = [
            r'\b(is|are|was|were)\s+(not|false|incorrect|inaccurate|untrue|wrong|fake)\b',
            r'\b(no evidence|lacks evidence|unproven|unverified|unfounded|baseless)\b',
            r'\b(myth|hoax|misconception|misinformation|disinformation)\b',
            r'\b(debunked|refuted|disproven|contradicted|disputed)\b',
            r'\b(however|but|although|despite)\b.*\b(not|false|incorrect)\b',
            r'\bnot\s+(true|accurate|correct|valid|proven)\b'
        ]
        
        # Uncertainty patterns
        uncertainty_patterns = [
            r'\b(unclear|unknown|uncertain|disputed|controversial|debated)\b',
            r'\b(may|might|could|possibly|perhaps|potentially)\s+be\b',
            r'\b(some|many|few)\s+(believe|think|claim|argue)\b',
            r'\b(mixed|conflicting|varying)\s+(evidence|views|opinions)\b'
        ]
        
        weighted_positive = 0
        weighted_negative = 0
        weighted_neutral = 0
        
        supporting_count = 0
        contradicting_count = 0
        neutral_count = 0
        
        claim_keywords = self.extract_claim_keywords(claim)
        print(f"Claim keywords: {claim_keywords}")
        
        for result in all_results:
            text_to_analyze = result.get('full_content', '') or result.get('snippet', '')
            
            # Find sentences that actually discuss the claim
            relevant_sentences = self.find_claim_context_sentences(claim, text_to_analyze)
            
            if not relevant_sentences:
                print(f"Source: {result.get('source')} - No relevant sentences found")
                neutral_count += 1
                continue
            
            print(f"\nSource: {result.get('source')}")
            print(f"Found {len(relevant_sentences)} relevant sentences")
            
            reliability = result.get('reliability_score', 5)
            weight = reliability / 10.0
            
            # Analyze only the relevant sentences
            combined_relevant = ' '.join(relevant_sentences)
            
            support_score = 0
            contradict_score = 0
            uncertain_score = 0
            
            # Check for support patterns
            for pattern in support_patterns:
                matches = re.findall(pattern, combined_relevant, re.IGNORECASE)
                support_score += len(matches)
            
            # Check for contradiction patterns
            for pattern in contradict_patterns:
                matches = re.findall(pattern, combined_relevant, re.IGNORECASE)
                contradict_score += len(matches)
            
            # Check for uncertainty patterns
            for pattern in uncertainty_patterns:
                matches = re.findall(pattern, combined_relevant, re.IGNORECASE)
                uncertain_score += len(matches)
            
            print(f"  Support patterns: {support_score}")
            print(f"  Contradict patterns: {contradict_score}")
            print(f"  Uncertainty patterns: {uncertain_score}")
            
            # Determine stance
            if uncertain_score >= 2:
                weighted_neutral += weight
                neutral_count += 1
                print(f"  → NEUTRAL (uncertainty)")
            elif contradict_score > support_score * 1.5:
                weighted_negative += weight * (1 + contradict_score * 0.2)
                contradicting_count += 1
                print(f"  → CONTRADICTING")
            elif support_score > contradict_score * 1.5:
                weighted_positive += weight * (1 + support_score * 0.2)
                supporting_count += 1
                print(f"  → SUPPORTING")
            elif support_score == 0 and contradict_score == 0:
                # No clear stance found in relevant sentences
                weighted_neutral += weight * 0.5
                neutral_count += 1
                print(f"  → NEUTRAL (no clear stance)")
            else:
                # Mixed signals
                weighted_neutral += weight * 0.7
                neutral_count += 1
                print(f"  → NEUTRAL (mixed)")
        
        total = len(all_results)
        total_weight = weighted_positive + weighted_negative + weighted_neutral
        
        print(f"\n{'='*60}")
        print(f"Final weights - Pos: {weighted_positive:.2f}, Neg: {weighted_negative:.2f}, Neutral: {weighted_neutral:.2f}")
        print(f"{'='*60}")
        
        # Calculate verdict - now MUCH more conservative
        if total_weight == 0:
            verdict = 'INSUFFICIENT_DATA'
            confidence = 0
        elif weighted_negative > weighted_positive * 3:
            verdict = 'LIKELY_FALSE'
            confidence = min(90, int((weighted_negative / total_weight) * 100))
        elif weighted_positive > weighted_negative * 3:
            verdict = 'LIKELY_TRUE'
            confidence = min(90, int((weighted_positive / total_weight) * 100))
        elif weighted_neutral > (weighted_positive + weighted_negative):
            verdict = 'DISPUTED'
            confidence = 45
        elif weighted_positive > weighted_negative * 1.5:
            verdict = 'LIKELY_TRUE'
            confidence = min(70, int((weighted_positive / total_weight) * 85))
        elif weighted_negative > weighted_positive * 1.5:
            verdict = 'LIKELY_FALSE'
            confidence = min(70, int((weighted_negative / total_weight) * 85))
        else:
            verdict = 'DISPUTED'
            confidence = 50
        
        summary = f"Analyzed {total} sources focusing on claim-relevant content: {supporting_count} supporting, {contradicting_count} contradicting, {neutral_count} neutral/unclear."
        
        return {
            'verdict': verdict,
            'confidence': confidence,
            'summary': summary,
            'stats': {
                'supporting': supporting_count,
                'contradicting': contradicting_count,
                'neutral': neutral_count,
                'total': total
            }
        }
    
    def check_claim(self, claim):
        """Main method to check a claim"""
        print(f"\n{'='*60}")
        print(f"Checking claim: {claim}")
        print(f"{'='*60}\n")
        
        all_results = []
        
        print("Searching Wikipedia...")
        wiki_results = self.search_wikipedia(claim)
        all_results.extend(wiki_results)
        time.sleep(0.5)
        
        print("Searching news sources...")
        news_results = self.search_news_api(claim)
        all_results.extend(news_results)
        time.sleep(0.5)
        
        print("Searching academic sources...")
        scholar_results = self.search_google_scholar(claim)
        all_results.extend(scholar_results)
        time.sleep(0.5)
        
        print("Searching web...")
        ddg_results = self.search_duckduckgo(claim, limit=3)
        all_results.extend(ddg_results)
        
        print(f"\nFound {len(all_results)} total sources")
        
        analysis = self.analyze_results(claim, all_results)
        
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
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

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
            {'name': 'Reuters', 'type': 'news', 'status': 'active', 'reliability': 9},
            {'name': 'Associated Press', 'type': 'news', 'status': 'active', 'reliability': 9},
            {'name': 'BBC News', 'type': 'news', 'status': 'active', 'reliability': 9},
            {'name': 'NPR', 'type': 'news', 'status': 'active', 'reliability': 9},
            {'name': 'Wikipedia', 'type': 'encyclopedia', 'status': 'active', 'reliability': 8},
            {'name': 'Web Search', 'type': 'search', 'status': 'active', 'reliability': 5}
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