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
    target_url = RESOLVER_URL.format(slug=slug)
    
    headers = {
        "Referer": referer_url,
        "Origin": referer_url.rstrip('/'),
        "Accept": "*/*"
    }

    try:
        # impersonate="chrome" ile gerçek bir tarayıcının TLS parmak izi taklit edilir
        response = requests.get(
            target_url, 
            headers=headers, 
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

    print("curl-cffi ile kanal kaynakları taranıyor...\n")

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
