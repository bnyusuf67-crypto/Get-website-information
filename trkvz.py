from curl_cffi import requests

# List of Dicts yapısı ve kanal bazlı referer tanımları
CHANNELS = [
    {"name": "ATV", "slug": "atv", "referer": "https://www.atv.com.tr/"},
    {"name": "A Haber", "slug": "ahaber", "referer": "https://www.ahaber.com.tr/"},
    {"name": "A News", "slug": "anews", "referer": "https://www.anews.com.tr/"},
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
    # Curl-cffi Session kullanarak çerez (Cookie Challenge) döngüsünü otomatik yönetiyoruz
    session = requests.Session()
    
    # Engelleme 1 & 4: Tam ve gerçekçi tarayıcı başlıkları (User-Agent, Referer, Origin, Accept)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": referer_url,
        "Origin": referer_url.rstrip('/'),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    })

    try:
        # Engelleme 2: Önce ana sayfaya istek atarak iFastNet/Unaux çerezlerini (__test vb.) topluyoruz
        session.get("https://uzunmuhalefet.unaux.com/", impersonate="chrome", timeout=10)

        # Engelleme 3 (Datacenter IP): impersonate="chrome" ile TLS imzamızı tarayıcı gibi gösterip WAF engellerini bypass ediyoruz
        target_url = RESOLVER_URL.format(slug=slug)
        response = session.get(
            target_url, 
            impersonate="chrome", 
            allow_redirects=True, 
            timeout=15
        )
        
        # Doğrudan son ulaşılan URL ercdn içeriyorsa
        if "ercdn.net" in response.url:
            return response.url
            
        # Yönlendirme geçmişindeki (History) ercdn adresini arama
        for req in response.history:
            location = req.headers.get("Location", "")
            if "ercdn.net" in location:
                return location
                
        return response.url
    except Exception as e:
        print(f"[HATA] {slug} çözülemedi: {e}")
        return None

def build_playlist():
    playlist_lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:3"
    ]

    print("Tüm güvenlik engelleri bypass edilerek kaynaklar taranıyor...\n")

    for ch in CHANNELS:
        name = ch["name"]
        slug = ch["slug"]
        referer = ch["referer"]
        
        stream_url = capture_ercdn_m3u8(slug, referer)
        
        if stream_url:
            playlist_lines.append(f'#EXTINF:-1 tvg-name="{name}" group-title="Turkuvaz",{name}')
            playlist_lines.append(stream_url)
            print(f"[EKLENDİ] {name} -> {stream_url}")
        else:
            print(f"[BAŞARISIZ] {name} alınamadı.")

    # playlist.m3u dosyasına kaydet
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(playlist_lines) + "\n")
        
    print("\nplaylist.m3u başarıyla güncellendi.")

if __name__ == "__main__":
    build_playlist()
