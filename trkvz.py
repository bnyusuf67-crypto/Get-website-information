import requests
import re
import os

CHANNELS = {
    "ATV": "https://www.atv.com.tr/canli-yayin",
    "A Haber": "https://www.ahaber.com.tr/canli-yayin",
    "A News": "https://www.anews.com.tr/live-stream",
    "A Para": "https://www.apara.com.tr/canli-yayin",
    "A Spor": "https://www.aspor.com.tr/canli-yayin",
    "A2 TV": "https://www.a2tv.com.tr/canli-yayin",
    "Minika Çocuk": "https://www.minikacocuk.com.tr/webtv/canli-yayin",
    "Minika GO": "https://www.minikago.com.tr/webtv/canli-yayin",
    "Vav TV": "https://www.vavtv.com.tr/canli-yayin",
    "ATV Avrupa": "https://www.atvavrupa.tv/canli-yayin"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.atv.com.tr/"
}

def get_m3u8_url(page_url):
    try:
        response = requests.get(page_url, headers=HEADERS, timeout=8)
        if response.status_code == 200:
            # Sayfa içinde geçen m3u8 linkini regex ile bulur
            match = re.search(r'https?://[^\s\'"]+\.m3u8[^\s\'"]*', response.text)
            if match:
                return match.group(0)
        else:
            print(f"[HATA] {page_url} - Status: {response.status_code}")
    except Exception as e:
        print(f"[BAĞLANTI HATASI] {page_url}: {e}")
    return None

def main():
    playlist_lines = ["#EXTM3U"]
    success_count = 0

    print("Kanal linkleri taranıyor...")
    for name, url in CHANNELS.items():
        m3u8_link = get_m3u8_url(url)
        if m3u8_link:
            print(f"[BAŞARILI] {name} -> {m3u8_link[:50]}...")
            playlist_lines.append(f"#EXTINF:-1 tvg-name=\"{name}\",{name}")
            playlist_lines.append(m3u8_link)
            success_count += 1
        else:
            print(f"[BAŞARISIZ] {name} linki alınamadı.")

    # Eğer hiçbir kanal alınamadıysa hata ver ki Workflow Fallback adımı devreye girsin
    if success_count == 0:
        print("HİÇBİR KANAL ÇEKİLEMEDİ! Geo-Block veya IP engeline takılındı.")
        exit(1)

    # M3U dosyasına yaz
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(playlist_lines))
    print("playlist.m3u başarıyla güncellendi.")

if __name__ == "__main__":
    main()
