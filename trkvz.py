from curl_cffi import requests
import re

CHANNELS = [
    {"name": "ATV", "slug": "atv", "referer": "https://www.atv.com.tr/", "embed_url": "https://www.atv.com.tr/canli-yayin"},
    {"name": "A Haber", "slug": "ahaber", "referer": "https://www.ahaber.com.tr/", "embed_url": "https://www.ahaber.com.tr/canli-yayin"},
    {"name": "A News", "slug": "anews", "referer": "https://anews.com.tr/", "embed_url": "https://www.anews.com.tr/anews-hd"},
    {"name": "A Para", "slug": "apara", "referer": "https://www.apara.com.tr/", "embed_url": "https://www.apara.com.tr/apara-canli-yayin"},
    {"name": "A Spor", "slug": "aspor", "referer": "https://www.aspor.com.tr/", "embed_url": "https://www.aspor.com.tr/aspor-canli-yayin"},
    {"name": "A2 TV", "slug": "a2tv", "referer": "https://www.a2tv.com.tr/", "embed_url": "https://www.a2tv.com.tr/canli-yayin"},
    {"name": "Minika Çocuk", "slug": "minikacocuk", "referer": "https://www.minikacocuk.com.tr/", "embed_url": "https://www.minikacocuk.com.tr/canli-yayin"},
    {"name": "Minika GO", "slug": "minikago", "referer": "https://www.minikago.com.tr/", "embed_url": "https://www.minikago.com.tr/canli-yayin"},
    {"name": "Vav TV", "slug": "vavtv", "referer": "https://www.vavtv.com.tr/", "embed_url": "https://www.vavtv.com.tr/canli-yayin"},
    {"name": "ATV Avrupa", "slug": "atvavrupa", "referer": "https://www.atvavrupa.tv/", "embed_url": "https://www.atvavrupa.tv/canli-yayin"}
]

def capture_ercdn_m3u8(channel):
    session = requests.Session()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Referer": channel["referer"],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    session.headers.update(headers)

    try:
        # 1. Adım: Canlı yayın sayfasına bağlanıp ercdn linklerini arıyoruz
        res = session.get(channel["embed_url"], impersonate="chrome", timeout=15)
        
        found_links = re.findall(r'https?://[^\s<>"]+?ercdn\.net[^\s<>"]+?\.m3u8', res.text)
        if found_links:
            # Radyo linklerini ele, sadece TV akışını al
            for link in found_links:
                if "radyo" not in link.lower():
                    return link

        # 2. Adım: Secure Video Token servislerini tarama
        token_match = re.search(r'securevideotoken\.tmgrup\.com\.tr[^\s<>"]+', res.text)
        if token_match:
            token_url = "https://" + token_match.group(0)
            token_res = session.get(token_url, impersonate="chrome", timeout=10)
            sub_links = re.findall(r'https?://[^\s<>"]+?ercdn\.net[^\s<>"]+?\.m3u8', token_res.text)
            if sub_links:
                for link in sub_links:
                    if "radyo" not in link.lower():
                        return link

        return None
    except Exception as e:
        print(f"[HATA] {channel['name']} çözülemedi: {e}")
        return None

def build_playlist():
    playlist_lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:3"
    ]

    print("Turkuvaz TV kaynakları doğrudan taranıyor...\n")
    success_count = 0

    for ch in CHANNELS:
        stream_url = capture_ercdn_m3u8(ch)
        
        if stream_url and "ercdn.net" in stream_url:
            playlist_lines.append(f'#EXTINF:-1 tvg-name="{ch["name"]}" group-title="Turkuvaz",{ch["name"]}')
            playlist_lines.append(stream_url)
            print(f"[BAŞARILI] {ch['name']} -> {stream_url}")
            success_count += 1
        else:
            print(f"[REDDEDİLDİ] {ch['name']} için geçerli TV kaynağı bulunamadı.")

    if success_count > 0:
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(playlist_lines) + "\n")
        print(f"\nplaylist.m3u başarıyla güncellendi ({success_count} kanal).")
    else:
        print("\n[UYARI] Hiçbir kanal için ercdn kaynağı bulunamadı, dosya değiştirilmedi.")

if __name__ == "__main__":
    build_playlist()
