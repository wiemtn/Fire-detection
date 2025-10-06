# 🔥 FireFarmWise – Smart Fire Detection & Alerting System

FireFarmWise is an intelligent fire detection and alerting system that uses YOLOv8 for real-time fire detection. It supports multiple alert channels including WhatsApp, Telegram, Twilio voice/SMS, and push notifications. It also supports camera input from both local webcams and mobile phones acting as IP cameras.

---

## 🚀 Features

- 🔍 Real-time fire detection using YOLOv8.
- 📞 Voice call & SMS alerts via Twilio.
- 💬 Instant messaging via WhatsApp and Telegram.
- 🔔 Free push notifications via OneSignal or Firebase Cloud Messaging.
- 📱 Stream video from your mobile phone’s camera using IP Webcam or similar apps.

---

## 🛠️ Tech Stack

- **YOLOv8** – Ultralytics model for fire detection.
- **OpenCV** – Real-time image and video capture.
- **Twilio API** – For voice call and SMS alerts.
- **WhatsApp & Telegram Bots** – For chat alerts.
- **Firebase / OneSignal** – For push notifications.
- **Python** – Main application language.

---

## 📱 Using Your Phone as an IP Camera

You can stream video from your phone and use it as the camera input:

1. Install an IP camera app:
   - **Android**: IP Webcam, DroidCam
   - **iOS**: EpocCam, iVCam

2. Connect your phone and computer to the **same Wi-Fi**.

3. Open the app and copy the video stream URL, e.g.:
