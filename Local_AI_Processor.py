import serial
import speech_recognition as sr
import time
import wave
import os
from datetime import datetime

COM_PORT = 'COM4'
BAUD_RATE = 921600 

def get_time():
    return datetime.now().strftime("%H:%M:%S")

def print_log(status, message, color="\033[0m"):
    print(f"[{get_time()}] {color}{status:<12}\033[0m | {message}")

try:
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    ser.reset_input_buffer()
    print_log("SYSTEM", f"Connected to ESP32 on {COM_PORT}", "\033[92m")
except Exception as e:
    print_log("ERROR", f"Failed to connect: {e}", "\033[91m")
    exit()

r = sr.Recognizer()
led_synonyms = ["led", "set", "let", "light", "lit", "lid", "red", "length", "land"]
off_commands = ["off", "of", "close", "shut", "stop"]
on_commands = ["on", "open", "turn", "start"]

current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "last_record.wav")

print("-" * 60)
print_log("STATUS", "Waiting for Trigger (Voice)...", "\033[94m")

while True:
    try:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            
            if "[RECORDING]" in line:
                print_log("MICROPHONE", "Trigger detected! Recording 2s...", "\033[93m")
                ser.reset_input_buffer() 
                
                raw_audio = b""
                expected_size = 64000 
                start_grab = time.time()
                
                while len(raw_audio) < expected_size:
                    if ser.in_waiting > 0:
                        raw_audio += ser.read(min(ser.in_waiting, expected_size - len(raw_audio)))
                    if time.time() - start_grab > 2.8: break

                print_log("BUFFER", f"Captured {len(raw_audio)} bytes", "\033[92m")
                
                with wave.open(file_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(raw_audio)
                
                print_log("AI_ENGINE", "Analyzing speech via Google...")
                audio_data = sr.AudioData(raw_audio, 16000, 2)
                
                try:
                    text = r.recognize_google(audio_data, language="en-US").lower()
                    print_log("RESULT", f"Text Recognized: '{text}'", "\033[96m")
                    
                    words = text.split()
                    
                    if any(syn in words for syn in led_synonyms):
                        
                        if any(cmd in words for cmd in off_commands):
                            ser.write(b'0')
                            print_log("ACTION", "Command Sent: [LED OFF]", "\033[91m")
                        
                        elif any(cmd in words for cmd in on_commands):
                            ser.write(b'1')
                            print_log("ACTION", "Command Sent: [LED ON]", "\033[92m")
                            
                    else:
                        print_log("REJECTED", "Keyword not detected.", "\033[93m")
                
                except sr.UnknownValueError:
                    print_log("AI_ERROR", "Speech not clear.", "\033[91m")
                except sr.RequestError:
                    print_log("NETWORK", "Connection error.", "\033[91m")
                
                print("-" * 60)
                print_log("STATUS", "Waiting for Voice...", "\033[94m")
                ser.reset_input_buffer()

        time.sleep(0.01)
    except KeyboardInterrupt:
        ser.close()
        break
