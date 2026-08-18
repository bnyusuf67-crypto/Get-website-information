from curl_cffi import requests

CHANNELS = [
    {"name": "ATV", "slug": "atv", "referer": "https://www.atv.com.tr/"},
    {"name": "A Haber", "slug": "ahaber", "referer": "https://www.ahaber.com.tr/"},
    {"name": "A News", "slug": "anews", "referer": "https://anews.com.tr/"},
    {"name": "A Para", "slug": "apara", "referer": "https://www.apara.com.tr/"},
    {"name": "A Spor", "slug": "aspor", "referer": "https://www.aspor.com.tr/"},
    {"name": "A2 TV", "slug": "a2tv", "referer": "https://www.a2tv.com.tr/"},
    {"name": "Minika Çocuk", "slug": "minikacocuk", "referer": "https://www.minikacocuk.com.tr/"},
    {"name": "Minika GO", "slug": "minikago", "referer": "https://www.minikago.com.tr/"},
    {"name": "Vav TV", "slug": "vavtv", "referer": "https://www.vavtv.com.tr/"},
    {"name": "ATV Avrupa", "slug": "atvavrupa", "referer": "https://www.atvavrupa.tv/"}
]

RESOLVER_URL = "https://uzunmuhalefet.unaux.com/trkvz.php?kanal={slug}&.m3u8"

# Eğer proxy kullanacaksanız burayı doldurabilirsiniz (Örn: Türkiye lokasyonlu bir proxy)
# Kullanmayacaksanız None yapabilirsiniz.
USE_PROXY = True 
PROXIES = {
    "http": "http://192.168.1.116",
    "https": "http://192.168.1.116"
} if USE_PROXY else None

def capture_ercdn_m3u8(slug, referer_url):
    session = requests.Session()
    
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Referer": referer_url,
        "Origin": referer_url.rstrip('/'),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
    })

    try:
        # Ana sayfa çerez doğrulaması (Proxy varsa proxy ile)
        session.get("https://uzunmuhalefet.unaux.com/", impersonate="chrome", proxies=PROXIES, timeout=10)

        target_url = RESOLVER_URL.format(slug=slug)
        response = session.get(
            target_url, 
            impersonate="chrome", 
            proxies=PROXIES,
            allow_redirects=True, 
            timeout=15
        )
        
        if "ercdn.net" in response.url:
            return response.url
            
        for req in response.history:
            location = req.headers.get("Location", "")
            if "ercdn.net" in location:
                return location
                
        return None
    except Exception as e:
        print(f"[AĞ HATASI] {slug}: {e}")
        return None

def build_playlist():
    playlist_lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:3"
    ]

    print("Proxy ve güvenlik filtreleriyle taranıyor...\n")
    success_count = 0

    for ch in CHANNELS:
        name = ch["name"]
        slug = ch["slug"]
        referer = ch["referer"]
        
        stream_url = capture_ercdn_m3u8(slug, referer)
        
        if stream_url and "ercdn.net" in stream_url:
            playlist_lines.append(f'#EXTINF:-1 tvg-name="{name}" group-title="Turkuvaz",{name}')
            playlist_lines.append(stream_url)
            print(f"[BAŞARILI] {name} -> {stream_url}")
            success_count += 1
        else:
            print(f"[REDDEDİLDİ] {name} için geçerli ercdn kaynağı alınamadı.")

    if success_count > 0:
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(playlist_lines) + "\n")
        print(f"\nplaylist.m3u başarıyla güncellendi ({success_count} kanal).")
    else:
        print("\n[UYARI] Hiçbir kanal için ercdn kaynağı bulunamadı, dosya değiştirilmedi.")

if __name__ == "__main__":
    build_playlist()
