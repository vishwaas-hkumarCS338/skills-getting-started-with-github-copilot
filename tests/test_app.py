from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirects_to_static_index():
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_details():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert expected_activity in response.json()
    assert "participants" in response.json()[expected_activity]


def test_signup_adds_participant():
    # Arrange
    activity_name = "Soccer Club"
    email = "student@example.com"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email in activities[activity_name]["participants"]
    assert response.json()["message"] == (
        f"Signed up {email} for {activity_name}"
    )


def test_signup_rejects_unknown_activity():
    # Arrange
    activity_name = "Unknown Club"
    email = "student@example.com"

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant():
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{quote(activity_name)}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"


def test_signup_requires_email():
    # Arrange
    activity_name = "Soccer Club"

    # Act
    response = client.post(f"/activities/{quote(activity_name)}/signup")

    # Assert
    assert response.status_code == 422


def test_unregister_removes_participant():
    # Arrange
    activity_name = "Track and Field"
    email = "student+track@example.com"
    activities[activity_name]["participants"].append(email)

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/participants/{quote(email)}"
    )

    # Assert
    assert response.status_code == 200
    assert email not in activities[activity_name]["participants"]
    assert response.json()["message"] == (
        f"Unregistered {email} from {activity_name}"
    )


def test_unregister_rejects_unknown_activity():
    # Arrange
    activity_name = "Unknown Club"
    email = "student@example.com"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/participants/{quote(email)}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_unregistered_participant():
    # Arrange
    activity_name = "Soccer Club"
    email = "student@example.com"

    # Act
    response = client.delete(
        f"/activities/{quote(activity_name)}/participants/{quote(email)}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up"