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

def capture_ercdn_m3u8(slug, referer_url):
    # Her istek için taze bir oturum açıyoruz (Çerez çakışmalarını önlemek için)
    session = requests.Session()
    
    # 1. & 4. Engel (Header & Referer Filtresi): Gerçek bir Chrome tarayıcısının tüm kimlik bilgileri
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Referer": referer_url,
        "Origin": referer_url.rstrip('/'),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Ch-Ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }
    
    session.headers.update(headers)

    try:
        # 2. Engel (Cookie / JS Challenge): Önce ana sayfaya bağlanıp iFastNet çerez motorunu tetikliyoruz
        session.get("https://uzunmuhalefet.unaux.com/", impersonate="chrome", timeout=10)

        # 3. Engel (Datacenter IP / WAF): impersonate="chrome" ile TLS parmak izini gizleyerek isteği atıyoruz
        target_url = RESOLVER_URL.format(slug=slug)
        response = session.get(
            target_url, 
            impersonate="chrome", 
            allow_redirects=True, 
            timeout=15
        )
        
        # Son ulaşılan URL ercdn içeriyorsa doğrudan yakala
        if "ercdn.net" in response.url:
            return response.url
            
        # Yönlendirme geçmişindeki (Redirect History) ercdn adresini tara
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

    print("Tüm güvenlik katmanları aşırı yüklenerek taranıyor...\n")
    success_count = 0

    for ch in CHANNELS:
        name = ch["name"]
        slug = ch["slug"]
        referer = ch["referer"]
        
        stream_url = capture_ercdn_m3u8(slug, referer)
        
        # Sadece ercdn.net içeren sağlam linkleri listeye ekle, unaux'yu asla sokma
        if stream_url and "ercdn.net" in stream_url:
            playlist_lines.append(f'#EXTINF:-1 tvg-name="{name}" group-title="Turkuvaz",{name}')
            playlist_lines.append(stream_url)
            print(f"[BAŞARILI] {name} -> {stream_url}")
            success_count += 1
        else:
            print(f"[ENGELLENDİ/BAŞARISIZ] {name} için ercdn alınamadı.")

    if success_count > 0:
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(playlist_lines) + "\n")
        print(f"\nplaylist.m3u başarıyla güncellendi ({success_count} kanal).")
    else:
        print("\n[KRİTİK UYARI] Tüm kanallar engellendi veya ercdn alınamadı. Dosya değiştirilmedi.")

if __name__ == "__main__":
    build_playlist()
