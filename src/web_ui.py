import streamlit as st
from datetime import datetime
import uuid
from client import EventAPI  # Import your EventAPI class

# Initialize the API client
api_client = EventAPI(
    private_key_path="priv.demo.key",
    public_key_path="pub.demo.key",
    base_url="http://localhost:8000",
)

# Streamlit App Layout
st.title("Event Ticketing System")

# Navigation
menu = st.sidebar.radio(
    "Navigation",
    ["Create Event", "Search Events", "Register for Event", "Redeem/Cancel Ticket"],
)

if menu == "Create Event":
    st.header("Create a New Event")
    event_name = st.text_input("Event Name")
    event_description = st.text_area("Event Description")
    tickets = st.number_input("Number of Tickets", min_value=1, step=1)
    start_date = st.date_input("Event Start Date")
    start_time = st.time_input("Event Start Time")
    end_date = st.date_input("Event End Date")
    end_time = st.time_input("Event End Time")
    private = st.checkbox("Private Event")

    if st.button("Create Event"):
        start_timestamp = int(datetime.combine(start_date, start_time).timestamp())
        end_timestamp = int(datetime.combine(end_date, end_time).timestamp())

        response = api_client.create_event(
            event_id=str(uuid.uuid4()),
            event_name=event_name,
            event_description=event_description,
            tickets=tickets,
            start=start_timestamp,
            end=end_timestamp,
            private=private,
        )

        if response.status_code == 200:
            st.success("Event Created Successfully!")
        else:
            st.error("Error creating event. Please try again.")

elif menu == "Search Events":
    st.header("Search Events")
    search_text = st.text_input("Search Text")
    search_limit = st.number_input("Number of Results", min_value=1, step=1)
    search_mode = st.selectbox("Search Mode", ["id", "text"])

    if st.button("Search"):
        response = api_client.search_event(
            text=search_text, limit=search_limit, mode=search_mode
        )
        if response.status_code == 200:
            st.write(response.json())
        else:
            st.error("Error searching events. Please try again.")

elif menu == "Register for Event":
    st.header("Register for Event")
    event_id = st.text_input("Event ID")

    if st.button("Register"):
        response = api_client.register_user(event_id=event_id)
        if response.status_code == 200:
            st.success("Registered Successfully!")
        else:
            st.error("Error registering for the event. Please try again.")

elif menu == "Redeem/Cancel Ticket":
    st.header("Redeem or Cancel Ticket")
    event_id = st.text_input("Event ID")
    ticket = st.text_input("Ticket ID")
    action = st.radio("Action", ["Redeem", "Cancel"])

    if st.button("Submit"):
        if action == "Redeem":
            response = api_client.redeem_ticket(event_id=event_id, ticket=ticket)
        else:
            response = api_client.cancel_ticket(event_id=event_id, ticket=ticket)

        if response.status_code == 200:
            st.success(f"Ticket {action}ed Successfully!")
        else:
            st.error(f"Error {action.lower()}ing ticket. Please try again.")
