import requests

# Kanal isimleri ve karşılık gelen slug değerleri
CHANNELS = {
    "ATV": "atv",
    "A Haber": "ahaber",
    "A News": "anews",
    "A Para": "apara",
    "A Spor": "aspor",
    "A2 TV": "a2tv",
    "Minika Çocuk": "minikacocuk",
    "Minika GO": "minikago",
    "Vav TV": "vavtv",
    "ATV Avrupa": "atvavrupa"
}

# Şablon URL
BASE_URL = "https://uzunmuhalefet.unaux.com/trkvz.php?kanal={slug}&.m3u8"

def build_playlist():
    playlist_lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:3"
    ]

    for name, slug in CHANNELS.items():
        # {slug} alanını ilgili kanalla dolduruyoruz
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
