const express = require("express");
const path = require("path");
const app = express();
const PORT = 3000;

// Menangani parser body JSON
app.use(express.json());

// Melayani file statis dari folder public (HTML, CSS, JS)
app.use(express.static(path.join(__dirname, "public")));

// Konfigurasi Peta Pin GPIO Raspberry Pi
// Ubah nomor Pin BCM sesuai konfigurasi driver motor / relay Anda
const GPIO_MAP = {
  UP: 17,
  DOWN: 27,
  LEFT: 22,
  RIGHT: 5,
  GRAB: 6,
};

// Mode Penanganan GPIO (Diperiksa apakah berjalan di PC atau di Raspberry Pi)
let gpios = {};
let isRaspberry = false;

try {
  const { Gpio } = require("onoff");
  for (const key in GPIO_MAP) {
    gpios[key] = new Gpio(GPIO_MAP[key], "out");
  }
  isRaspberry = true;
  console.log("Hardware Raspberry Pi GPIO Berhasil Diinisialisasi.");
} catch (e) {
  console.log(
    "[PC Simulation Mode] Pustaka 'onoff' tidak dimuat. Menjalankan mode simulasi.",
  );
}

// Endpoint untuk menerima perintah navigasi dan pencapitan
app.post("/control", (req, res) => {
  const { action } = req.body;
  console.log(`[Aksi Diterima]: ${action}`);

  if (GPIO_MAP[action] !== undefined) {
    if (isRaspberry && gpios[action]) {
      // Pulsa singkat / Aktifkan Pin GPIO selama 300ms
      gpios[action].writeSync(1);
      setTimeout(() => {
        gpios[action].writeSync(0);
      }, 300);
    }

    return res.json({
      status: "success",
      action: action,
      pin: GPIO_MAP[action],
    });
  }

  res.status(400).json({ status: "error", message: "Aksi tidak valid" });
});

// Pembersihan Pin saat Server dihentikan
process.on("SIGINT", () => {
  if (isRaspberry) {
    Object.values(gpios).forEach((gpio) => gpio.unexport());
  }
  process.exit();
});

app.listen(PORT, () => {
  console.log(`Server Mesin Capit berjalan di http://localhost:${PORT}`);
});
