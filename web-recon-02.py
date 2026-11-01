import argparse
import json
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


def process_url(url):
  # 1. Phân tích URL
  parsed = urlparse(url)

  # 2. Gửi HTTP Request
  try:
    response = requests.get(url, timeout=5)
    status = response.status_code
    html_content = response.text
    headers = dict(response.headers)
  except requests.RequestException as e:
    return {"error": str(e)}

  # 3. Phân tích nội dung HTML (BeautifulSoup)
  soup = BeautifulSoup(html_content, "html.parser")
  title = soup.title.text.strip() if soup.title else ""
  links = [link.get("href") for link in soup.find_all("a") if link.get("href")]

  # 4. Trích xuất tùy chỉnh bằng Regex (ví dụ tìm email)
  emails = re.findall(r"[\w.-]+@[\w.-]+\.\w+", html_content)

  # --- CẬU CÓ THỂ THÊM TÍNH NĂNG RIÊNG Ở ĐÂY ---

  return {
      "url": url,
      "scheme": parsed.scheme,
      "hostname": parsed.hostname,
      "status_code": status,
      "title": title,
      "links_count": len(links),
      "emails_found": list(set(emails)),
      # "security_headers": {h: headers.get(h) for h in ["X-Frame-Options", "Content-Security-Policy"]}
  }


def main():
  parser = argparse.ArgumentParser(
      description="Khung code tối giản để quét và phân tích URL."
  )
  parser.add_argument("--urls", nargs="+", required=True, help="Danh sách URL")
  parser.add_argument(
      "-o", "--output", default="result.json", help="File lưu kết quả"
  )
  args = parser.parse_args()

  results = {}
  for url in args.urls:
    print(f"Đang xử lý: {url}")
    results[url] = process_url(url)

  with open(args.output, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

  print(f"Hoàn tất. Kết quả được lưu tại: {args.output}")


if __name__ == "__main__":
  main()