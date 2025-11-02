import pytest
import uuid
from datetime import datetime
from client import EventAPI  # Assume your implementation is saved in `event_api.py`


@pytest.fixture(scope="module")
def api_client():
    """Fixture to initialize the EventAPI client."""
    private_key_path = "data/priv.key"
    public_key_path = "data/pub.key"
    base_url = "http://localhost:8000"
    return EventAPI(private_key_path, public_key_path, base_url)


@pytest.fixture(scope="module")
def event_payload():
    """Fixture to provide payload for creating an event."""
    return {
        "event_id": str(uuid.uuid4()),
        "event_name": "Pytest Conference",
        "event_description": "Testing conference for developers.",
        "tickets": 100,
        "start": int(datetime(2025, 12, 1, 9, 0).timestamp()),
        "end": int(datetime(2025, 12, 1, 17, 0).timestamp()),
        "private": False,
    }


class TestEventWorkflow:
    event_id = None
    ticket_id = None

    def test_create_event(self, api_client, event_payload):
        """Test the event creation workflow."""
        response = api_client.create_event(**event_payload)
        assert response.status_code == 200
        response_data = response.json()
        assert "id" in response_data["data"]
        TestEventWorkflow.event_id = response_data["data"]["content"]["event_id"]
        assert TestEventWorkflow.event_id is not None

    def test_search_event(self, api_client):
        """Test the event search workflow."""
        text = "Pytest Conference"
        response = api_client.search_event(text=text, limit=1, mode="text")
        assert response.status_code == 200
        response_data = response.json()
        print("response_data for search", response_data)
        assert len(response_data) > 0
        assert text in response_data["data"]["content"]["events"][0]["name"]

    def test_register_user(self, api_client):
        """Test the user registration workflow."""
        assert TestEventWorkflow.event_id is not None, "Event ID is not set."
        response = api_client.register_user(
            event_id=TestEventWorkflow.event_id, content="John Doe"
        )
        assert response.status_code == 200
        response_data = response.json()
        print("response_data_from")
        # assert response_data["status"] == "success"
        TestEventWorkflow.ticket_id = response_data["data"]["content"]["ticket"]

    def test_cancel_ticket(self, api_client):
        """Test the ticket cancellation workflow."""
        assert TestEventWorkflow.event_id is not None, "Event ID is not set."
        assert TestEventWorkflow.ticket_id is not None, "Ticket ID is not set."
        response = api_client.cancel_ticket(
            event_id=TestEventWorkflow.event_id, ticket=TestEventWorkflow.ticket_id
        )
        print("response from cancel", response)
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "canceled"

    def test_full_event_workflow(self, api_client, event_payload):
        """Test the full event workflow from creation to cancellation."""
        # Create a new event for this specific test
        create_response = api_client.create_event(**event_payload)
        assert create_response.status_code == 201
        event_id = create_response.json()["content"]["event"]["id"]

        # Register a user for the event
        register_response = api_client.register_user(event_id=event_id, content="Alice")
        assert register_response.status_code == 200

        # Cancel the user's ticket
        ticket_id = register_response.json()["content"]["ticket_id"]
        cancel_response = api_client.cancel_ticket(event_id=event_id, ticket=ticket_id)
        assert cancel_response.status_code == 200
