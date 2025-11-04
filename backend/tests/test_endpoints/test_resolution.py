import requests

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000"

#---------------------------------
# Resolution Endpoints Tests
#---------------------------------

print("=" * 60)
print("Testing Resolution Endpoints")
print("=" * 60)

# Test 1: Process ticket resolution
print("\n[TEST 1] Testing /resolution/process endpoint...")
resolution_data = {
    "ticket_title": "Cannot access VPN",
    "ticket_description": "I'm unable to connect to the company VPN. Getting connection timeout error.",
    "service_category": "Network",
    "service_subcategory": "VPN",
    "top_k": 3
}

response = requests.post(
    f"{BASE_URL}/resolution/process",
    json=resolution_data
)

if response.status_code == 200:
    result = response.json()
    print(f"✓ Status: {response.status_code}")
    print(f"  Classification: {result.get('classification')}")
    print(f"  Predicted Team: {result.get('predicted_team')}")
    print(f"  Team Confidence: {result.get('team_confidence')}")
    print(f"  Response: {result.get('response')}")
    print(f"  Similar Tickets Found: {len(result.get('similar_replies', []))}")
else:
    print(f"✗ Error {response.status_code}: {response.text}")

print("\n" + "-" * 60)

# Test 2: Save feedback (resolved ticket)
print("\n[TEST 2] Testing /resolution/feedback endpoint...")
feedback_data = {
    "ticket_title": "Password reset needed",
    "ticket_description": "User needs password reset for their account",
    "edited_response": "Hello! I've reset your password. Please check your email for the temporary password. Let me know if you need further assistance.",
    "predicted_team": "IT Support",
    "predicted_classification": "password_reset",
    "service_name": "Account Management",
    "service_subcategory": "Password"
}

response = requests.post(
    f"{BASE_URL}/resolution/feedback",
    json=feedback_data
)

if response.status_code == 200:
    result = response.json()
    print(f"✓ Status: {response.status_code}")
    print(f"  Success: {result.get('success')}")
    print(f"  Message: {result.get('message')}")
    print(f"  Ticket Ref: {result.get('ticket_ref')}")
    print(f"  New KB Size: {result.get('new_kb_size')}")
    print(f"  Embedding Added Incrementally: {result.get('embedding_added_incrementally')}")
else:
    print(f"✗ Error {response.status_code}: {response.text}")

print("\n" + "-" * 60)

# Test 3: Test with minimal data (only title)
print("\n[TEST 3] Testing /resolution/process with minimal data...")
minimal_data = {
    "ticket_title": "Printer not working",
    "top_k": 2
}

response = requests.post(
    f"{BASE_URL}/resolution/process",
    json=minimal_data
)

if response.status_code == 200:
    result = response.json()
    print(f"✓ Status: {response.status_code}")
    print(f"  Classification: {result.get('classification')}")
    print(f"  Predicted Team: {result.get('predicted_team')}")
else:
    print(f"✗ Error {response.status_code}: {response.text}")

print("\n" + "-" * 60)

# Test 4: Error case - no title or description
print("\n[TEST 4] Testing error handling (no title/description)...")
invalid_data = {
    "top_k": 5
}

response = requests.post(
    f"{BASE_URL}/resolution/process",
    json=invalid_data
)

print(f"Status: {response.status_code}")
if response.status_code == 422:
    print(f"✓ Validation error handled correctly")
    print(f"  Error: {response.json()}")
else:
    print(f"Response: {response.text}")

print("\n" + "-" * 60)

# Test 5: Rebuild embeddings (local operation, no external API)
print("\n[TEST 5] Testing /resolution/rebuild-embeddings...")
print("Note: This uses local SentenceTransformer + FAISS, no external API")
response = requests.post(f"{BASE_URL}/resolution/rebuild-embeddings")

if response.status_code == 200:
    result = response.json()
    print(f"✓ Status: {response.status_code}")
    print(f"  Rebuilt: {result.get('rebuilt')}")
    print(f"  Records: {result.get('records')}")
    print(f"  Embedding Dimension: {result.get('embedding_dim')}")
    print(f"  Cache Saved: {result.get('cache_saved')}")
else:
    print(f"✗ Error {response.status_code}: {response.text}")

print("\n" + "=" * 60)
print("Resolution Endpoints Testing Complete")
print("=" * 60)

