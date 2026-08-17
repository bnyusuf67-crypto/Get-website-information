import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

CHANNELS = {
    "ATV": "https://www.atv.com.tr/canli-yayin",
    "A Haber": "https://www.ahaber.com.tr/canli-yayin",
    "A News": "https://www.anews.com.tr/live-stream",
    "A Para": "https://www.apara.com.tr/canli-yayin",
    "A Spor": "https://www.aspor.com.tr/canli-yayin",
    "A2 TV": "https://www.a2tv.com.tr/canli-yayin",
    "Minika Çocuk": "https://www.minikacocuk.com.tr/webtv/canli-yayin",
    "Minika GO": "https://www.minikago.com.tr/webtv/canli-yayin",
    "Vav TV": "https://www.vavtv.com.tr/canli-yayin",
    "ATV Avrupa": "https://www.atvavrupa.tv/canli-yayin",
}

MAPPING_WEBSITEID_HLSURL = {
    "9BBE055A-4CF6-4BC3-A675-D40E89B55B91": "https://trkvz.daioncdn.net/aspor/aspor.m3u8?ce=3&app=45f847c4-04e8-419a-a561-2ebf87084765",
    "0C1BC8FF-C3B1-45BE-A95B-F7BB9C8B03ED": "https://trkvz.daioncdn.net/a2tv/a2tv.m3u8?ce=3&app=59363a60-be96-4f73-9eff-355d0ff2c758",
    "AAE2E325-4EAE-45B7-B017-26FD7DDB6CE4": "https://trkvz.daioncdn.net/minikago/minikago.m3u8?app=web&ce=3",
    "01ED59F2-4067-4945-8204-45F6C6DB4045": "https://trkvz.daioncdn.net/minikago_cocuk/minikago_cocuk.m3u8?app=web&ce=3",
}
VIDEOID_LIVE = "00000000-0000-0000-0000-000000000000"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def get_secure_token_api_url(page_url: str) -> str | None:
    try:
        res = requests.get(page_url, headers=HEADERS, timeout=10)
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

        # VideoJS API sorgusu
        api_url = f"https://videojs.tmgrup.com.tr/getvideo/{website_id}/{video_id}"
        api_res = requests.get(api_url, headers=HEADERS, timeout=10).json()

        if not api_res.get("success"):
            return None

        hls_url = api_res["video"]["VideoSmilUrl"]
        if video_id == VIDEOID_LIVE:
            hls_url = MAPPING_WEBSITEID_HLSURL.get(website_id.upper(), hls_url)

        # Doğrudan Secure Video Token API adresi oluşturulur
        token_api_endpoint = f"https://securevideotoken.tmgrup.com.tr/webtv/secure?url={quote(hls_url, safe=':/?=&')}"
        return token_api_endpoint

    except Exception as e:
        print(f"Hata ({page_url}): {e}")

    return None

def main():
    with open("tokens.txt", "w", encoding="utf-8") as f:
        for channel_name, page_url in CHANNELS.items():
            print(f"Token API Adresi Oluşturuluyor: {channel_name}")
            api_endpoint = get_secure_token_api_url(page_url)
            
            if api_endpoint:
                f.write(f"{channel_name}: {api_endpoint}\n")
                print(f" -> [OK] API URL: {api_endpoint}")
            else:
                print(" -> [HATA] Oluşturulamadı.")

if __name__ == "__main__":
    main()
