#!/usr/bin/env python3
"""
Quick test script for NoSubvo backend API
"""

import requests
import json

BASE_URL = "http://localhost:5001"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing /health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Status: {response.status_code}")
        print(f"📄 Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_chunk():
    """Test chunking endpoint"""
    print("\n🔍 Testing /chunk endpoint...")
    
    test_text = """
    Open your eyes in sea water and it is difficult to see much more than 
    a murky, bleary green colour. Without specialised equipment humans would 
    be lost in these deep sea habitats, so how do fish make it seem so easy?
    """
    
    try:
        response = requests.post(
            f"{BASE_URL}/chunk",
            json={"text": test_text},
            headers={"Content-Type": "application/json"}
        )
        print(f"✅ Status: {response.status_code}")
        data = response.json()
        print(f"📊 Chunks found: {data['chunk_count']}")
        print(f"📝 First 5 chunks:")
        for i, chunk in enumerate(data['chunks'][:5], 1):
            print(f"   {i}. {chunk}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 NoSubvo Backend API Test")
    print("=" * 50)
    print("\n⚠️  Make sure backend is running: python backend.py\n")
    
    health_ok = test_health()
    chunk_ok = test_chunk()
    
    print("\n" + "=" * 50)
    if health_ok and chunk_ok:
        print("✅ All tests passed!")
        print("🎉 Backend is working correctly!")
    else:
        print("❌ Some tests failed")
        print("💡 Make sure backend is running on port 5001")

if __name__ == "__main__":
    main()


