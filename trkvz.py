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

UNAUX_RESOLVER = "https://uzunmuhalefet.unaux.com/trkvz.php?kanal={slug}&.m3u8"

def get_tr_proxy_from_proxyscrape():
    """ProxyScrape API üzerinden anlık Türkiye IP'si çeker."""
    api_url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=displayproxies&protocol=http&country=tr&timeout=5000"
    try:
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            proxies = response.text.strip().split("\n")
            for p in proxies:
                clean_p = p.strip()
                if clean_p:
                    return f"http://{clean_p}"
    except Exception:
        pass
    return None

def get_stream_via_unaux(slug, proxy_url):
    """Unaux ve Playwright ile orijinal token'lı linki yakalar."""
    with sync_playwright() as p:
        launch_args = {"headless": True, "args": ["--no-sandbox", "--disable-setuid-sandbox"]}
        if proxy_url:
            launch_args["proxy"] = {"server": proxy_url}

        try:
            browser = p.chromium.launch(**launch_args)
        except Exception:
            return None

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            locale="tr-TR"
        )
        page = context.new_page()
        target_url = UNAUX_RESOLVER.format(slug=slug)
        captured_url = None

        def handle_response(response):
            nonlocal captured_url
            url = response.url
            if "ercdn.net" in url and ".m3u8" in url and "radyo" not in url.lower():
                if "st=" in url:
                    captured_url = url

        page.on("response", handle_response)

        try:
            page.goto(target_url, timeout=12000, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            if not captured_url and "ercdn.net" in page.url and "radyo" not in page.url.lower():
                captured_url = page.url
        except Exception:
            pass
        finally:
            browser.close()
            
        return captured_url

def get_stream_via_streamlink(web_url):
    """Streamlink ile orijinal akış linkini çözer."""
    try:
        session = Streamlink()
        session.set_option("http-headers", {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        })
        streams = session.streams(web_url)
        if streams and "best" in streams:
            return streams["best"].to_url()
    except Exception:
        pass
    return None

def resolve_channel(ch):
    proxy = get_tr_proxy_from_proxyscrape()
    
    # 1. Unaux + Proxy
    url = get_stream_via_unaux(ch["slug"], proxy)
    if url and "ercdn.net" in url:
        print(f"[{ch['name']}] -> Unaux (Proxy) ile alındı.")
        return url

    # 2. Unaux Direkt
    url = get_stream_via_unaux(ch["slug"], None)
    if url and "ercdn.net" in url:
        print(f"[{ch['name']}] -> Unaux (Direkt) ile alındı.")
        return url

    # 3. Streamlink Fallback
    url = get_stream_via_streamlink(ch["web_url"])
    if url:
        print(f"[{ch['name']}] -> Streamlink ile alındı.")
        return url

    return None

def build_playlist():
    playlist_lines = ["#EXTM3U", "#EXT-X-VERSION:3"]
    success_count = 0

    print("Dinamik Token Çözücü Çalıştırılıyor...\n")

    for ch in CHANNELS:
        stream_url = resolve_channel(ch)
        if stream_url:
            playlist_lines.append(f'#EXTINF:-1 tvg-name="{ch["name"]}" group-title="Turkuvaz",{ch["name"]}')
            playlist_lines.append(stream_url)
            success_count += 1
            print(f"[BAŞARILI] {ch['name']}\n")
        else:
            print(f"[BAŞARISIZ] {ch['name']}\n")

    if success_count > 0:
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(playlist_lines) + "\n")
        print(f"playlist.m3u güncellendi ({success_count} kanal).")
    else:
        print("[UYARI] Güncelleme yapılmadı.")

if __name__ == "__main__":
    build_playlist()
