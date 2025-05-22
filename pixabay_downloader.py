import requests
from pyntree import Node
from tqdm import tqdm

data = Node("pixabay.yml", autosave=True)

BASE_URL = "https://pixabay.com/api/"


def get_sunset_pictures(loop_count=-1):
    i = 0
    while True:
        download_pending()
        response = requests.get(BASE_URL, params={
            "key": data.api_key(),
            "q": "sunset",
            "image_type": "photo",
            "category": "places",
            "per_page": 200,
            "page": data.page()
        })
        for item in response.json()["hits"]:
            data.links().append(item["webformatURL"])
        data.page = data.page() + 1
        i += 1
        if i == loop_count:
            break


def download_pending():
    i = data.dl_index()
    for link in tqdm(data.links()[i:]):
        response = requests.get(link)
        if response.status_code == 200:
            with open(f"pixabay/sunset/pixb_{i}.jpg", "wb") as f:
                f.write(response.content)
            i += 1
            data.dl_index = i
        else:
            raise requests.RequestException(f"Failed to download {link}")


if __name__ == "__main__":
    get_sunset_pictures()
