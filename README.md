# example1

response = session.post(
    f"{API_URL.rstrip('/')}/api_key/token",
    params={"key": api_key},
    timeout=(15, 60),
)
