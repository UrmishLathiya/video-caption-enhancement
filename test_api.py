import requests

try:
    response = requests.get('http://localhost:8000/health', timeout=5)
    print(f"API Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test root endpoint too
    root_response = requests.get('http://localhost:8000/', timeout=5)
    print(f"Root Status: {root_response.status_code}")
    print(f"Root Response: {root_response.json()}")
    
    print("\n✅ API is working correctly!")
    
except requests.exceptions.ConnectionError:
    print("❌ Could not connect to API. Make sure the backend is running.")
except Exception as e:
    print(f"❌ Error testing API: {e}")
