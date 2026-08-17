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

MAPPING_WEBSITEID_HLSURL = {
    "9BBE055A-4CF6-4BC3-A675-D40E89B55B91": "https://trkvz.daioncdn.net/aspor/aspor.m3u8?ce=3&app=45f847c4-04e8-419a-a561-2ebf87084765",
    "0C1BC8FF-C3B1-45BE-A95B-F7BB9C8B03ED": "https://trkvz.daioncdn.net/a2tv/a2tv.m3u8?ce=3&app=59363a60-be96-4f73-9eff-355d0ff2c758",
    "AAE2E325-4EAE-45B7-B017-26FD7DDB6CE4": "https://trkvz.daioncdn.net/minikago/minikago.m3u8?app=web&ce=3",
    "01ED59F2-4067-4945-8204-45F6C6DB4045": "https://trkvz.daioncdn.net/minikago_cocuk/minikago_cocuk.m3u8?app=web&ce=3",
}
VIDEOID_LIVE = "00000000-0000-0000-0000-000000000000"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

def process_channel(channel_name: str, page_url: str):
    try:
        # 1. Adım: Kanal sayfasının HTML içeriğini al ve ID'leri çek
        res = requests.get(page_url, headers=HEADERS, timeout=10)
        if res.status_code != 200:
            return None, None

        soup = BeautifulSoup(res.text, "html.parser")
        div = soup.find(attrs={"data-videoid": True, "data-websiteid": True})
        
        if not div:
            match = re.search(r"""var\s+tmdPlayer\s*=\s*(?P<q>["'])(.*?)(?P=q)""", res.text, re.DOTALL)
            if match:
                p_soup = BeautifulSoup(match.group(2), "html.parser")
                div = p_soup.find(attrs={"data-videoid": True, "data-websiteid": True})

        if not div:
            return None, None

        video_id = div["data-videoid"]
        website_id = div["data-websiteid"]

        # 2. Adım: Turkuvaz Video API'sinden ham akış adresini al
        api_endpoint = f"https://videojs.tmgrup.com.tr/getvideo/{website_id}/{video_id}"
        api_res = requests.get(api_endpoint, headers=HEADERS, timeout=10).json()

        if not api_res.get("success"):
            return None, None

        video_data = api_res.get("video", {})
        raw_hls_url = video_data.get("VideoSmilUrl") or video_data.get("VideoUrl") or video_data.get("Url")

        if video_id == VIDEOID_LIVE:
            raw_hls_url = MAPPING_WEBSITEID_HLSURL.get(website_id.upper(), raw_hls_url)

        if not raw_hls_url:
            return None, None

        # 3. Adım: Secure Token API adresini oluştur
        secure_api_url = f"https://securevideotoken.tmgrup.com.tr/webtv/secure?url={quote(raw_hls_url, safe=':/?=&')}"

        # 4. Adım: Referer başlığı göndererek anlık geçerli imzalı M3U8 adresini çöz
        token_headers = {
            "User-Agent": HEADERS["User-Agent"],
            "Referer": page_url
        }
        token_res = requests.get(secure_api_url, headers=token_headers, timeout=10).json()

        active_signed_url = None
        if token_res.get("Success"):
            active_signed_url = token_res.get("Url")

        return secure_api_url, active_signed_url

    except Exception as e:
        print(f"[{channel_name}] Hata oluştu: {e}")
        return None, None

def main():
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    with open("trkvz-tokens.txt", "w", encoding="utf-8") as f_txt, \
         open("playlist.m3u", "w", encoding="utf-8") as f_m3u:

        f_txt.write(f"# Last Updated: {now_str}\n\n")
        f_m3u.write("#EXTM3U\n")

        for channel_name, page_url in CHANNELS.items():
            print(f"İşleniyor: {channel_name}...")
            secure_api_url, active_signed_url = process_channel(channel_name, page_url)

            if secure_api_url:
                # TXT Çıktısı Yapılandırması
                f_txt.write(f"--- {channel_name} ---\n")
                f_txt.write(f"Referer: {page_url}\n")
                f_txt.write(f"Secure Token API: {secure_api_url}\n")
                if active_signed_url:
                    f_txt.write(f"Aktif Imzali M3U8: {active_signed_url}\n")
                f_txt.write("\n")

                # M3U Çalma Listesi Çıktısı Yapılandırması (VLC / IPTV uyumlu)
                stream_for_m3u = active_signed_url if active_signed_url else secure_api_url
                f_m3u.write(f'#EXTINF:-1 tvg-name="{channel_name}",{channel_name}\n')
                f_m3u.write(f"#EXTVLCOPT:http-referrer={page_url}\n")
                f_m3u.write(f"{stream_for_m3u}\n\n")

                print(" -> [BAŞARILI]")
            else:
                print(" -> [BAŞARISIZ]")

    print("\nTamamlandı: 'tokens.txt' ve 'playlist.m3u' dosyaları güncellendi.")

if __name__ == "__main__":
    main()
