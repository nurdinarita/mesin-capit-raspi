import time
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Status Sesi Mesin Capit (Global Lock)
is_busy = False
active_session_id = None

# Mapping Aksi Navigasi ke Pin GPIO BCM
GPIO_MAP = {
    'UP': 17,    
    'DOWN': 27,  
    'LEFT': 22,  
    'RIGHT': 5,  
    'GRAB': 6    
}

# Pin Khusus untuk Indikator Koin/Kredit
COIN_PIN = 26 

is_raspberry = False
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Setup Pin Navigasi (Default IDLE = HIGH / Active LOW)
    for pin in GPIO_MAP.values():
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)
        
    # Setup Pin Koin/Kredit (Default IDLE = HIGH / Active LOW)
    GPIO.setup(COIN_PIN, GPIO.OUT)
    GPIO.output(COIN_PIN, GPIO.HIGH)
    
    is_raspberry = True
    print("RPi.GPIO Berhasil Diinisialisasi (Active LOW Mode).")
except ImportError:
    print("[PC Simulation Mode] Modul RPi.GPIO tidak ditemukan. Menjalankan mode simulasi.")

@app.route('/')
def index():
    return render_template('index.html')

# Endpoint pengecekan status mesin
@app.route('/check-status', methods=['GET'])
def check_status():
    global is_busy
    return jsonify({"is_busy": is_busy})

# Endpoint untuk Mulai Main (Kunci Mesin & Kirim Sinyal Koin Active LOW)
@app.route('/trigger-coin', methods=['POST'])
def trigger_coin():
    global is_busy, active_session_id
    
    data = request.get_json()
    session_id = data.get('session_id')
    count = int(data.get('count', 1))
    
    if is_busy and active_session_id != session_id:
        return jsonify({"status": "error", "message": "Mesin sedang digunakan oleh pemain lain!"}), 403
    
    is_busy = True
    active_session_id = session_id
    
    print(f"[KOIN] Menerima {count}x pulsa koin dari Session: {session_id}")
    
    if is_raspberry:
        for i in range(count):
            GPIO.output(COIN_PIN, GPIO.LOW)   # Aktif (LOW)
            time.sleep(1)
            GPIO.output(COIN_PIN, GPIO.HIGH)  # Idle (HIGH)
            time.sleep(1)
            
    return jsonify({"status": "success", "pulses": count})

# Endpoint Navigasi (Mendukung Multi-Direction / Diagonal - Active LOW)
@app.route('/control', methods=['POST'])
def control():
    global is_busy, active_session_id
    
    data = request.get_json()
    actions = data.get('actions', [])  # Menerima list aksi, misal: ['UP', 'RIGHT']
    state = data.get('state')          # 'ON' atau 'OFF'
    session_id = data.get('session_id')
    
    if active_session_id != session_id:
        return jsonify({"status": "error", "message": "Akses ditolak. Mesin sedang digunakan pemain lain!"}), 403

    if is_raspberry:
        if state == 'OFF' or not actions:
            # Mati semua -> Set ke HIGH (Idle)
            for pin in GPIO_MAP.values():
                GPIO.output(pin, GPIO.HIGH)
        else:
            # Set pin yang ada di list 'actions' jadi LOW (Aktif), sisanya HIGH (Idle)
            for act, pin in GPIO_MAP.items():
                if act in actions:
                    GPIO.output(pin, GPIO.LOW)   # Aktif
                else:
                    GPIO.output(pin, GPIO.HIGH)  # Idle
    
    print(f"[NAVIGASI DIAGONAL] Aksi Terdeteksi: {actions} -> State: {state}")
    return jsonify({"status": "success", "actions": actions, "state": state})

# Endpoint untuk Melepas Kunci Sesi
@app.route('/release-session', methods=['POST'])
def release_session():
    global is_busy, active_session_id
    
    data = request.get_json()
    session_id = data.get('session_id')
    
    if active_session_id == session_id or active_session_id is None:
        is_busy = False
        active_session_id = None
        print(f"[SESSION] Sesi dilepas. Mesin siap digunakan kembali.")
        return jsonify({"status": "success"})
        
    return jsonify({"status": "error", "message": "Gagal melepas sesi"}), 400

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        if is_raspberry:
            GPIO.cleanup()