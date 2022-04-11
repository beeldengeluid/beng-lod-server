from urllib.parse import urlparse, urlunparse

def prepare_beng_uri(beng_data_domain : str, path: str):
    """Use the domain and the path given to construct a proper Beeld en Geluid URI."""
    parts = urlparse(beng_data_domain)
    new_parts = (parts.scheme, parts.netloc, path, None, None, None)
    return urlunparse(new_parts)