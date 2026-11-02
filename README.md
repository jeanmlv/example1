# example1

if not response.ok:
    try:
        error_data = response.json()
        print("HTTP status:", response.status_code)
        print("Girder error:", error_data.get("message", "No error message"))
        print("Error type:", error_data.get("type", "Unknown"))
    except ValueError:
        print("HTTP status:", response.status_code)
        print("The server returned a non-JSON error response.")

    raise RuntimeError("Girder API authentication failed.")
