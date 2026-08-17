import re
import requests
from bs4 import BeautifulSoup

MAPPING_WEBSITEID_HLSURL = {
    "9BBE055A-4CF6-4BC3-A675-D40E89B55B91": "https://trkvz.daioncdn.net/aspor/aspor.m3u8?ce=3&app=45f847c4-04e8-419a-a561-2ebf87084765",
    "0C1BC8FF-C3B1-45BE-A95B-F7BB9C8B03ED": "https://trkvz.daioncdn.net/a2tv/a2tv.m3u8?ce=3&app=59363a60-be96-4f73-9eff-355d0ff2c758",
    "AAE2E325-4EAE-45B7-B017-26FD7DDB6CE4": "https://trkvz.daioncdn.net/minikago/minikago.m3u8?app=web&ce=3",
    "01ED59F2-4067-4945-8204-45F6C6DB4045": "https://trkvz.daioncdn.net/minikago_cocuk/minikago_cocuk.m3u8?app=web&ce=3",
}
VIDEOID_LIVE = "00000000-0000-0000-0000-000000000000"

def get_secure_video_token(page_url: str) -> str | None:
    headers = {"User-Agent": "Mozilla/5.0"}

    # 1. Sayfadan data-videoid ve data-websiteid çekme
    res = requests.get(page_url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    
    div = soup.find(attrs={"data-videoid": True, "data-websiteid": True})
    if not div:
        match = re.search(r"""var\s+tmdPlayer\s*=\s*(?P<q>["'])(.*?)(?P=q)""", res.text, re.DOTALL)
        if match:
            p_soup = BeautifulSoup(match.group(2), "html.parser")
            div = p_soup.find(attrs={"data-videoid": True, "data-websiteid": True})

    if not div:
        return None

    video_id = div["data-videoid"]
    website_id = div["data-websiteid"]

    # 2. videojs API'sinden ham HLS URL'sini alma
    api_url = f"https://videojs.tmgrup.com.tr/getvideo/{website_id}/{video_id}"
    data = requests.get(api_url, headers=headers).json()
    if not data.get("success"):
        return None

    hls_url = data["video"]["VideoSmilUrl"]
    if video_id == VIDEOID_LIVE:
        hls_url = MAPPING_WEBSITEID_HLSURL.get(website_id.upper(), hls_url)

    # 3. securevideotoken servisine Referer göndererek imzalı linki alma
    token_api = "https://securevideotoken.tmgrup.com.tr/webtv/secure"
    token_res = requests.get(
        token_api,
        params={"url": hls_url},
        headers={"Referer": page_url, "User-Agent": "Mozilla/5.0"}
    ).json()

    return token_res.get("Url") if token_res.get("Success") else None


# Kullanım Örneği:
target_page = "https://www.atvavrupa.tv/canli-yayin"
secure_token_url = get_secure_video_token(target_page)

print("Bulunan Secure Token Kaynağı:")
print(secure_token_url)
