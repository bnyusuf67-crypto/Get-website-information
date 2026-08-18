# Kanal isimleri ve slug bilgileri
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

BASE_URL = "https://uzunmuhalefet.unaux.com/trkvz.php?kanal={slug}&.m3u8"

def build_playlist():
    playlist_lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:3"
    ]

    for ch in CHANNELS:
        name = ch["name"]
        slug = ch["slug"]
        stream_url = BASE_URL.format(slug=slug)
        
        playlist_lines.append(f'#EXTINF:-1 tvg-name="{name}" group-title="Turkuvaz",{name}')
        playlist_lines.append(stream_url)
        print(f"[EKLENDİ] {name} -> {stream_url}")

    # playlist.m3u dosyasına yazma
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(playlist_lines) + "\n")
        
    print("\nplaylist.m3u başarıyla oluşturuldu.")

if __name__ == "__main__":
    build_playlist()
