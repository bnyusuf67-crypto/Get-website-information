import re
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from urllib.parse import quote

CHANNELS = {
    "ATV": {"page": "https://www.atv.com.tr/canli-yayin", "fallback_hls": "https://trkvz.daioncdn.net/atv/atv.m3u8?ce=3&app=web"},
    "A Haber": {"page": "https://www.ahaber.com.tr/canli-yayin", "fallback_hls": "https://trkvz.daioncdn.net/ahaber/ahaber.m3u8?ce=3&app=web"},
    "A News": {"page": "https://www.anews.com.tr/live-stream", "fallback_hls": "https://trkvz.daioncdn.net/anews/anews.m3u8?ce=3&app=web"},
    "A Para": {"page": "https://www.apara.com.tr/canli-yayin", "fallback_hls": "https://trkvz.daioncdn.net/apara/apara.m3u8?ce=3&app=web"},
    "A Spor": {"page": "https://www.aspor.com.tr/canli-yayin", "fallback_hls": "https://trkvz.daioncdn.net/aspor/aspor.m3u8?ce=3&app=45f847c4-04e8-419a-a561-2ebf87084765"},
    "A2 TV": {"page": "https://www.a2tv.com.tr/canli-yayin", "fallback_hls": "https://trkvz.daioncdn.net/a2tv/a2tv.m3u8?ce=3&app=59363a60-be96-4f73-9eff-355d0ff2c758"},
    "Minika Çocuk": {"page": "https://www.minikacocuk.com.tr/webtv/canli-yayin", "fallback_hls": "https://trkvz.daioncdn.net/minikago_cocuk/minikago_cocuk.m3u8?app=web&ce=3"},
    "Minika GO": {"page": "https://www.minikago.com.tr/webtv/canli-yayin", "fallback_hls": "https://trkvz.daioncdn.net/minikago/minikago.m3u8?app=web&ce=3"},
    "Vav TV": {"page": "https://www.vavtv.com.tr/canli-yayin", "fallback_hls": "https://trkvz.daioncdn.net/vavtv/vavtv.m3u8?ce=3&app=web"},
    "ATV Avrupa": {"page": "https://www.atvavrupa.tv/canli-yayin", "fallback_hls": "https://trkvz.daioncdn.net/atvavrupa/atvavrupa.m3u8?ce=3&app=web"}
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def get_secure_token_api_url(info: dict) -> str:
    hls_url = None
    try:
        res = requests.get(info["page"], headers=HEADERS, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            div = soup.find(attrs={"data-videoid": True, "data-websiteid": True})
            if div:
                video_id = div["data-videoid"]
                website_id = div["data-websiteid"]
                api_res = requests.get(f"https://videojs.tmgrup.com.tr/getvideo/{website_id}/{video_id}", headers=HEADERS, timeout=5).json()
                if api_res.get("success"):
                    hls_url = api_res["video"]["VideoSmilUrl"]
    except Exception:
        pass

    if not hls_url:
        hls_url = info["fallback_hls"]

    return f"https://securevideotoken.tmgrup.com.tr/webtv/secure?url={quote(hls_url, safe=':/?=&')}"

def main():
    try:
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        with open("tokens.txt", "w", encoding="utf-8") as f:
            f.write(f"# Last Updated: {now_str}\n\n")
            for channel_name, info in CHANNELS.items():
                token_api_url = get_secure_token_api_url(info)
                f.write(f"{channel_name} | Referer: {info['page']} | API: {token_api_url}\n")
    except Exception as e:
        print(f"Betiğin çalışması sırasında beklenmeyen bir hata oluştu: {e}")

if __name__ == "__main__":
    main()
