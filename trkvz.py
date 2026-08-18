import requests
import re

# Turkuvaz / CNN Türk veya ilgili yayın adresi
TARGET_URL = "https://securevideotoken.tmgrup.com.tr/webtv/secure" # Kendi istek attığınız URL

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://atvavrupa.tv/",
    "Origin": "https://atvavrupa.tv"
}

def fetch_stream_token():
    try:
        # Doğrudan VPS'in Türkiye IP'si ile istek atılır (Sıfır Proxy / Yüksek Hız)
        response = requests.get(TARGET_URL, headers=HEADERS, timeout=5)
        
        if response.status_code == 200:
            print("Yayın isteği başarılı! Status: 200")
            # M3U8 veya Token alma işlemleriniz...
            stream_data = response.text
            
            # Örnek: M3U dosyasına yazma
            with open("playlist.m3u", "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                f.write("#EXTINF:-1, Kanal ATV\n")
                f.write(f"{stream_data}\n")
                
            print("playlist.m3u başarıyla güncellendi.")
        else:
            print(f"Hata Oluştu! HTTP Kodu: {response.status_code}")

    except Exception as e:
        print(f"Bağlantı Hatası: {e}")

if __name__ == "__main__":
    fetch_stream_token()
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
