from curl_cffi import requests
import re
import json

CHANNELS = [
    {"name": "ATV", "slug": "atv", "referer": "https://www.atv.com.tr/", "video_id": "atvhd"},
    {"name": "A Haber", "slug": "ahaber", "referer": "https://www.ahaber.com.tr/", "video_id": "ahaber"},
    {"name": "A News", "slug": "anews", "referer": "https://anews.com.tr/", "video_id": "anewshd"},
    {"name": "A Para", "slug": "apara", "referer": "https://www.apara.com.tr/", "video_id": "aparahd"},
    {"name": "A Spor", "slug": "aspor", "referer": "https://www.aspor.com.tr/", "video_id": "asporhd"},
    {"name": "A2 TV", "slug": "a2tv", "referer": "https://www.a2tv.com.tr/", "video_id": "a2tv"},
    {"name": "Minika Çocuk", "slug": "minikacocuk", "referer": "https://www.minikacocuk.com.tr/", "video_id": "minikacocuk"},
    {"name": "Minika GO", "slug": "minikago", "referer": "https://www.minikago.com.tr/", "video_id": "minikago"},
    {"name": "Vav TV", "slug": "vavtv", "referer": "https://www.vavtv.com.tr/", "video_id": "vavtv"},
    {"name": "ATV Avrupa", "slug": "atvavrupa", "referer": "https://www.atvavrupa.tv/", "video_id": "atvavrupa"}
]

def capture_ercdn_m3u8(channel):
    session = requests.Session()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Referer": channel["referer"],
        "Origin": channel["referer"].rstrip('/'),
        "Accept": "*/*",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    session.headers.update(headers)

    try:
        # Turkuvaz güvenli video token servisinin doğrudan çağrı yapısı
        # Bu yöntem sayfa içindeki JS karmaşasını atlayarak direkt token üretir
        token_api_url = f"https://securevideotoken.tmgrup.com.tr/webtv/secure?json=true&q={channel['video_id']}"
        
        res = session.get(token_api_url, impersonate="chrome", timeout=15)
        
        if res.status_code == 200:
            # Gelen JSON yanıtı içerisindeki m3u8 / ercdn linkini ayıkla
            try:
                data = res.json()
                # Yanıt yapısına göre url alanını yakala
                stream_url = data.get("url") or data.get("Stream") or data.get("Data")
                if stream_url and "ercdn.net" in stream_url:
                    return stream_url
            except json.JSONDecodeError:
                pass
            
            # Eğer JSON yerine direkt düz metin içinde döndüyse regex ile çek
            found_links = re.findall(r'https?://[^\s<>"]+?ercdn\.net[^\s<>"]+?\.m3u8[^\s<>"]*', res.text)
            if found_links:
                for link in found_links:
                    if "radyo" not in link.lower():
                        return link

        # Yedek olarak doğrudan canlı yayın sayfasını tarama
        embed_fallback = f"https://www.atv.com.tr/canli-yayin" if "atv" in channel["slug"] else channel["referer"] + "canli-yayin"
        fallback_res = session.get(embed_fallback, impersonate="chrome", timeout=15)
        fallback_links = re.findall(r'https?://[^\s<>"]+?ercdn\.net[^\s<>"]+?\.m3u8[^\s<>"]*', fallback_res.text)
        
        for link in fallback_links:
            if "radyo" not in link.lower():
                return link

        return None
    except Exception as e:
        print(f"[HATA] {channel['name']} token alınamadı: {e}")
        return None

def build_playlist():
    playlist_lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:3"
    ]

    print("Turkuvaz token API'leri taranıyor...\n")
    success_count = 0

    for ch in CHANNELS:
        stream_url = capture_ercdn_m3u8(ch)
        
        if stream_url and "ercdn.net" in stream_url:
            playlist_lines.append(f'#EXTINF:-1 tvg-name="{ch["name"]}" group-title="Turkuvaz",{ch["name"]}')
            playlist_lines.append(stream_url)
            print(f"[BAŞARILI] {ch['name']} -> {stream_url}")
            success_count += 1
        else:
            print(f"[REDDEDİLDİ] {ch['name']} için token alınamadı.")

    if success_count > 0:
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(playlist_lines) + "\n")
        print(f"\nplaylist.m3u başarıyla güncellendi ({success_count} kanal).")
    else:
        print("\n[UYARI] Hiçbir kanal için kaynak bulunamadı, dosya değiştirilmedi.")

if __name__ == "__main__":
    build_playlist()
