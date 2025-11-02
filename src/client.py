import uuid
import jwt
import requests
from datetime import datetime
import time
from app.crypto.asymmetric import AKE


class EventAPI:
    def __init__(self, private_key_path: str, public_key_path: str, base_url: str):
        """
        Initializes the EventAPI class with paths to keys and base URL.
        :param private_key_path: Path to the RSA private key file.
        :param public_key_path: Path to the RSA public key file.
        :param base_url: Base URL of the API.
        """
        self.private_key_path = private_key_path
        self.public_key_path = public_key_path
        self.base_url = base_url
        self.private_key = self._load_key(private_key_path)
        self.public_key = self._load_key(public_key_path)

        self.server_private_key = self._load_key("data\\priv.key")
        self.server_public_key = self._load_key("data\\pub.key")

    def _load_key(self, key_path: str) -> str:
        """Loads the key from the specified file path."""
        with open(key_path, "r") as key_file:
            return key_file.read()

    def _generate_jwt(self, data: dict) -> str:
        """Generates a JWT token for the given data."""
        return jwt.encode(data, self.private_key, algorithm="RS256")

    def _post_request(self, endpoint: str, payload: dict) -> requests.Response:
        """Sends a POST request to the specified endpoint with the given payload."""
        url = f"{self.base_url}/{endpoint}"
        return requests.post(url, json=payload)

    def _get_request(
        self, endpoint: str, params: dict, headers: dict = None
    ) -> requests.Response:
        """
        Sends a GET request to the specified endpoint with the given parameters and headers.
        :param endpoint: API endpoint (e.g., 'search').
        :param params: Dictionary of query parameters to include in the request.
        :param headers: Optional dictionary of HTTP headers.
        :return: Response from the server.
        """
        url = f"{self.base_url}/{endpoint}"
        return requests.get(url, params=params, headers=headers)

    def search_event(self, text: str, limit: int, mode: str) -> requests.Response:
        """
        Sends a search request with a signed JWT.
        :param text: Text to search for.
        :param limit: Number of results to return.
        :param mode: Search mode (e.g., 'id', 'text').
        :return: Response from the server.
        """
        data = {
            "id": str(uuid.uuid4()),
            "timestamp": float(time.time()),
            "content": {"text": text, "limit": limit, "mode": mode},
        }
        signature = self._generate_jwt(data)
        payload = {"data": data, "public_key": self.public_key, "signature": signature}
        return self._post_request("search", payload)

    def register_user(self, event_id: str) -> requests.Response:
        """
        Sends a user registration request with a signed JWT.
        :param event_id: ID of the event the user is registering for.
        :param content: User-specific registration content.
        :return: Response from the server.
        """
        data = {
            "id": str(uuid.uuid4()),
            "timestamp": float(time.time()),
            "content": {"event_id": event_id},
        }
        signature = self._generate_jwt(data)
        payload = {"data": data, "public_key": self.public_key, "signature": signature}
        return self._post_request("register", payload)

    def create_event(
        self,
        event_id: str,
        event_name: str,
        event_description: str,
        tickets: int,
        start: int,
        end: int,
        private: bool,
    ) -> requests.Response:
        """
        Sends a request to create an event with a signed JWT.
        :param event_id: Unique identifier for the event.
        :param event_name: Name of the event.
        :param event_description: Description of the event.
        :param tickets: Total number of tickets available for the event.
        :param start: Event start timestamp (Unix time).
        :param end: Event end timestamp (Unix time).
        :param private: Boolean indicating if the event is private.
        :return: Response from the server.
        """
        data = {
            "id": str(uuid.uuid4()),
            "timestamp": float(time.time()),
            "content": {
                "event": {
                    "id": str(uuid.uuid4()),
                    "name": event_name,
                    "description": event_description,
                    "tickets": tickets,
                    "issued": 0,
                    "start": start,
                    "end": end,
                    "exchanges": 16,
                    "private": private,
                }
            },
        }
        signature = self._generate_jwt(data)
        payload = {"data": data, "public_key": self.public_key, "signature": signature}
        return self._post_request("create", payload)

    def cancel_ticket(self, event_id: str, ticket: str) -> requests.Response:
        """
        Sends a ticket cancellation request with a signed JWT.
        :param event_id: ID of the event the ticket is associated with.
        :param ticket: Ticket ID or identifier to cancel.
        :return: Response from the server.
        """
        data = {
            "id": str(uuid.uuid4()),
            "timestamp": float(time.time()),
            "content": {"event_id": event_id, "ticket": ticket},
        }
        signature = self._generate_jwt(data)
        payload = {"data": data, "public_key": self.public_key, "signature": signature}
        return self._post_request("cancel", payload)

    def redeem_ticket(self, event_id: str, ticket: str) -> requests.Response:
        """
        Sends a ticket redemption request with a signed JWT.
        :param event_id: ID of the event associated with the ticket.
        :param ticket: Ticket ID or identifier to redeem.
        :return: Response from the server.
        """
        data = {
            "id": str(uuid.uuid4()),
            "timestamp": float(time.time()),
            "content": {"event_id": event_id, "ticket": ticket},
        }
        signature = self._generate_jwt(data)
        payload = {"data": data, "public_key": self.public_key, "signature": signature}
        return self._post_request("redeem", payload)

    def verify(
        self, event_id: str, ticket: str, check_public_key: str
    ) -> requests.Response:
        """
        Verifies a ticket by making a request to the /verify endpoint.
        :param event_id: ID of the event associated with the ticket.
        :param ticket: Ticket ID or identifier to verify.
        :param check_public_key: Public key to check against.
        :return: Response from the /verify endpoint.
        """
        data = {
            "id": str(uuid.uuid4()),
            "timestamp": float(time.time()),
            "content": {
                "event_id": event_id,
                "ticket": ticket,
                "check_public_key": self.public_key,##using same pubkey as server rn
            },
        }
        signature = self._generate_jwt(data)
        payload = {"data": data, "public_key": self.public_key, "signature": signature}
        return self._post_request("verify", payload)
    




    def check_signature(self, res_json, public_key = None) -> bool:
        """
        """

        cipher = AKE(private_key=self.server_private_key, public_key=self.server_public_key)##check public key needed if this was ever rly implemted
        return cipher.verify(res_json["signature"], res_json["data"])


# Example usage
if __name__ == "__main__":
    # Initialize the API client
    api_client = EventAPI(
        private_key_path="priv.demo.key",
        public_key_path="pub.demo.key",
        base_url="http://localhost:8000",
    )

    # # Create event
    # create_response = api_client.create_event(
    #     event_id=str(uuid.uuid4()),
    #     event_name="Cybersecurity Conference",
    #     event_description="Annual cybersecurity conference.",
    #     tickets=500,
    #     start=int(datetime(2025, 12, 1, 9, 0).timestamp()),
    #     end=int(datetime(2025, 12, 1, 17, 0).timestamp()),
    #     private=False,
    # )
    # print("Create Event Response:", create_response.status_code, create_response.json())

    # Search event
    # search_response = api_client.search_event(text="event123", limit=1, mode="id")
    # print("Search Response:", search_response.status_code, search_response.json())

    """
    event_id = "794b0be3-53ad-455c-b9ea-2c7e61bc2188"
    # # Register user
    register_response = api_client.register_user(event_id=event_id, content="user123")
    print("Register Response:", register_response.status_code, register_response.json())
    """

    # # Cancel ticket
    # cancel_response = api_client.cancel_ticket(event_id="event123", ticket="ticket456")
    # print(
    #     "Cancel Ticket Response:", cancel_response.status_code, cancel_response.json()
    # )

    ##ticket = "3JHN1KA6f2GqC4u2X8F/9w==-DQ6zMVtp5wvC37Mv9b4uYMehGNx5QymArZyd7hor95r13WQXLTOLQgheg1n9iDk0wJ9CT84birKBPcwt+GDKVlXaEfTrn70CMxLqblou/WKXXPZ6nNsrqCjfZr4Fr39VxyLi0BuJuIQCDX2bHVn5Q42bVilD9GS+eTWgSy+KgcyVYrX9W5WBHVVkxxQXLrtpW+ZVrsJ7lw7GgwwNO9xb+XaztSnu69wRX9cN6JsSQd3NGQhboO4aDWHkZRnUbuiE76kZQ7XNXjqWbX8bznmSAIZk0gUV4NoIL6Yfn47xJ+naCU/DEitoUjzGPcXsSGw8dDyCIsAyGD4iJIc+LF9f0AaVWA6zJA1EKxpFMabg1LBJIvw80E4+56YgdlWW00lCZDiuq359HlTrEENJEFkR70v1UZdz9ZhIFJa6xcwppAdorvZBGBtg5P19PrkshiH4VzApdiPTljnUAxo6S3e+X3i+2eT3qPrt2iRVPu/nTpwHJSZ0wMTqtJtkh8G8usf/nh/0sPhCfif+45ZjfnQCu06lI96/MJgHE+VxBcR6ueHckppPw2s05f/fzRmFFdmm8d5rcg6QNoF5uOteXyUWR41q9css79yD8/X4m03TJDUppyqHkvgANmJmJQvCFoUznLtRkIR8aVVnZqC+8rCrRf5AAnZvDdYzV+67oIczZSv8N1g4uJevbCxDG7xd+pBXbxRGOYvp7F3J8dsaGBCTrZBwcDCzWYTmzXz42vpf8QwJUsm2HdrPIT868WxT70OEwnno0RNoOgJLzn7LoHEPway62MaLxtX5gG30CHRNl5lCJphrB4n5LKlt8MiS01+uVlEzWbjXC3GgXJfTsH/1wqCUezQDjOPbPmjzDk82NJ32/YDrBFWAjxxTWOVAhQ4zi1PWqTSeqJEYY6YpxUCHeLwlT6OrPqbsXsGic+fo9MVsbQ3dYf5uO9+YLM8wYXMQdGinLzh7spsX8SNZIc1ZSujq1BASOy8JjnpGx6OR8msmrWWDsTOp7WzmXCg1T3tuMzPmpGJGBB3yePx2o28dbngtZtXm1m1OwVfNYvGMJtyENbvwOpt/9S/mK09sa0D0IdME5VrhIEp5+c3ld/ZpvAiepwIRXmW9G7uAyxDyBK39QVsiTSar3jPC/57mHrbfEiogugqQWUQmNwXXmmgUj98AXbzLOUeIPk3kwUVcoxDXD5XQu2ps3QYEI/lxoR20"
    """
    ticket = "Yk/YujnFzrvGqFY1VttF2g==-VubW/QwQm9M60j9KOWVOHuNlGa/Mom4s7qcicaIQP7F1E1dclz6n9DmGLHHc+xhUKl20YAPfV4KC3bOtXDOt2HlTlTX4HDI7MWzBZPBI45m/Npg8axi0589gKxm041RCJTzTQeBlUPmzUxto4+AVP3S51ESaper44rh8xmWqm2Hv26ZRmSRmDgwdVR98I4f4P0mhfUykk6j/fquiWRpTvz9b6Zl5e32pnZXdKcsAQzlKrtbdvpl95lmDP+5wwsuejSNHFwyHJjsaGEhv2F7b6HzmIxaBPHYpNEmE97uUBUyUZSxt2VEAHW/NnPXOhGtRbLvsS36Z7Vel3m87bfJGCBlXM/1bFG3FLc9U4yv3oqIAZMtsgMlHvP1KTTvu0MD0mg6CB2XNA8Z3FLO+O29QiAY9yw4kjn7QvZo8q2tmxruZnWlhwrLsaMkCE/NZkEtDrbC01pV7UtLGRjUy9+ZHTReLjk+AqQoEF+1Aw7cbWWJbd1Tk99T5KdjjhkI6K1T0Nry2ZNetF10AnYrXvXeWxXzBs+pv9OfJWNL/DjSUNW1h1qYQsjzW5bwxWZuaykl7pr+j9on4HyElrOpiUkbHt9itziGLiUtOtAw/+27wrzI2LBD/9NSqhjzjQw+wUSutu06QY93+DQ2IBOmwxPyy2OgokJhNjqQyHNoyu6kqWO42hOYYHfVME7wDQ83r+AR28qU+drg/cmAfTuOJiy1z+rQeBmJtIQHnvUfYwfkXLX9UlUBQG8hXrFVvgBTGSwFVQBiY0uCmxeYP1ginC6Ph0b27xoYVLUcluWLqavNHO8rgs6bmpFA+LNj4psGJSL9NzxQ2F0PjX6qHrLgIZ7hmzpQXUlHv864Cj0G9PusJKongTmjogWC+eU9txwboMEnBrmRzF2vMMcQey7dxGf0CcerHLmarksVcOjrKsuY9Y35+1EyOaSjpAyJvDe3McsoyxdiXDUb6QeC9OPPMc3Ly5DpGRw2fdkIWDfU4ipT9/sEoi84FhTHGIzN9VD0pZAScoAsDru+QIh2gYXSw/8wLskUNWVMnPHlckaOA500FY97mIjhmZH7dHa8w/56sKJ0E5JIrdAd/vm2TsnEeMfS6VJVJMEL4VzldSMiUDugiBtY2VmupvSbbr34tmv8UcYkOJ0LHt1z5hPa8Xkxr9mnXbnL05Y01eTYHeJUwz9C34ma12B6q0AoxGEAa9irj2atB"

    event_id = "794b0be3-53ad-455c-b9ea-2c7e61bc2188"  # Replace with your event ID
    # ticket = "3JHN1KA6f2GqC4u2X8F/9w==..."  # Replace with your ticket string
    redeem_response = api_client.redeem_ticket(event_id=event_id, ticket=ticket)
    print("redeem response", redeem_response)
    print(
        "Redeem Ticket Response:", redeem_response.status_code, redeem_response.json()
    )
    """


    ticket = "Yk/YujnFzrvGqFY1VttF2g==-VubW/QwQm9M60j9KOWVOHuNlGa/Mom4s7qcicaIQP7F1E1dclz6n9DmGLHHc+xhUKl20YAPfV4KC3bOtXDOt2HlTlTX4HDI7MWzBZPBI45m/Npg8axi0589gKxm041RCJTzTQeBlUPmzUxto4+AVP3S51ESaper44rh8xmWqm2Hv26ZRmSRmDgwdVR98I4f4P0mhfUykk6j/fquiWRpTvz9b6Zl5e32pnZXdKcsAQzlKrtbdvpl95lmDP+5wwsuejSNHFwyHJjsaGEhv2F7b6HzmIxaBPHYpNEmE97uUBUyUZSxt2VEAHW/NnPXOhGtRbLvsS36Z7Vel3m87bfJGCBlXM/1bFG3FLc9U4yv3oqIAZMtsgMlHvP1KTTvu0MD0mg6CB2XNA8Z3FLO+O29QiAY9yw4kjn7QvZo8q2tmxruZnWlhwrLsaMkCE/NZkEtDrbC01pV7UtLGRjUy9+ZHTReLjk+AqQoEF+1Aw7cbWWJbd1Tk99T5KdjjhkI6K1T0Nry2ZNetF10AnYrXvXeWxXzBs+pv9OfJWNL/DjSUNW1h1qYQsjzW5bwxWZuaykl7pr+j9on4HyElrOpiUkbHt9itziGLiUtOtAw/+27wrzI2LBD/9NSqhjzjQw+wUSutu06QY93+DQ2IBOmwxPyy2OgokJhNjqQyHNoyu6kqWO42hOYYHfVME7wDQ83r+AR28qU+drg/cmAfTuOJiy1z+rQeBmJtIQHnvUfYwfkXLX9UlUBQG8hXrFVvgBTGSwFVQBiY0uCmxeYP1ginC6Ph0b27xoYVLUcluWLqavNHO8rgs6bmpFA+LNj4psGJSL9NzxQ2F0PjX6qHrLgIZ7hmzpQXUlHv864Cj0G9PusJKongTmjogWC+eU9txwboMEnBrmRzF2vMMcQey7dxGf0CcerHLmarksVcOjrKsuY9Y35+1EyOaSjpAyJvDe3McsoyxdiXDUb6QeC9OPPMc3Ly5DpGRw2fdkIWDfU4ipT9/sEoi84FhTHGIzN9VD0pZAScoAsDru+QIh2gYXSw/8wLskUNWVMnPHlckaOA500FY97mIjhmZH7dHa8w/56sKJ0E5JIrdAd/vm2TsnEeMfS6VJVJMEL4VzldSMiUDugiBtY2VmupvSbbr34tmv8UcYkOJ0LHt1z5hPa8Xkxr9mnXbnL05Y01eTYHeJUwz9C34ma12B6q0AoxGEAa9irj2atB"
    utick = "sxZx0HSmSyMLCI3keoG/Cg==-o8LDvLiERNnOxcPNodWXJALzxQJoX/jobz42T+UtN4lEy42nb8pxYu6Y9+d5Po34rXhm02/dNzlUouuB1TxvNzJtcoxhsbw+diZaolhxWlw9a3cRWJ7qvbp5RHYYZGnrsm87FJn8T52u8SrB4q3wvAzeNjD1w7RzFBIGczxBw23bPyWztwokIg6hMFTcGUPzaZiMlmU+ql+E6Ft+4BBoKL9/3srjE3LBrxrGNFZVDbZ/Hon6F+kMnlrNmwhGgLZaJt/N5FVLE8cnSkj4hbbf+dcwDvEvosTEeJrIiBCLeq++kp7XnBeCcc/+s+vrjOIyXwTfwHKdYIlRsmwETOsqwXsHwNWFYcWX5SyobsaDQ1NIIvGxh/ae9/xDY8wteG33nf0LKwiLzBzr/NMi1GRxt9mU7hmJuXx7tYv/JFE0DocJ4LM9ge5IR0tSjnOkD/oBJHDMxrKL5DbxQGEwTq2Hk1yFrznsiuqdlZbNIJJr1NDENa/Eg+sh5Kgw3Kccy9RRPTktSmRzYFAA2D3ORktoNOLdmbCVNLqG8zvoNqOmDSubNFjdsOns/llvPfkT+klPdGMywEHYbihQjycknusjeoNYjh6ARN/1Wmc+zgmWTmskMbO8XpBqYvVdiW0rT/HqAJ+JawtizeD194wp3hG1P3QeHs9N9LtNraVOETVMDqz73BoVlYAYKKJfaF1PyYzxMaST6nOaIb3w1oT8yBUlKnv+VI5PB+d6hKtNI9OoEEdE+ib6dJ7/+GKbVIONnMb/jA4beZ0pVr522JSHf7je7fdwXhC7mOe4rp+zv9Lo6KqlWIYBgF3iMsCx186qZI86TNSgGXQqR/i1EjJrtvLaIor1PNL3aWafdmyEUSUiB8cjEY1daX+P7HFLN9PnuCxo3QXs5odG/IHie4lEoy/5IImVz+H3kbkFmfwc2U9OUzny7qbkhIcDbWXNXli+HnmjRNkWKZcoszJdoGXcm0bD3FFH6t7pQ8X5Ow9qpaykMUNwF3UKxO2jKxgt3GuAVJXBlxCyfT6IU94GKEkLx69rn28F81+liET+5UfrGLthY0q7st9CgklOSP+v2uhvAOH3uON+M3sYPsM2imW5UqHQFEciI0AOal5rLduFxP+HOzJV+7/kQJ46gtI+NyslD2kGSQNny1STDFLLLbx1kE4Y088wfNJJlTnMyoYV4RX+Zdi5T/ibuZigJObemaaXjX/r"
   
    event_id = "794b0be3-53ad-455c-b9ea-2c7e61bc2188"  # Replace with your event ID
    # ticket = "3JHN1KA6f2GqC4u2X8F/9w==..."  # Replace with your ticket string
    verify_response = api_client.verify(event_id=event_id, ticket=ticket, check_public_key=None)
    print(
        "Redeem Ticket Response:", verify_response.status_code, verify_response.json()
    )