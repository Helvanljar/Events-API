import requests
import time

BASE_URL = "http://localhost:5000"


def unique_user():
    timestamp = int(time.time() * 1000)
    username = f"user{timestamp}"
    email = f"user{timestamp}@test.com"
    password = "Password123!"
    return username, email, password


def register_user(username, email, password):
    data = {
        "username": username,
        "email": email,
        "password": password
    }
    return requests.post(f"{BASE_URL}/api/auth/register", json=data)


def login_user(username, password):
    data = {
        "username": username,
        "password": password
    }
    return requests.post(f"{BASE_URL}/api/auth/login", json=data)


def create_authenticated_user_and_token():
    username, email, password = unique_user()

    register_response = register_user(username, email, password)
    assert register_response.status_code == 201

    login_response = login_user(username, password)
    assert login_response.status_code == 200

    token = login_response.json().get("token") or login_response.json().get("access_token")
    return username, email, password, token


def create_event(token, is_public=True):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    event_data = {
        "title": f"Test Event {int(time.time() * 1000)}",
        "description": "Testing event",
        "date": "2030-01-01T18:00:00",
        "location": "Berlin",
        "capacity": 10,
        "is_public": is_public
    }

    return requests.post(f"{BASE_URL}/api/events", json=event_data, headers=headers)


def get_event_id(response):
    data = response.json()

    if "id" in data:
        return data["id"]

    if "event" in data and "id" in data["event"]:
        return data["event"]["id"]

    return None


def test_health_endpoint():
    response = requests.get(f"{BASE_URL}/api/health")
    assert response.status_code == 200


def test_register_user_creates_new_user():
    username, email, password = unique_user()
    response = register_user(username, email, password)
    assert response.status_code == 201


def test_login_returns_jwt_token():
    username, email, password = unique_user()

    register_response = register_user(username, email, password)
    assert register_response.status_code == 201

    response = login_user(username, password)

    assert response.status_code == 200
    assert "token" in response.json() or "access_token" in response.json()


def test_create_public_event_requires_auth_and_succeeds_with_token():
    username, email, password, token = create_authenticated_user_and_token()

    response = create_event(token, is_public=True)

    assert response.status_code == 201


def test_duplicate_registration_fails():
    username, email, password = unique_user()

    first = register_user(username, email, password)
    second = register_user(username, email, password)

    assert first.status_code == 201
    assert second.status_code in [400, 409]


def test_create_event_without_auth_fails():
    event_data = {
        "title": "Unauthorized Event",
        "description": "Should fail",
        "date": "2030-01-01T18:00:00",
        "location": "Berlin",
        "capacity": 5,
        "is_public": True
    }

    response = requests.post(f"{BASE_URL}/api/events", json=event_data)

    assert response.status_code in [401, 403]


def test_rsvp_public_event_succeeds_with_token():
    username, email, password, token = create_authenticated_user_and_token()

    create_response = create_event(token, is_public=True)
    assert create_response.status_code == 201

    event_id = get_event_id(create_response)
    assert event_id is not None

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(
        f"{BASE_URL}/api/rsvps/event/{event_id}",
        json={"attending": True},
        headers=headers
    )

    assert response.status_code in [200, 201]


def test_rsvp_private_event_without_auth_fails():
    username, email, password, token = create_authenticated_user_and_token()

    create_response = create_event(token, is_public=False)
    assert create_response.status_code == 201

    event_id = get_event_id(create_response)
    assert event_id is not None

    response = requests.post(
        f"{BASE_URL}/api/rsvps/event/{event_id}",
        json={"attending": True}
    )

    assert response.status_code in [401, 403]