import time
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Mapping Aksi Navigasi ke Pin GPIO BCM
GPIO_MAP = {
    'UP': 17,    
    'DOWN': 27,  
    'LEFT': 22,  
    'RIGHT': 5,  
    'GRAB': 6    
}

# Pin Khusus untuk Indikator Koin/Kredit (Ganti nomor BCM sesuai kebutuhan)
COIN_PIN = 26 

is_raspberry = False
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Setup Pin Navigasi
    for pin in GPIO_MAP.values():
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)
        
    # Setup Pin Koin/Kredit
    GPIO.setup(COIN_PIN, GPIO.OUT)
    GPIO.output(COIN_PIN, GPIO.HIGH)
    
    is_raspberry = True
    print("RPi.GPIO Berhasil Diinisialisasi.")
except ImportError:
    print("[PC Simulation Mode] Modul RPi.GPIO tidak ditemukan.")

@app.route('/')
def index():
    return render_template('index.html')

# Endpoint untuk Kontrol Tahan/Lepas (Hold/Release Navigasi)
@app.route('/control', methods=['POST'])
def control():
    data = request.get_json()
    action = data.get('action')
    state = data.get('state')  # 'ON' atau 'OFF'
    
    if action in GPIO_MAP:
        pin = GPIO_MAP[action]
        if is_raspberry:
            if state == 'ON':
                GPIO.output(pin, GPIO.LOW)
            else:
                GPIO.output(pin, GPIO.HIGH)
        
        print(f"[NAVIGASI] {action} -> {state} (Pin {pin})")
        return jsonify({"status": "success", "action": action, "state": state})

    return jsonify({"status": "error", "message": "Aksi tidak valid"}), 400

# Endpoint untuk Trigger Angka Koin (HIGH-LOW Jeda 1 Detik Berulang)
@app.route('/trigger-coin', methods=['POST'])
def trigger_coin():
    data = request.get_json()
    count = int(data.get('count', 1))
    
    print(f"[KOIN] Menerima {count}x pulsa koin...")
    
    if is_raspberry:
        for i in range(count):
            GPIO.output(COIN_PIN, GPIO.LOW)
            time.sleep(1)
            GPIO.output(COIN_PIN, GPIO.HIGH)
            time.sleep(1)
            
    return jsonify({"status": "success", "pulses": count})

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        if is_raspberry:
            GPIO.cleanup()