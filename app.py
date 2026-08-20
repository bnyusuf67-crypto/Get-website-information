import os
import re
import json
import subprocess
import threading
import time
import requests
import urllib3
from urllib.parse import urljoin
from flask import Flask, send_from_directory, jsonify, request  # hls.js preflight kontrolü için 'request' eklendi

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HLS_DIR = "hls_stream"
os.makedirs(HLS_DIR, exist_ok=True)

app = Flask(__name__)

# Global Durum Değişkenleri ve Kilit (Lock)
ffmpeg_process = None
ffmpeg_lock = threading.Lock()
stream_start_time = 0
TOKEN_REFRESH_INTERVAL = 6800  # Token ve CDN link süresi dolmadan önleyici yenileme (Saniye)

# ==========================================
# 1. CNN TÜRK DİNAMİK URL VE TRACK AYRIŞTIRMA
# ==========================================
def get_cnnturk_master_url():
    """CNN Türk API'sinden güncel M3U8 ana yayın linkini çeker."""
    api_url = "https://www.cnnturk.com/api/cnnvideo/media?id=62d6814670380e2cdc7c124c&isMobile=true"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Forwarded-For': '185.93.88.1'
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        data = response.json()

        service_url = data["Media"]["Link"]["ServiceUrl"]
        secure_path = data["Media"]["Link"]["SecurePath"]

        # Unicode escape çözümlemesi (\u0026 -> & vb.)
        secure_path = secure_path.encode('utf-8').decode('unicode_escape')

        final_m3u8_link = f"{service_url}{secure_path}"
        return final_m3u8_link
    except Exception as e:
        print(f"[HATA] CNN Türk Master URL çekilemedi: {e}")
        return None

def get_cnnturk_track_urls():
    """
    Master M3U8 dosyasını okur ve 5 kalite seviyesini ayrıştırır:
    track_0_192, track_1_320, track_2_550, track_3_750, track_4_1000
    """
    master_url = get_cnnturk_master_url()
    if not master_url:
        return [None] * 5

    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        res = requests.get(master_url, headers=headers, verify=False, timeout=10)
        if res.status_code == 200:
            lines = [line.strip() for line in res.text.splitlines() if line.strip() and not line.startswith("#")]
            full_urls = [urljoin(master_url, line) for line in lines]
            
            if len(full_urls) >= 5:
                return full_urls[:5]
            elif len(full_urls) > 0:
                return (full_urls + [full_urls[-1]] * 5)[:5]
    except Exception as e:
        print(f"[HATA] CNN Türk Track URL ayrıştırma başarısız: {e}")

    return [master_url] * 5

# ==========================================
# 2. MANİFEST VE FFMPEG AKIŞ YÖNETİMİ
# ==========================================
def create_master_manifest():
    """İstemcilerin en yüksek kaliteden başlaması için kaliteler tersten (yüksek -> düşük) sıralandı."""
    master_content = """#EXTM3U
#EXT-X-VERSION:2
#EXT-X-STREAM-INF:BANDWIDTH=1301120,FRAME-RATE=25.00,CODECS="avc1.4d001f,mp4a.40.2"
track_4_1000.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1013575,FRAME-RATE=25.00,CODECS="avc1.42001f,mp4a.40.2"
track_3_750.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=775503,FRAME-RATE=25.00,CODECS="avc1.42001e,mp4a.40.2"
track_2_550.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=492891,FRAME-RATE=25.00,CODECS="avc1.42001e,mp4a.40.2"
track_1_320.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=331520,FRAME-RATE=25.00,CODECS="avc1.42001e,mp4a.40.2"
track_0_192.m3u8"""

    with open(os.path.join(HLS_DIR, "master.m3u8"), "w", encoding="utf-8") as f:
        f.write(master_content)

def start_ffmpeg_process():
    """5 farklı kalite için FFmpeg sürecini yöneten thread-safe fonksiyon."""
    global ffmpeg_process, stream_start_time

    with ffmpeg_lock:
        track_urls = get_cnnturk_track_urls()
        if not track_urls[0]:
            print("[HATA] Akış URL'leri alınamadı, FFmpeg başlatılamıyor.")
            return False

        create_master_manifest()

        # Var olan eski FFmpeg sürecini sonlandır
        if ffmpeg_process and ffmpeg_process.poll() is None:
            print("[BİLGİ] Eski FFmpeg süreci kapatılıyor...")
            ffmpeg_process.kill()
            ffmpeg_process.wait()

        ffmpeg_cmd = ["ffmpeg", "-y", "-loglevel", "error"]
        
        # Giriş bağlantılarını ekle
        for url in track_urls:
            ffmpeg_cmd.extend([
                "-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "-reconnect", "1", "-reconnect_at_eof", "1", 
                "-reconnect_streamed", "1", "-reconnect_delay_max", "5",
                "-i", url
            ])

        # Çıktı M3U8 haritalamaları
        track_names = ["track_0_192.m3u8", "track_1_320.m3u8", "track_2_550.m3u8", "track_3_750.m3u8", "track_4_1000.m3u8"]
        for idx, track_name in enumerate(track_names):
            ffmpeg_cmd.extend([
                "-map", f"{idx}:v?", "-map", f"{idx}:a?", "-c", "copy",
                "-f", "hls", "-hls_time", "4", "-hls_list_size", "10",
                "-hls_flags", "delete_segments+append_list",
                os.path.join(HLS_DIR, track_name)
            ])

        ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        stream_start_time = time.time()
        print("[BİLGİ] CNN Türk FFmpeg süreci (Ters Kalite Sıralı) başarıyla başlatıldı.")
        return True

# ==========================================
# 3. WATCHDOG (OTOMATİK İZLEYİCİ VE YENİLEYİCİ)
# ==========================================
def stream_watchdog():
    """Çökmeleri ve periyodik token/URL yenilenmesini takip eder."""
    global ffmpeg_process, stream_start_time
    
    while True:
        time.sleep(8)
        now = time.time()
        
        if ffmpeg_process is not None and ffmpeg_process.poll() is not None:
            print("[UYARI] FFmpeg beklenmedik şekilde durdu! Yeniden başlatılıyor...")
            start_ffmpeg_process()
            
        elif ffmpeg_process is not None and (now - stream_start_time) >= TOKEN_REFRESH_INTERVAL:
            print("[BİLGİ] Yayın süresi doldu. CNN Türk URL/Token güncellemesi yapılıyor...")
            start_ffmpeg_process()

threading.Thread(target=stream_watchdog, daemon=True).start()

# ==========================================
# 4. FLASK ENDPOINT'LERİ
# ==========================================
@app.route("/")
def index():
    return """
    <h1>CNN Türk HLS Streamer (Full hls.js & CORS Support)</h1>
    <ul>
        <li><a href='/hls_stream/master.m3u8'>Master Playlist</a></li>
        <li><a href='/hls_stream/track_4_1000.m3u8'>Track 4 (1000k - En Yüksek)</a></li>
        <li><a href='/hls_stream/track_3_750.m3u8'>Track 3 (750k)</a></li>
        <li><a href='/hls_stream/track_2_550.m3u8'>Track 2 (550k)</a></li>
        <li><a href='/hls_stream/track_1_320.m3u8'>Track 1 (320k)</a></li>
        <li><a href='/hls_stream/track_0_192.m3u8'>Track 0 (192k - En Düşük)</a></li>
        <li><a href='/start'>Yeniden Başlatma Tuşu</a></li>
        <li><a href='/health'>Health Status</a></li>
    </ul>
    """

@app.route("/hls_stream/<path:filename>", methods=["GET", "OPTIONS"])
def serve_hls(filename):
    global ffmpeg_process
    
    # 1. Tarayıcının OPTIONS (Preflight) isteğine onay ver
    if request.method == "OPTIONS":
        response = app.make_default_options_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Range"
        return response

    # 2. LAZY LOAD: İlk izleyici isteğinde yayın başlatılır
    if ffmpeg_process is None or ffmpeg_process.poll() is not None:
        print("[LAZY LOAD] İlk izleyici isteği geldi. CNN Türk yayını başlatılıyor...")
        start_ffmpeg_process()
        
    response = send_from_directory(HLS_DIR, filename)
    
    # 3. hls.js Uyumlu Tam CORS Başlıkları
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Range"
    response.headers["Access-Control-Expose-Headers"] = "Content-Length, Content-Range"
    
    return response

@app.route("/health")
def health_check():
    is_alive = ffmpeg_process is not None and ffmpeg_process.poll() is None
    next_refresh = max(0, int(TOKEN_REFRESH_INTERVAL - (time.time() - stream_start_time))) if is_alive else 0
    
    return jsonify({
        "status": "healthy" if is_alive else "restarting",
        "ffmpeg_active": is_alive,
        "watchdog_active": True,
        "next_token_refresh_in_seconds": next_refresh
    }), 200

@app.route("/restart")
def manual_restart():
    success = start_ffmpeg_process()
    if success:
        return "CNN Türk yayını başarıyla yeniden başlatıldı."
    return "Yayın başlatılamadı!", 500

if __name__ == "__main__":
    start_ffmpeg_process()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
