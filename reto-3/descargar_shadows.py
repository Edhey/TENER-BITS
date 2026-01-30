import requests
import os

# CONFIGURATION
BASE_URL = "http://hpecds.comnetconsultores.cloud:7373"
ENDPOINT_BASE = "/api/v1/EMBARQUESHADOW/download"
FILES = [
    "shadow1.pdf",
    "shadow2.pdf",
    "shadow3.pdf",
    "shadow4.pdf",
    "shadow5.pdf",
    "shadow6.pdf",
    "shadow7.pdf",
]


def download_files():
    print("STARTING DOWNLOAD OF CONFIDENTIAL DOCUMENTS...\n")

    output_dir = "shadow_files"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in FILES:
        # Build full URL
        url = f"{BASE_URL}{ENDPOINT_BASE}/{filename}"

        print(f"Downloading {filename} ...")

        try:
            r = requests.get(url, timeout=10)

            if r.status_code == 200:
                # Save into the folder
                file_path = os.path.join(output_dir, filename)
                with open(file_path, "wb") as f:
                    f.write(r.content)
                print(f"Saved to: {file_path}")
            else:
                print(f"Error {r.status_code}: Could not download.")

        except Exception as e:
            print(f"Connection error: {e}")

    print("\n" + "=" * 50)
    print("OPERATION COMPLETED.")
    print(f"   Check the folder '{output_dir}'")
    print("=" * 50)


if __name__ == "__main__":
    download_files()
