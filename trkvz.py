import re
import requests
from bs4 import BeautifulSoup

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

def get_secure_video_token(page_url: str) -> str | None:
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(page_url, headers=headers, timeout=10)
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

        api_url = f"https://videojs.tmgrup.com.tr/getvideo/{website_id}/{video_id}"
        data = requests.get(api_url, headers=headers, timeout=10).json()
        if not data.get("success"):
            return None

        hls_url = data["video"]["VideoSmilUrl"]
        if video_id == VIDEOID_LIVE:
            hls_url = MAPPING_WEBSITEID_HLSURL.get(website_id.upper(), hls_url)

        token_api = "https://securevideotoken.tmgrup.com.tr/webtv/secure"
        token_res = requests.get(
            token_api,
            params={"url": hls_url},
            headers={"Referer": page_url, "User-Agent": "Mozilla/5.0"},
            timeout=10
        ).json()

        return token_res.get("Url") if token_res.get("Success") else None
    except Exception:
        return None

def main():
    file_name = "tokens.txt"
    
    with open(file_name, "w", encoding="utf-8") as file:
        for channel_name, page_url in CHANNELS.items():
            print(f"Çözümleniyor: {channel_name}")
            token_url = get_secure_video_token(page_url)
            
            if token_url:
                file.write(f"{channel_name}: {token_url}\n")
                print(f" -> [OK] Adres alındı.")
            else:
                print(f" -> [HATA] Adres alınamadı.")

    print(f"\nİşlem tamamlandı! Adresler '{file_name}' dosyasına kaydedildi.")

if __name__ == "__main__":
    main()
