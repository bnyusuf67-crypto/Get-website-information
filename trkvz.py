from playwright.sync_api import sync_playwright

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

def capture_ercdn_with_browser(slug):
    with sync_playwright() as p:
        # Tarayıcıyı headless (ekransız) modda başlatıyoruz
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            locale="tr-TR"
        )
        page = context.new_page()
        
        target_url = RESOLVER_URL.format(slug=slug)
        captured_url = None

        # Ağ trafiğini dinleyerek ercdn.net yönlendirmesini anında yakala
        def handle_response(response):
            nonlocal captured_url
            url = response.url
            if "ercdn.net" in url and "radyo" not in url.lower():
                captured_url = url

        page.on("response", handle_response)

        try:
            # Unaux adresine gidip yönlendirmenin tamamlanmasını bekle
            page.goto(target_url, timeout=20000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000) # Yönlendirmenin oturması için kısa bekleme
            
            # Eğer ağ dinleyicisi yakalayamadıysa son sayfa URL'sini kontrol et
            if not captured_url and "ercdn.net" in page.url and "radyo" not in page.url.lower():
                captured_url = page.url
                
        except Exception as e:
            print(f"[TARAYICI HATASI] {slug}: {e}")
        finally:
            browser.close()
            
        return captured_url

def build_playlist():
    playlist_lines = [
        "#EXTM3U",
        "#EXT-X-VERSION:3"
    ]

    print("Playwright Chrome motoru ile Unaux taranıyor...\n")
    success_count = 0

    for ch in CHANNELS:
        name = ch["name"]
        slug = ch["slug"]
        
        stream_url = capture_ercdn_with_browser(slug)
        
        if stream_url and "ercdn.net" in stream_url:
            playlist_lines.append(f'#EXTINF:-1 tvg-name="{name}" group-title="Turkuvaz",{name}')
            playlist_lines.append(stream_url)
            print(f"[BAŞARILI] {name} -> {stream_url}")
            success_count += 1
        else:
            print(f"[REDDEDİLDİ] {name} için kaynak alınamadı.")

    if success_count > 0:
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(playlist_lines) + "\n")
        print(f"\nplaylist.m3u başarıyla güncellendi ({success_count} kanal).")
    else:
        print("\n[UYARI] Hiçbir kanal bulunamadı, dosya değiştirilmedi.")

if __name__ == "__main__":
    build_playlist()
