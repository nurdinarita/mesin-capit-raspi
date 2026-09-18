import time
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Mapping Aksi ke Nomor Pin BCM GPIO
GPIO_MAP = {
    'UP': 17,    
    'DOWN': 27,  
    'LEFT': 22,  
    'RIGHT': 5,  
    'GRAB': 6    
}

# Inisialisasi GPIO (Safety check untuk PC Windows / Raspberry Pi)
is_raspberry = False
try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    for pin in GPIO_MAP.values():
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)
    is_raspberry = True
    print("RPi.GPIO Berhasil Diinisialisasi.")
except ImportError:
    print("[PC Simulation Mode] Modul RPi.GPIO tidak ditemukan. Menjalankan mode simulasi.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/control', methods=['POST'])
def control():
    data = request.get_json()
    action = data.get('action')
    print(f"[Aksi Diterima]: {action}")

    if action in GPIO_MAP:
        pin = GPIO_MAP[action]
        
        if is_raspberry:
            # Beri pulsa ke GPIO selama 0.3 detik
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(0.3)
            GPIO.output(pin, GPIO.LOW)

        return jsonify({"status": "success", "action": action, "pin": pin})

    return jsonify({"status": "error", "message": "Aksi tidak valid"}), 400

if __name__ == '__main__':
    try:
        # Jalankan server Flask pada port 5000
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        if is_raspberry:
            GPIO.cleanup()