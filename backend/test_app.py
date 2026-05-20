import requests
import json
import os

BASE_URL = "http://localhost:8000"

def test_health():
    print("Testing health check...")
    r = requests.get(f"{BASE_URL}/")
    print(f"Status: {r.status_code}, Body: {r.json()}")
    return r.status_code == 200

def test_upload():
    print("\nTesting file upload...")
    test_file = "test_doc.txt"
    if not os.path.exists(test_file):
        with open(test_file, "w") as f:
            f.write("Artificial intelligence is the intelligence of machines.")
    
    with open(test_file, "rb") as f:
        r = requests.post(f"{BASE_URL}/upload", files=[("files", (test_file, f, "text/plain"))])
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        print(f"Response: {r.json()}")
    else:
        print(f"Error: {r.text}")
    return r.status_code == 200

def test_ask():
    print("\nTesting chat /ask...")
    payload = {"question": "What is AI?"}
    r = requests.post(f"{BASE_URL}/ask", json=payload)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        ans = r.json()
        print(f"Answer: {ans['answer']}")
        print(f"Source count: {ans['source_count']}")
    else:
        print(f"Error: {r.text}")
    return r.status_code == 200

if __name__ == "__main__":
    try:
        if test_health():
            if test_upload():
                test_ask()
    except Exception as e:
        print(f"Test failed with exception: {e}")
