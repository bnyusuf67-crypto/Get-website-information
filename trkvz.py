import requests

CHANNELS = [
    {"name": "ATV", "slug": "atv"},
    {"name": "A Haber", "slug": "ahaber"},
    {"name": "A News", "slug": "anews"},
    {"name": "A Para", "slug": "apara"},
    {"name": "A Spor", "slug": "aspor"},
    {"name": "A2 TV", "slug": "a2tv"},
    {"name": "Minika Çocuk", "slug": "minikacocuk"},
    {"name": "Minika GO", "slug": "minikago"},
    {"name": "Vav TV", "slug": "vavtv"},
    {"name": "ATV Avrupa", "slug": "atvavrupa"}
]

RESOLVER_URL = "https://uzunmuhalefet.unaux.com/trkvz.php?kanal={slug}&.m3u8"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
}

def resolve_token_m3u8(slug):
    url = RESOLVER_URL.format(slug=slug)
    try:
        # allow_redirects=True sayesinde HTML okumadan doğrudan 302 yönlendirmesini takip eder
        response = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        
        # Yönlendirilen son canlı m3u8 adresi
        final_url = response.url
        
        if ".m3u8" in final_url and response.status_code == 200:
            return final_url
        else:
            print(f"[UYARI] {slug} için yönlendirme m3u8 içermiyor: {final_url}")
            return None
    except Exception as e:
        print(f"[HATA] {slug} kanalı çözülemedi: {e}")
        return None

def build_playlist():
    playlist_lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:3"
    ]

    print("Doğrudan yönlendirme üzerinden token'lı m3u8 adresleri çözülüyor...\n")

    for ch in CHANNELS:
        name = ch["name"]
        slug = ch["slug"]
        
        real_stream_url = resolve_token_m3u8(slug)
        
        if real_stream_url:
            playlist_lines.append(f'#EXTINF:-1 tvg-name="{name}" group-title="Turkuvaz",{name}')
            playlist_lines.append(real_stream_url)
            print(f"[ÇÖZÜLDÜ] {name} -> {real_stream_url}")
        else:
            print(f"[BAŞARISIZ] {name} için link alınamadı.")

    # playlist.m3u dosyasına yazma
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(playlist_lines) + "\n")
        
    print("\nplaylist.m3u başarıyla oluşturuldu.")

if __name__ == "__main__":
    build_playlist()
