from playwright.sync_api import sync_playwright
from streamlink import Streamlink
import requests

CHANNELS = [
    {"name": "ATV", "slug": "atv", "web_url": "https://www.atv.com.tr/canli-yayin"},
    {"name": "A Haber", "slug": "ahaber", "web_url": "https://www.ahaber.com.tr/canli-yayin"},
    {"name": "A News", "slug": "anews", "web_url": "https://www.anews.com.tr/anews-hd"},
    {"name": "A Para", "slug": "apara", "web_url": "https://www.apara.com.tr/apara-canli-yayin"},
    {"name": "A Spor", "slug": "aspor", "web_url": "https://www.aspor.com.tr/aspor-canli-yayin"},
    {"name": "A2 TV", "slug": "a2tv", "web_url": "https://www.a2tv.com.tr/canli-yayin"},
    {"name": "Minika Çocuk", "slug": "minikacocuk", "web_url": "https://www.minikacocuk.com.tr/canli-yayin"},
    {"name": "Minika GO", "slug": "minikago", "web_url": "https://www.minikago.com.tr/canli-yayin"},
    {"name": "Vav TV", "slug": "vavtv", "web_url": "https://www.vavtv.com.tr/canli-yayin"},
    {"name": "ATV Avrupa", "slug": "atvavrupa", "web_url": "https://www.atvavrupa.tv/canli-yayin"}
]

# Unaux üzerinden sunucunun GMT+3 (Türkiye) saatiyle ürettiği taze linki çeker
UNAUX_RESOLVER = "https://uzunmuhalefet.unaux.com/trkvz.php?kanal={slug}&.m3u8"

def get_stream_via_unaux(slug):
    """Tarayıcıyı GMT+3 simüle ederek çalıştırır ve taze token'ı yakalar."""
    with sync_playwright() as p:
        # Tarayıcıyı Türkiye saatiyle senkronize başlat
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            locale="tr-TR",
            timezone_id="Europe/Istanbul" # GMT+3/UTC+3 zorunlu kılınır
        )
        page = context.new_page()
        found_urls = []

        def handle_response(response):
            if "ercdn.net" in response.url and "st=" in response.url:
                found_urls.append(response.url)

        page.on("response", handle_response)
        
        try:
            page.goto(UNAUX_RESOLVER.format(slug=slug), timeout=15000)
            page.wait_for_timeout(3000)
        except:
            pass
        finally:
            browser.close()
        
        # En yüksek kaliteyi bul (1080p > 720p > diğerleri)
        for q in ["1080p", "720p", "576p", "360p"]:
            for u in found_urls:
                if f"_{q}" in u:
                    return u
        return found_urls[-1] if found_urls else None

def build_playlist():
    playlist_lines = ["#EXTM3U", "#EXT-X-VERSION:3"]
    print("GMT+3 Zaman Damgalı Taze Token Çözücü Başlatıldı...\n")

    for ch in CHANNELS:
        url = get_stream_via_unaux(ch["slug"])
        if url:
            playlist_lines.append(f'#EXTINF:-1 tvg-name="{ch["name"]}" group-title="Turkuvaz",{ch["name"]}')
            playlist_lines.append(url)
            print(f"[BAŞARILI] {ch['name']} - Kalite: Yüksek")
        else:
            print(f"[BAŞARISIZ] {ch['name']}")

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(playlist_lines) + "\n")

if __name__ == "__main__":
    build_playlist()
