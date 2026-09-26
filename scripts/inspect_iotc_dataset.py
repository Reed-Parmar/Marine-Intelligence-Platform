"""
Inspect IOTC dataset zip contents.
"""
import io
import zipfile
import requests
import pandas as pd

urls = [
    "https://iotc.org/sites/default/files/documents/2024/07/IOTC-2024-WPB22-DATA03-NC.zip",
    "https://iotc.org/sites/default/files/documents/2024/07/IOTC-2024-WPB22-DATA05-CESurface.zip",
]

for url in urls:
    print(f"\nFetching {url}...")
    try:
        r = requests.get(url, timeout=30)
        print("Status:", r.status_code, "Size:", len(r.content) / 1024, "KB")
        if r.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                print("Files inside zip:")
                for name in z.namelist():
                    info = z.getinfo(name)
                    print(f"  {name} ({info.file_size / 1024:.1f} KB)")
                    if name.endswith(".csv"):
                        with z.open(name) as f:
                            df = pd.read_csv(f, nrows=5)
                            print(f"    Columns ({len(df.columns)}):", list(df.columns))
                            print("    Sample row:", df.iloc[0].to_dict())
    except Exception as e:
        print("Error:", e)
