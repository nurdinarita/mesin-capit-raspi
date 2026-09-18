const express = require("express");
const path = require("path");
const { Gpio } = require("onoff");

const app = express();
const PORT = 3000;

// Pemetaan tombol ke Pin GPIO (Gunakan nomor Pin BCM)
// Catatan: Jika dijalankan di PC/bukan Raspi, penyiapan Gpio akan error.
const gpioPins = {
  1: new Gpio(17, "out"), // Kotak 1 -> GPIO 17
  2: new Gpio(27, "out"), // Kotak 2 -> GPIO 27
  3: new Gpio(22, "out"), // Kotak 3 -> GPIO 22
  4: new Gpio(5, "out"), // Kotak 4 -> GPIO 5
  5: new Gpio(6, "out"), // Kotak 5 -> GPIO 6
};

// Serve static file (HTML/CSS) dari folder 'public'
app.use(express.static(path.join(__dirname, "public")));

// Endpoint API saat kotak diklik
app.post("/trigger/:id", (req, res) => {
  const boxId = req.params.id;
  const gpio = gpioPins[boxId];

  if (gpio) {
    // Baca status pin saat ini (0 = LOW, 1 = HIGH) lalu balikkan nilainya (toggle)
    const currentState = gpio.readSync();
    const newState = currentState === 0 ? 1 : 0;

    gpio.writeSync(newState);

    return res.json({
      status: "success",
      box: boxId,
      state: newState === 1 ? "HIGH" : "LOW",
    });
  }

  res.status(400).json({ status: "error", message: "Kotak tidak valid" });
});

// Bersihkan pin GPIO saat server dimatikan (Ctrl+C)
process.on("SIGINT", () => {
  Object.values(gpioPins).forEach((gpio) => gpio.unexport());
  process.exit();
});

app.listen(PORT, () => {
  console.log(`Server Node.js berjalan di http://localhost:${PORT}`);
});
