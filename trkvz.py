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

def capture_ercdn_m3u8(slug, referer_url):
    # F12 Network mantığını taklit eden Session oluşturuyoruz
    session = requests.Session()
    
    # Tarayıcı başlıklarını (Headers) birebir tanımlıyoruz
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": referer_url,
        "Origin": referer_url.rstrip('/'),
        "Accept": "*/*"
    })

    # Unaux üzerindeki resolver adresine istek atıyoruz
    target_url = f"https://uzunmuhalefet.unaux.com/trkvz.php?kanal={slug}&.m3u8"

    try:
        # F12'deki tüm Redirect (302/301) ağ akışını takip eder
        response = session.get(target_url, allow_redirects=True, timeout=10)
        
        # 1. Yöntem: Doğrudan ulaşılan son URL (ERCdn içeriyorsa)
        if "ercdn.net" in response.url:
            return response.url

        # 2. Yöntem: Yönlendirme geçmişindeki (Redirect History) ERCdn linkini avlama
        for req in response.history:
            location = req.headers.get("Location", "")
            if "ercdn.net" in location:
                return location

        # ERCdn yakalanamadıysa son ulaşılan URL'yi döndürür
        return response.url

    except Exception as e:
        print(f"[AĞ HATASI] {slug}: {e}")
        return None

# Test
print(capture_ercdn_m3u8("atv", "https://www.atv.com.tr/"))
