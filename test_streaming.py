#!/usr/bin/env python3
"""Test script to verify Cohere streaming is working"""

import requests
import json

def test_streaming():
    url = "http://localhost:8000/ask?stream=true"
    
    payload = {
        "question": "What is salinity?"
    }
    
    print("🔄 Testing streaming endpoint...")
    print(f"URL: {url}")
    print(f"Payload: {payload}\n")
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            stream=True
        )
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return
        
        print("✅ Stream connected! Receiving tokens:\n")
        print("-" * 80)
        
        accumulated_text = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        if data.get('chunk') and not data.get('done'):
                            chunk = data['chunk']
                            accumulated_text += chunk
                            print(chunk, end='', flush=True)
                        elif data.get('done'):
                            print("\n" + "-" * 80)
                            print("✅ Stream completed!")
                            break
                    except json.JSONDecodeError as e:
                        print(f"\n❌ JSON parse error: {e}")
                        print(f"Line: {line_str}")
        
        print(f"\n\n📊 Final accumulated text ({len(accumulated_text)} chars):")
        print(accumulated_text)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_streaming()
