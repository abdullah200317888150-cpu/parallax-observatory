"""Bounded, TLS-verified requests with safe, actionable archive errors."""
import requests

class ArchiveError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code

def archive_get(url: str, *, stage: str, params=None, timeout=(10, 35)):
    for attempt in range(2):
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            status = exc.response.status_code if exc.response is not None else None
            transient = isinstance(exc, (requests.Timeout, requests.ConnectionError)) or status in (429, 502, 503, 504)
            if attempt == 0 and transient and not isinstance(exc, requests.exceptions.SSLError):
                continue
            if isinstance(exc, requests.exceptions.SSLError):
                message = f'{stage}: TLS certificate verification failed. Check the Python certificate store or a network inspection proxy; certificate verification remains enabled.'
            elif isinstance(exc, requests.exceptions.ProxyError):
                message = f'{stage}: the configured network proxy could not connect to IRSA. Check your proxy or VPN connection.'
            elif isinstance(exc, requests.Timeout):
                raise ArchiveError(f'{stage}: IRSA did not respond within the connection/read timeout, including a retry. Check archive access or try again later.', 504) from exc
            elif status:
                message = f'{stage}: IRSA returned HTTP {status} after the request attempts.'
                if status in (502,503,504):
                    message += ' The archive or an upstream gateway could not complete the request.'
            else:
                message = f'{stage}: could not connect to IRSA. Check your internet, DNS, proxy, or VPN connection.'
            raise ArchiveError(message) from exc
