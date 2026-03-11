import requests

BASE_URL = "http://localhost:5000"

def test_health_endpoint():
    response = requests.get(f"{BASE_URL}/api/health")
    assert response.status_code == 200