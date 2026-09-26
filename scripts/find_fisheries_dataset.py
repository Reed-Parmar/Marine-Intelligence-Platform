"""
Discover authoritative public marine fisheries catch datasets.
"""
import re
import requests

def search_iotc():
    paths = [
        "/data/datasets/latest/NC/ALL",
        "/data/datasets/latest/CE/ALL",
        "/data/datasets/latest/CE/LL",
        "/data/datasets/latest/CE/SURF",
        "/data/datasets/latest/CE/COAST",
    ]
    for p in paths:
        url = "https://iotc.org" + p
        try:
            r = requests.get(url, timeout=10, allow_redirects=True)
            print(f"{p} -> {r.status_code} (final URL: {r.url})")
            links = re.findall(r'href="([^"]*\.zip)"', r.text)
            if links:
                print("  Zip files:", set(links))
        except Exception as e:
            print(f"Error {p}: {e}")

if __name__ == "__main__":
    search_iotc()
