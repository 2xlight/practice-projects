import requests
import json
from pathlib import Path

Path("results").mkdir(exist_ok=True)

output = Path("results") / "example.json"

def scan_http(url, timeout=5):

    result = {
        "url": url,
        "status": None,
        "server": None,
        "technologies": []
    }

    try:
        response = requests.get(url, timeout=timeout)

        result["status"] = response.status_code

        headers = response.headers

        result["server"] = headers.get("Server")

        if "X-Powered-By" in headers:
            result["technologies"].append(
                headers["X-Powered-By"]
            )

        if result["server"]:
            result["technologies"].append(
                result["server"]
            )

        result["technologies"] = list(
            set(result["technologies"])
        )

        return result

    except requests.RequestException as error:

        result["error"] = str(error)

        return result

with open("results/example.json") as f:
    data = json.load(f)
    dump = json.dump(f, indent=4)

print(data["target"])
print(data["server"])
print(dump["elements"])