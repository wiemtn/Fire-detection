from ultralytics import YOLO
import cv2
import threading
import time
import requests
import pywhatkit as pwk
from datetime import datetime
from twilio.rest import Client
import os
import numpy as np
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

"""
Why Roboflow for Fire Detection?

1. Data Management & Preprocessing:
   - Roboflow provides powerful tools for dataset management
   - Automatic image preprocessing (resize, augmentation, normalization)
   - Supports multiple annotation formats
   - Version control for datasets

2. Model Training Benefits:
   - Easy export to multiple model formats (YOLO, TensorFlow, PyTorch)
   - Automated model training infrastructure
   - Built-in data augmentation techniques
   - Real-time model performance metrics

3. Deployment Advantages:
   - Simple export process for trained models
   - Multiple deployment options (edge devices, cloud, web)
   - API integration capabilities
   - Model monitoring and analytics

4. Quality Control:
   - Built-in dataset health checks
   - Annotation quality verification
   - Class balance analysis
   - Dataset statistics and visualization
"""

# === CONFIGURATION ===

# Email Configuration
EMAIL_SENDER = "zakraouiwiem@gmail.com"
EMAIL_PASSWORD = "kzzi jekt nymj rlhk"
EMAIL_RECEIVER = "zakraouiwiem@gmail.com"
EMAIL_SUBJECT = "🚨 Fire Detection Alert!"

# Video Recording Configuration
RECORD_DURATION = 10  # seconds to record after fire detection
VIDEO_OUTPUT_DIR = "fire_recordings"
if not os.path.exists(VIDEO_OUTPUT_DIR):
    os.makedirs(VIDEO_OUTPUT_DIR)

# Load your trained model
model = YOLO("best.pt")

# WhatsApp Configuration
WHATSAPP_NUMBER = "+21650852180"  

# Twilio Configuration (commented out until properly configured)
# TWILIO_ACCOUNT_SID = "ACbd337248e7718753c1a2a9b2b882db86"
# TWILIO_AUTH_TOKEN = "dd24f89038dac3f028c896e88a8aee3f"
# TWILIO_PHONE_NUMBER = "19183933506"

TELEGRAM_BOT_TOKEN = "7840954461:AAGI8i4X5MljPmTbuuIniApFcWD4fE05jZc"
TELEGRAM_CHAT_ID = "910266840"

# Alarm file path (must be a short .wav file)
ALARM_PATH = "alarm.wav"

# === FUNCTIONS ===

def evaluate_model_metrics():
    """
    Evaluate the model's performance metrics if data.yaml is available
    """
    try:
        if os.path.exists("data.yaml"):
            results = model.val(data="data.yaml", 
                              conf=0.6,
                              iou=0.5)
            
            metrics = {
                "mAP50": results.box.map50,
                "mAP50-95": results.box.map,
                "Precision": results.box.p,
                "Recall": results.box.r,
                "F1-Score": results.box.f1
            }
            
            print("\n=== Model Performance Metrics ===")
            for metric_name, value in metrics.items():
                print(f"{metric_name}: {value:.4f}")
                
            return metrics
        else:
            print("ℹ️ Skipping model evaluation - data.yaml not found")
            return None
            
    except Exception as e:
        print(f"ℹ️ Skipping model evaluation: {str(e)}")
        return None

def analyze_detection_speed():
    """
    Analyze the model's detection speed on the current hardware.
    """
    try:
        # Initialize timing list
        inference_times = []
        num_trials = 100
        
        # Create a dummy image for testing
        test_image = np.zeros((640, 640, 3), dtype=np.uint8)
        
        print("\n=== Speed Analysis ===")
        print(f"Running {num_trials} inference trials...")
        
        # Run multiple trials
        for _ in range(num_trials):
            start_time = time.time()
            model.predict(source=test_image, conf=0.6, verbose=False)
            inference_times.append(time.time() - start_time)
        
        # Calculate statistics
        avg_time = np.mean(inference_times)
        std_time = np.std(inference_times)
        fps = 1.0 / avg_time
        
        print(f"Average inference time: {avg_time*1000:.2f}ms (±{std_time*1000:.2f}ms)")
        print(f"Frames per second: {fps:.2f}")
        
        return {
            "avg_inference_time": avg_time,
            "std_inference_time": std_time,
            "fps": fps
        }
        
    except Exception as e:
        print(f"❌ Error during speed analysis: {str(e)}")
        return None

def make_voice_call():
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        call = client.calls.create(
            twiml='<Response><Say language="en">Emergency! Fire has been detected in your area. This is an automated alert. Please check immediately!</Say></Response>',
            to=WHATSAPP_NUMBER,
            from_=TWILIO_PHONE_NUMBER
        )
        print(f"✅ Emergency voice call initiated: {call.sid}")
    except Exception as e:
        print(f"❌ Failed to make voice call: {str(e)}")

def send_sms_alert():
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body="🚨 ALERT: Fire detected in your area! Please check immediately! 🔥",
            from_=TWILIO_PHONE_NUMBER,
            to=WHATSAPP_NUMBER
        )
        print(f"✅ Emergency SMS sent: {message.sid}")
    except Exception as e:
        print(f"❌ Failed to send SMS: {str(e)}")

def play_alarm():
    try:
        playsound(ALARM_PATH)
        print("✅ Alarm played successfully")
    except Exception as e:
        print("🔇 Alarm Error:", str(e))

def send_telegram_alert():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message = {"chat_id": TELEGRAM_CHAT_ID, "text": "🚨🔥 Fire detected! Immediate action required!"}
    try:
        response = requests.post(url, data=message)
        if response.status_code == 200:
            print("✅ Telegram alert sent.")
        else:
            print("❌ Telegram failed:", response.text)
    except Exception as e:
        print("❌ Telegram exception:", e)

def send_whatsapp_alert():
    try:
        # Get current time
        now = datetime.now()
        # Add 1 minute to current time to ensure message sends
        message_time_hour = now.hour
        message_time_min = now.minute + 1
        
        # Send WhatsApp message
        pwk.sendwhatmsg(WHATSAPP_NUMBER, 
                        "🚨🔥 Fire detected! Immediate action required!", 
                        message_time_hour, 
                        message_time_min,
                        wait_time=15,
                        tab_close=True)
        print("✅ WhatsApp alert scheduled.")
    except Exception as e:
        print("❌ WhatsApp alert error:", e)

def record_video(frame_queue, duration=RECORD_DURATION):
    """
    Record video from the frame queue for specified duration
    """
    try:
        if not frame_queue:
            print("❌ Error: Frame queue is empty")
            return None
            
        print(f"📹 Starting video recording... ({len(frame_queue)} frames in queue)")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(VIDEO_OUTPUT_DIR, f"fire_detection_{timestamp}.mp4")
        
        # Get the first frame to determine video properties
        first_frame = frame_queue[0]
        height, width = first_frame.shape[:2]
        print(f"🎥 Frame size: {width}x{height}")
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, 20.0, (width, height))
        
        if not out.isOpened():
            print("❌ Failed to create video writer")
            return None
            
        # Write frames from queue
        frames_written = 0
        for frame in frame_queue:
            if frame is None:
                print(f"⚠️ Skipping None frame at position {frames_written}")
                continue
            try:
                out.write(frame)
                frames_written += 1
            except Exception as e:
                print(f"❌ Error writing frame {frames_written}: {str(e)}")
                
        out.release()
        
        if frames_written == 0:
            print("❌ No frames were written to video")
            if os.path.exists(output_path):
                os.remove(output_path)
            return None
            
        if not os.path.exists(output_path):
            print("❌ Video file was not created")
            return None
            
        file_size = os.path.getsize(output_path)
        print(f"✅ Video saved: {output_path}")
        print(f"📊 Stats: {frames_written} frames written, file size: {file_size/1024:.1f}KB")
        return output_path
        
    except Exception as e:
        print(f"❌ Error in record_video: {str(e)}")
        return None

def send_email_alert(video_path):
    """
    Send email with video attachment
    """
    try:
        print(f"📧 Preparing to send email alert with video: {video_path}")
        
        # Verify video file exists
        if not os.path.exists(video_path):
            print(f"❌ Video file not found: {video_path}")
            return
            
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = EMAIL_SUBJECT
        
        # Add body
        body = """
        🚨 FIRE DETECTION ALERT! 🔥
        
        A fire has been detected by the monitoring system.
        Please check the attached video recording immediately.
        
        Time of detection: {}
        
        This is an automated message. Please take necessary action.
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        msg.attach(MIMEText(body, 'plain'))
        
        print("📎 Attaching video file...")
        # Attach video
        with open(video_path, 'rb') as f:
            video_attachment = MIMEApplication(f.read(), _subtype="mp4")
            video_attachment.add_header('Content-Disposition', 'attachment', 
                                     filename=os.path.basename(video_path))
            msg.attach(video_attachment)
        
        print("🔒 Connecting to Gmail SMTP server...")
        # Send email using Gmail's SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            print("🔐 Starting TLS connection...")
            server.starttls()
            print("🔑 Attempting login...")
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            print("📤 Sending email...")
            server.send_message(msg)
            
        print("✅ Email alert sent successfully")
        
    except smtplib.SMTPAuthenticationError as e:
        print("❌ Gmail authentication failed. Please check:")
        print("  1. Email address is correct")
        print("  2. App password is correct")
        print("  3. 2-Step verification is enabled in your Google Account")
        print(f"Error details: {str(e)}")
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error occurred: {str(e)}")
        print("Please check your internet connection and Gmail settings")
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        print("Stack trace:", e.__traceback__)

def test_email_functionality():
    """
    Test the email sending functionality with a sample video
    """
    print("\n=== Testing Email Functionality ===")
    
    # Create a test video
    print("📹 Creating test video...")
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(test_frame, "Test Video", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)
    
    test_frames = [test_frame.copy() for _ in range(20)]  # 20 frames of test video
    
    # Save test video
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_video_path = os.path.join(VIDEO_OUTPUT_DIR, f"test_video_{timestamp}.mp4")
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(test_video_path, fourcc, 20.0, (640, 480))
    
    for frame in test_frames:
        out.write(frame)
    out.release()
    
    print(f"✅ Test video created: {test_video_path}")
    
    # Test email sending
    print("\n📧 Testing email sending...")
    print(f"From: {EMAIL_SENDER}")
    print(f"To: {EMAIL_RECEIVER}")
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = "Test Email - Fire Detection System"
        
        body = """
        This is a test email from your Fire Detection System.
        If you receive this email and can view the attached video, the email functionality is working correctly.
        
        Time of test: {}
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach test video
        print("📎 Attaching test video...")
        with open(test_video_path, 'rb') as f:
            video_attachment = MIMEApplication(f.read(), _subtype="mp4")
            video_attachment.add_header('Content-Disposition', 'attachment', 
                                     filename=os.path.basename(test_video_path))
            msg.attach(video_attachment)
        
        # Send email
        print("🔒 Connecting to Gmail SMTP server...")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            print("🔐 Starting TLS connection...")
            server.starttls()
            print("🔑 Attempting login with provided credentials...")
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            print("📤 Sending test email...")
            server.send_message(msg)
            
        print("\n✅ Test email sent successfully!")
        print("Please check your inbox at:", EMAIL_RECEIVER)
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print("\n❌ Gmail authentication failed!")
        print("Please verify:")
        print("1. Your Gmail address is correct:", EMAIL_SENDER)
        print("2. Your App Password is correct (16 characters)")
        print("3. 2-Step Verification is enabled in your Google Account")
        print("\nError details:", str(e))
        return False
        
    except Exception as e:
        print("\n❌ Error sending test email:", str(e))
        return False

def verify_email_settings():
    """
    Verify email settings and connection
    """
    print("\n🔍 Verifying Email Settings...")
    
    # Check email format
    if not EMAIL_SENDER or '@' not in EMAIL_SENDER:
        print("❌ Invalid sender email address:", EMAIL_SENDER)
        return False
    if not EMAIL_RECEIVER or '@' not in EMAIL_RECEIVER:
        print("❌ Invalid receiver email address:", EMAIL_RECEIVER)
        return False
    
    # Check app password
    if not EMAIL_PASSWORD or len(EMAIL_PASSWORD) != 16:
        print("❌ Invalid app password length (should be 16 characters)")
        return False
    
    # Test SMTP connection
    try:
        print("🔒 Testing SMTP connection...")
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
            print("🔐 Starting TLS...")
            server.starttls()
            print("🔑 Testing login...")
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            print("✅ SMTP connection and login successful!")
            return True
    except smtplib.SMTPAuthenticationError as e:
        print("❌ Authentication failed!")
        print("Error:", str(e))
        print("\nPlease verify:")
        print("1. You have enabled 2-Step Verification in your Google Account")
        print("2. You are using an App Password (not your regular password)")
        print("3. The App Password is correctly copied (16 characters)")
        return False
    except Exception as e:
        print("❌ Connection failed!")
        print("Error:", str(e))
        return False

def send_test_email():
    """
    Send a simple test email without attachment
    """
    try:
        print("\n📧 Sending test email...")
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = "Test Email - Fire Detection System"
        
        body = "This is a test email from your Fire Detection System."
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
            
        print("✅ Test email sent successfully!")
        return True
    except Exception as e:
        print("❌ Failed to send test email!")
        print("Error:", str(e))
        return False

def show_ios_guide():
    """
    Display setup guide for iOS devices
    """
    print("\n📱 iOS Setup Guide for DroidCam:")
    print("\n1. Install DroidCam on your iPhone:")
    print("   - Open App Store")
    print("   - Search for 'DroidCam'")
    print("   - Install 'DroidCam Webcam & OBS Camera'")
    
    print("\n2. Connect your iPhone:")
    print("   - Open DroidCam on your iPhone")
    print("   - Make sure your iPhone is connected to the same WiFi as your computer")
    print("   - Look for 'WiFi IP' in the app (e.g., 192.168.1.21)")
    print("   - The port number is usually 4747")
    
    print("\n3. Important iOS Notes:")
    print("   - Keep the DroidCam app open and screen on")
    print("   - Allow camera permissions if prompted")
    print("   - If using iOS 14+, allow local network access")
    print("   - For better performance, use 'High Quality' mode in DroidCam settings")
    
    input("\nPress Enter when you're ready to connect...")

def connect_to_ip_camera():
    """
    Handle IP camera connection with retry mechanism and different app support
    """
    print("\n📱 IP Camera Connection Guide:")
    print("1. IP Webcam (Android)")
    print("2. DroidCam (iOS/Android)")
    print("3. Custom URL")
    
    app_choice = input("Choose your camera app (1-3): ")
    
    if app_choice == "1":
        # IP Webcam
        ip = input("Enter IP address (e.g., 192.168.1.21): ")
        port = input("Enter port (default 8080): ") or "8080"
        url = f"http://{ip}:{port}/video"
    elif app_choice == "2":
        # Show iOS guide if needed
        ios_choice = input("\nAre you using an iPhone? (y/n): ").lower()
        if ios_choice == 'y':
            show_ios_guide()
        
        # DroidCam
        ip = input("\nEnter IP address shown in DroidCam app: ")
        port = input("Enter port (default 4747): ") or "4747"
        print("\nDroidCam connection options:")
        print("1. Standard video feed (try this first)")
        print("2. MJPEG feed (better performance)")
        print("3. High quality feed")
        print("4. Low latency feed")
        droid_option = input("Choose connection type (1-4): ") or "1"
        
        if droid_option == "1":
            url = f"http://{ip}:{port}/video"
        elif droid_option == "2":
            url = f"http://{ip}:{port}/mjpegfeed"
        elif droid_option == "3":
            url = f"http://{ip}:{port}/videofeed?1280x720"
        else:
            url = f"http://{ip}:{port}/videofeed?640x480"
            
        print("\n💡 iOS Troubleshooting Tips:")
        print("- Make sure 'Local Network' access is allowed for DroidCam")
        print("- Try switching between WiFi and cellular data")
        print("- Check if your iPhone's personal hotspot is turned off")
        print("- Verify no VPN is active on either device")
    else:
        # Custom URL
        url = input("Enter complete camera URL: ")
    
    print(f"\n🎥 Attempting to connect to {url}...")
    
    # Try different connection methods for the selected URL
    methods = [
        (url, "Default URL"),
        (url.replace("video", "videofeed"), "Video feed URL"),
        (url.replace("video", "mjpegfeed"), "MJPEG feed URL"),
        (f"{url}?640x480", "640x480 resolution"),
        (f"{url}?1280x720", "720p resolution"),
        (f"http://{ip}:{port}/video", "Basic video URL"),
        (f"http://{ip}:{port}/videofeed", "Basic feed URL")
    ]
    
    for method_url, method_name in methods:
        print(f"\nTrying {method_name}...")
        try:
            cap = cv2.VideoCapture(method_url)
            
            # Test if connection is working
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    print(f"✅ Successfully connected using {method_name}")
                    print(f"📊 Frame size: {frame.shape[1]}x{frame.shape[0]}")
                    return cap, method_url
                else:
                    print("⚠️ Connection opened but no valid frame received")
            else:
                print("⚠️ Could not open connection")
            
            cap.release()
        except Exception as e:
            print(f"⚠️ Error: {str(e)}")
            continue
    
    print("\n❌ Failed to connect. Please verify:")
    print("1. DroidCam app is running and screen is on")
    print("2. Both PC and iPhone are on the same WiFi network")
    print("3. Windows Firewall is not blocking the connection")
    print("4. The IP address shown in DroidCam app matches what you entered")
    print("5. Local Network access is allowed for DroidCam (iOS Settings)")
    print("\n💡 iOS-specific troubleshooting:")
    print("- Go to iPhone Settings → Privacy → Local Network")
    print("- Make sure DroidCam is allowed")
    print("- Try restarting the DroidCam app")
    print("- Check if iOS camera permissions are granted")
    return None, None

if __name__ == "__main__":
    print("\n🚀 Fire Detection System")
    print("1. Start fire detection (Local Webcam)")
    print("2. Start fire detection (IP Camera)")
    print("3. Test email functionality")
    print("4. Verify email settings")
    print("5. Send test email (no attachment)")
    print("6. Test video recording")
    choice = input("Enter your choice (1-6): ")
    
    if choice == "2":
        cap, ip_address = connect_to_ip_camera()
        if not cap:
            print("Exiting...")
            exit()
    elif choice == "3":
        test_email_functionality()
        exit()
    elif choice == "4":
        verify_email_settings()
        exit()
    elif choice == "5":
        send_test_email()
        exit()
    elif choice == "6":
        # Test video recording with a simple pattern
        print("\n📹 Testing video recording...")
        test_frames = []
        for i in range(20):
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, f"Test Frame {i}", (50, 240), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            test_frames.append(frame)
        video_path = record_video(test_frames)
        if video_path:
            print("✅ Test recording successful!")
        else:
            print("❌ Test recording failed!")
        exit()
    else:
        print("\n📷 Using local webcam...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Failed to open local webcam.")
            exit()
        print("✅ Successfully connected to local webcam")

    # First verify email settings before starting
    if not verify_email_settings():
        print("\n⚠️ Email settings verification failed!")
        proceed = input("Do you want to proceed anyway? (y/n): ").lower()
        if proceed != 'y':
            print("Exiting...")
            exit()
    
    print("\n🚀 Starting Fire Detection System...")
    
    # Optional model evaluation
    metrics = evaluate_model_metrics()
    speed_metrics = analyze_detection_speed()
    
    fire_detected = False
    frame_queue = []
    recording = False
    last_email_time = 0
    EMAIL_COOLDOWN = 60
    recording_start_time = None

    print("Press 'q' to quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to grab frame. Retrying...")
            # For IP camera, try to reconnect
            if choice == "2":
                time.sleep(1)  # Wait before retrying
                cap, ip_address = connect_to_ip_camera()
                continue
            else:
                break

        try:
            results = model.predict(source=frame, conf=0.6, verbose=False)
            fire_found = False

            for result in results:
                if result.boxes is not None and result.boxes.cls.numel() > 0:
                    classes = result.boxes.cls.cpu().numpy().astype(int)
                    if 0 in classes:
                        fire_found = True
                        break

            current_time = time.time()
            
            # Always keep recent frames in queue for potential recording
            frame_queue.append(frame.copy())
            if len(frame_queue) > 20:
                frame_queue.pop(0)

            if fire_found:
                if not fire_detected:
                    print("🔥 Fire detected! Starting video recording and preparing alerts...")
                    fire_detected = True
                    recording = True
                    recording_start_time = current_time
                    
                    # Start immediate alerts
                    threading.Thread(target=play_alarm).start()
                    threading.Thread(target=send_telegram_alert).start()
                
                # Check if we should stop recording
                if recording and recording_start_time and (current_time - recording_start_time) >= RECORD_DURATION:
                    print(f"📹 Recording complete after {RECORD_DURATION} seconds...")
                    recording = False
                    
                if current_time - last_email_time >= EMAIL_COOLDOWN:
                    print(f"💾 Saving video from {len(frame_queue)} frames...")
                    video_path = record_video(frame_queue)
                    if video_path:
                        print("📧 Sending email with video...")
                        try:
                            msg = MIMEMultipart()
                            msg['From'] = EMAIL_SENDER
                            msg['To'] = EMAIL_RECEIVER
                            msg['Subject'] = EMAIL_SUBJECT
                            
                            camera_type = "IP Camera" if choice == "2" else "Local Webcam"
                            body = f"""
                            🚨 FIRE DETECTION ALERT! 🔥
                            
                            A fire has been detected by the monitoring system.
                            Camera: {camera_type}
                            Please check the attached video recording immediately.
                            
                            Time of detection: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                            """
                            
                            msg.attach(MIMEText(body, 'plain'))
                            
                            with open(video_path, 'rb') as f:
                                video_attachment = MIMEApplication(f.read(), _subtype="mp4")
                                video_attachment.add_header('Content-Disposition', 'attachment', 
                                                         filename=os.path.basename(video_path))
                                msg.attach(video_attachment)
                            
                            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                                server.starttls()
                                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                                server.send_message(msg)
                            
                            print("✅ Email alert sent successfully")
                            last_email_time = current_time
                        except Exception as e:
                            print(f"❌ Error sending email: {str(e)}")
                    else:
                        print("❌ Failed to save video, email not sent")
                else:
                    print("⏳ Email cooldown active, skipping email alert")
                
                frame_queue = []  # Clear the queue after sending
                
            elif not fire_found and fire_detected:
                print("✅ Fire no longer detected")
                fire_detected = False
                recording = False
                recording_start_time = None

            # Show webcam feed
            annotated_frame = results[0].plot()
            cv2.imshow("Live Fire Detection", annotated_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        except Exception as e:
            print(f"❌ Error processing frame: {str(e)}")
            continue

    cap.release()
    cv2.destroyAllWindows()
