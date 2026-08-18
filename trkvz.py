import requests

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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.atv.com.tr/"
}

# TCP bağlantılarını açık tutarak hızı artırır (Session kullanımı)
session = requests.Session()
session.headers.update(HEADERS)

def run():
    for name, url in CHANNELS.items():
        try:
            # Doğrudan TR VPS IP'si ile istek - proxy arama derdi yok
            res = session.get(url, timeout=5)
            if res.status_code == 200:
                print(f"[BAŞARILI] {name} - Status: 200")
                # Buraya M3U8/Token ayrıştırma mantığınızı ekleyin
            else:
                print(f"[HATA] {name} - Status: {res.status_code}")
        except Exception as e:
            print(f"[BAĞLANTI HATASI] {name}: {e}")

if __name__ == "__main__":
    run()
