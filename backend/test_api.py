#!/usr/bin/env python3
"""
Test script for the Fact Checker API
Run this after starting the server to test endpoints
"""

import requests
import json
from time import sleep

BASE_URL = "http://localhost:5000"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def test_health():
    """Test the health check endpoint"""
    print_section("Testing Health Check")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_sources():
    """Test the sources endpoint"""
    print_section("Testing Sources List")
    try:
        response = requests.get(f"{BASE_URL}/api/sources")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_submit_endpoint(message):
    """Test the new /submit endpoint with message format"""
    print_section(f"Testing /submit Endpoint: '{message}'")
    try:
        response = requests.post(
            f"{BASE_URL}/submit",
            json={"message": message},
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📋 Topic: {data['topic']}")
            print(f"⚖️  Resolution: {data['resolution']}")
            print(f"📊 Confidence: {data['confidence']}")
            print(f"\n📈 Statistics:")
            print(f"   Supporting: {data['supporting']}")
            print(f"   Contradicting: {data['contradicting']}")
            print(f"   Neutral: {data['neutral']}")
            print(f"\n📚 Total Sources: {len(data['sources'])}")
            
            print("\n🔍 Sample Sources:")
            for i, source in enumerate(data['sources'][:3], 1):
                print(f"\n{i}. {source['website']}")
                print(f"   Link: {source['link']}")
                print(f"   Body: {source['body'][:100]}...")
            
            print("\n\n📄 Full JSON Response:")
            print(json.dumps(data, indent=2))
        else:
            print(f"Response: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_verify_claim(claim):
    """Test claim verification (original endpoint)"""
    print_section(f"Testing Original /api/verify: '{claim}'")
    try:
        response = requests.post(
            f"{BASE_URL}/api/verify",
            json={"claim": claim},
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📋 Claim: {data['claim']}")
            print(f"\n⚖️  Verdict: {data['analysis']['verdict']}")
            print(f"📊 Confidence: {data['analysis']['confidence']}%")
            print(f"📝 Summary: {data['analysis']['summary']}")
            print(f"\n📚 Sources Found: {data['source_count']}")
            
            print("\n🔍 Top Sources:")
            for i, source in enumerate(data['sources'][:3], 1):
                print(f"\n{i}. {source['source']} - {source['title']}")
                print(f"   URL: {source['url']}")
                print(f"   Snippet: {source['snippet'][:100]}...")
        else:
            print(f"Response: {response.json()}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n🚀 Fact Checker API Test Suite")
    print("="*60)
    print("Make sure the server is running on http://localhost:5000")
    print("="*60)
    
    input("\nPress Enter to start tests...")
    
    # Test 1: Health Check
    health_ok = test_health()
    
    if not health_ok:
        print("\n❌ Server is not responding. Make sure to run 'python app.py' first!")
        return
    
    sleep(1)
    
    # Test 2: Sources
    test_sources()
    sleep(1)
    
    # Test 3: Test NEW /submit endpoint
    print("\n" + "="*60)
    print("  TESTING NEW /submit ENDPOINT")
    print("="*60)
    
    test_messages = [
        "The Earth is flat",
        "The Eiffel Tower was completed in 1889",
        "Python is a programming language"
    ]
    
    for message in test_messages:
        test_submit_endpoint(message)
        sleep(2)  # Wait between tests to avoid rate limiting
    
    # Test 4: Test ORIGINAL /api/verify endpoint
    print("\n" + "="*60)
    print("  TESTING ORIGINAL /api/verify ENDPOINT")
    print("="*60)
    
    test_verify_claim("Water boils at 100 degrees Celsius at sea level")
    sleep(2)
    
    print_section("Tests Complete!")
    print("✅ All tests finished. Check the results above.\n")

if __name__ == "__main__":
    main()
