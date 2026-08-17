import re
import requests
from datetime import datetime, timezone
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
    "ATV Avrupa": "https://www.atvavrupa.tv/canli-yayin"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

def get_trkvz_api_stream_url(page_url: str) -> str | None:
    try:
        # 1. Kanal sayfasının HTML kaynağını çek
        res = requests.get(page_url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return None

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

        # 2. Turkuvaz Video API adresine istek at
        api_endpoint = f"https://videojs.tmgrup.com.tr/getvideo/{website_id}/{video_id}"
        api_res = requests.get(api_endpoint, headers=HEADERS, timeout=10).json()

        if not api_res.get("success"):
            return None

        video_data = api_res.get("video", {})
        
        # API'den dönen orijinal yayın adresi (VideoSmilUrl / VideoUrl)
        stream_url = video_data.get("VideoSmilUrl") or video_data.get("VideoUrl") or video_data.get("Url")
        return stream_url

    except Exception as e:
        print(f"Hata ({page_url}): {e}")
        return None

def main():
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    with open("trkvz-tokens.txt", "w", encoding="utf-8") as f:
        f.write(f"# Last Updated: {now_str}\n\n")
        
        for channel_name, page_url in CHANNELS.items():
            stream_url = get_trkvz_api_stream_url(page_url)
            
            if stream_url:
                # Video API'sinden gelen kaynak doğrudan secure URL parametresine eklenir
                secure_api_url = f"https://securevideotoken.tmgrup.com.tr/webtv/secure?url={quote(stream_url, safe=':/?=&')}"
                f.write(f"{channel_name} | Referer: {page_url} | API: {secure_api_url}\n")
                print(f"[OK] {channel_name} -> {stream_url}")
            else:
                print(f"[HATA] {channel_name} için API kaynağı çekilemedi.")

if __name__ == "__main__":
    main()
