from playwright.sync_api import sync_playwright
from streamlink import Streamlink
import requests
import time
from datetime import datetime, timedelta, timezone

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

def get_tr_timestamp():
    """Türkiye saat dilimine (UTC+3) göre güncel Unix timestamp ve 2 saat sonrasının bitiş süresini hesaplar."""
    tr_tz = timezone(timedelta(hours=3))
    now_tr = datetime.now(tr_tz)
    # Token'ın geçerlilik süresini Türkiye saatine göre 3 saat sonrasına ayarla
    expire_tr = now_tr + timedelta(hours=3)
    return int(now_tr.timestamp()), int(expire_tr.timestamp())

def adjust_token_timestamp(url):
    """Yakalanan linkteki süre parametrelerini Türkiye saatine göre günceller."""
    if not url or "ercdn.net" not in url:
        return url
    
    current_ts, expire_ts = get_tr_timestamp()
    
    # URL içindeki 'st=' ve 'e=' parametrelerini TR zaman damgasıyla yenile
    if "e=" in url:
        import re
        url = re.sub(r'e=\d+', f'e={expire_ts}', url)
    
    return url

def get_tr_proxy_from_proxyscrape():
    """ProxyScrape API üzerinden anlık Türkiye IP'si çeker."""
    api_url = "https://api.proxyscrape.com/v4/free-proxy-list/get?request=displayproxies&protocol=http&country=tr&timeout=5000"
    try:
        print("ProxyScrape'den Türkiye lokasyonlu proxy aranıyor...")
        response = requests.get(api_url, timeout=8)
        if response.status_code == 200:
            proxies = response.text.strip().split("\r\n")
            if not proxies or proxies[0] == "":
                proxies = response.text.strip().split("\n")
            
            for p in proxies:
                clean_p = p.strip()
                if clean_p:
                    proxy_url = f"http://{clean_p}"
                    print(f"[PROXY ADAYI] {proxy_url}")
                    return proxy_url
    except Exception as e:
        print(f"[PROXY API HATA]: {e}")
    
    print("[BİLGİ] Proxy alınamadı, doğrudan bağlantı kullanılacak.")
    return None

def get_stream_via_unaux(slug, proxy_url):
    """Playwright ile Unaux üzerinden token yakalar."""
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
            page.goto(target_url, timeout=10000, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)
            if not captured_url and "ercdn.net" in page.url and "radyo" not in page.url.lower():
                captured_url = page.url
        except Exception:
            pass
        finally:
            browser.close()
            
        return adjust_token_timestamp(captured_url)

def get_stream_via_streamlink(web_url, proxy_url):
    """Streamlink ile doğrudan çözer."""
    try:
        session = Streamlink()
        
        if proxy_url:
            session.set_option("http-proxy", proxy_url)

        session.set_option("http-headers", {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        })
        
        streams = session.streams(web_url)
        if streams and "best" in streams:
            raw_url = streams["best"].to_url()
            return adjust_token_timestamp(raw_url)
    except Exception:
        pass
    return None

def resolve_channel(ch):
    proxy = get_tr_proxy_from_proxyscrape()
    
    print(f"[{ch['name']}] Unaux (Proxy ile) deneniyor...")
    url = get_stream_via_unaux(ch["slug"], proxy)
    
    if url and "ercdn.net" in url:
        print(f"[{ch['name']}] -> Unaux (Proxy) başarılı.")
        return url
        
    if proxy:
        print(f"[{ch['name']}] Proxy başarısız oldu, doğrudan Unaux deneniyor...")
        url = get_stream_via_unaux(ch["slug"], None)
        if url and "ercdn.net" in url:
            print(f"[{ch['name']}] -> Unaux (Direkt) başarılı.")
            return url

    print(f"[{ch['name']}] Streamlink Fallback deneniyor...")
    url = get_stream_via_streamlink(ch["web_url"], None)
    
    if url:
        print(f"[{ch['name']}] -> Streamlink başarılı.")
        return url
        
    return None

def build_playlist():
    playlist_lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:3"
    ]

    print("\nTürkiye Zaman Damgalı Akış Çözücü Başlatıldı...\n")
    success_count = 0

    for ch in CHANNELS:
        stream_url = resolve_channel(ch)
        
        if stream_url:
            playlist_lines.append(f'#EXTINF:-1 tvg-name="{ch["name"]}" group-title="Turkuvaz",{ch["name"]}')
            playlist_lines.append(stream_url)
            print(f"[BAŞARILI] {ch['name']} eklendi.\n")
            success_count += 1
        else:
            print(f"[REDDEDİLDİ] {ch['name']} çözülemedi.\n")

    if success_count > 0:
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(playlist_lines) + "\n")
        print(f"playlist.m3u başarıyla güncellendi ({success_count} kanal).")
    else:
        print("\n[UYARI] Hiçbir kanal bulunamadı, dosya değiştirilmedi.")

if __name__ == "__main__":
    build_playlist()
