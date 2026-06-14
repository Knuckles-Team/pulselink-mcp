from typing import Any, Dict

import requests


class ApiClientBase:
    """Base HTTP API client wrapper."""

    def __init__(self, base_url: str, token: str, verify: bool = True):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.verify = verify
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = self.session.request(method, url, verify=self.verify, **kwargs)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            return {"status": response.status_code, "text": response.text}
