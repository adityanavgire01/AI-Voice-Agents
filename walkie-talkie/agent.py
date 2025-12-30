import os
import time
import sounddevice as sd
import soundfile as sf
from openai import OpenAI
from deepgram import DeepgramClient
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

if not OPENAI_API_KEY or not DEEPGRAM_API_KEY:
    raise ValueError("❌ Missing API Keys. Please check your .env file.")

# Initialize Clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)
deepgram = DeepgramClient(api_key=DEEPGRAM_API_KEY)

# Audio Settings
FILENAME = "input.wav"
OUTPUT_FILENAME = "response.mp3"
SAMPLE_RATE = 16000
DURATION = 10  # Duration of recording in seconds

def record_audio():
    print(f"\n🔴 Recording for {DURATION} seconds... Speak now!")
    # NOTE: If your mic doesn't work, try adding device=1 or device=2 here
    audio_data = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1)
    sd.wait()
    sf.write(FILENAME, audio_data, SAMPLE_RATE)
    print("✅ Recording saved.")

def transcribe_audio():
    print("👂 Transcribing...")
    with open(FILENAME, "rb") as audio_file:
        audio_data = audio_file.read()
    
    response = deepgram.listen.v1.media.transcribe_file(
        request=audio_data,
        model="nova-2",
        smart_format=True
    )
    
    transcript = response.results.channels[0].alternatives[0].transcript
    print(f"You said: '{transcript}'")
    return transcript

def get_ai_response(text):
    print("🧠 Thinking...")
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful, concise voice assistant. Keep answers short (under 2 sentences) for spoken audio."},
            {"role": "user", "content": text}
        ]
    )
    reply = response.choices[0].message.content
    print(f"AI says: '{reply}'")
    return reply

def text_to_speech(text):
    print("🗣️ Generating Voice...")
    
    response = deepgram.speak.v1.audio.generate(
        text=text,
        model="aura-asteria-en"
    )
    
    # Collect audio bytes from the generator
    audio_bytes = b"".join(chunk for chunk in response)
    
    # Save the audio response to file
    with open(OUTPUT_FILENAME, "wb") as f:
        f.write(audio_bytes)
    
    print("▶️ Playing response...")
    if os.name == 'nt':  # Windows
        os.system(f"start {OUTPUT_FILENAME}")
    else:  # Mac / Linux
        os.system(f"afplay {OUTPUT_FILENAME}" if os.uname().sysname == 'Darwin' else f"aplay {OUTPUT_FILENAME}")

def main():
    while True:
        try:
            input("\nPress Enter to start talking (or Ctrl+C to quit)...")
            
            record_audio()
            user_text = transcribe_audio()

            if not user_text:
                print("I didn't hear anything.")
                continue

            ai_response = get_ai_response(user_text)
            text_to_speech(ai_response)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()