# 🔐 Smart Door Lock System  
### Multi-Authentication Door Lock using OTP, Bluetooth Listener & Arduino Servo Motor

This project implements a **Smart Door Lock System** that can be unlocked using:

✔ **Dynamic 15-second OTP**  
✔ **Web Application (mobile-friendly)**  
✔ **Bluetooth / Media Key**  
✔ **Arduino Uno + Servo Motor**

The system integrates **Flask backend**, **JavaScript frontend**, **background Python listeners**, and **Arduino hardware**, offering a complete IoT-style smart security solution.

---

## 🚀 Features

### 🔢 OTP Unlock  
- Generates a new 4-digit OTP every **15 seconds**  
- Secure HMAC-SHA256 based algorithm  
- OTP verification supports ±3 time windows  
- Clean and responsive OTP UI  

### 📱 Web-Based Unlock  
- Unlock with a single button  
- Real-time door status  
- Bluetooth toggle control  

### 🎧 Bluetooth / Media Key Unlock  
- Press the **Play/Pause** media key on any keyboard or Bluetooth device  
- Background listener triggers unlock automatically  
- Works even when browser is closed  

### 🛠️ Hardware Unlock (Arduino)  
- Arduino Uno controls a Servo Motor  
- Python-to-Serial communication  
- Servo rotates to unlock and resets automatically  
- Complete real-world implementation (not simulation)

---

## 📂 Project Structure

```
smart-door-lock/
│
├── app.py
├── controller.py
├── listener.py
├── arduino_bridge.py
│
├── static/
│   ├── main.js
│   └── styles.css
│
├── templates/
│   ├── base.html
│   ├── index.html
│   └── enter_otp.html
│
└── arduino/
    └── servo_unlock.ino
```

---

## 🧰 Technologies Used

### **Software**
- Python (Flask)  
- JavaScript (Fetch API)  
- HTML5 + CSS3  
- pynput  
- pyserial  
- requests  
- Arduino IDE  

### **Hardware**
- Arduino Uno  
- Servo Motor (SG90 or similar)  
- USB Cable  
- Bluetooth keyboard/headset (optional)

---

## ⚙️ Architecture / Workflow

### **1️⃣ OTP Generation**
- Generated using:
  ```
  HMAC_SHA256(secret XOR timestamp)
  ```
- Regenerates every 15 seconds  
- Exposed at `/get_otp`

### **2️⃣ OTP Verification**
- User enters OTP on `/enter-otp`  
- JS sends → `POST /verify_otp { otp: "1234" }`  
- Valid OTP unlocks door + starts auto relock timer

### **3️⃣ Web Unlock**
One-click browser unlock →  
`POST /unlock_bt`

### **4️⃣ Bluetooth Unlock**
Media key listener detects Play/Pause →  
`POST /media_unlock`

### **5️⃣ Arduino Bridge**
Polls Flask `/status` → sends `'a'` to Arduino when door becomes unlocked.

### **6️⃣ Arduino Servo Action**
- Servo rotates to unlock  
- Waits 5 seconds  
- Auto resets to 0° (locked)

---

## 🛠️ Installation

### **1. Install Dependencies**
```bash
pip install flask pynput pyserial requests
```

### **2. Upload Arduino Code**
```cpp
#include <Servo.h>

Servo myservo;

void setup() {
  myservo.attach(3);
  Serial.begin(9600);
  myservo.write(0);
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'a') {
      myservo.write(85);
      delay(5000);
      myservo.write(0);
    }
  }
}
```

### **3. Start the System**
```bash
python controller.py
```

---

## 🔧 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| SMARTLOCK_SHARED_SECRET | OTP Secret | your_secret_here |
| RELOCK_SECONDS | Auto-lock timer | 5 |
| ARDUINO_PORT | Serial port | COM5 |
| ARDUINO_UNLOCK_BYTE | Unlock byte | a |
| FLASK_STATUS_URL | Flask status endpoint | http://127.0.0.1:5000/status |

---

## 🔮 Future Enhancements
- Fingerprint unlock module  
- Mobile application  
- Cloud-based remote unlocking  
- Intrusion alert system  
- Real-time logging & monitoring dashboard

---

## 🤝 Contributing
Pull requests are welcome! Improvements to UI, hardware, or security are appreciated.

---

## 📜 License
MIT License

---

## 👤 Author
**Aakash Thakur**  
Smart Door Lock Project – 2025  
Sharda University  
