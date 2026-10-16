import aria.sdk_gen2 as sdk_gen2
import aria.stream_receiver as receiver
import anthropic
import base64
import threading
import asyncio
import cv2
import numpy as np
import edge_tts
import subprocess
import tempfile
import os
import signal

# ── Config ──────────────────────────────────────────────────────────────────
CLAUDE_API_KEY = "your-api-key-here"  
VOICE = "en-GB-SoniaNeural"
# ────────────────────────────────────────────────────────────────────────────

async def generate_speech(text):
    communicate = edge_tts.Communicate(text, voice=VOICE)
    mp3_chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            mp3_chunks.append(chunk["data"])
    return b"".join(mp3_chunks)

def main():
    # Connect to device
    print("Connecting to Aria glasses...")
    device_client = sdk_gen2.DeviceClient()
    device = device_client.connect()
    print("Connected.")

    # Configure and start streaming over USB
    streaming_config = sdk_gen2.HttpStreamingConfig()
    streaming_config.profile_name = "profile9"
    streaming_config.streaming_interface = sdk_gen2.StreamingInterface.USB_NCM
    device.set_streaming_config(streaming_config)
    device.start_streaming()

    # Set up receiver
    config = sdk_gen2.HttpServerConfig()
    config.address = "0.0.0.0"
    config.port = 6768

    stream_receiver = receiver.StreamReceiver(enable_image_decoding=True)
    stream_receiver.set_server_config(config)

    # Capture a single frame
    frame_captured = threading.Event()
    captured_frame = {}

    def rgb_callback(image_data, image_record):
        if not frame_captured.is_set():
            try:
                pixels = image_data.to_numpy_array()
                if pixels is not None and pixels.size > 0:
                    captured_frame["data"] = pixels
                    frame_captured.set()
            except Exception:
                pass

    stream_receiver.register_rgb_callback(rgb_callback)

    print("Starting streaming server, waiting for frame...")
    stream_receiver.start_server()
    frame_captured.wait(timeout=15)

    # Stop in a separate thread to avoid hanging
    def stop():
        try:
            device.stop_streaming()
        except Exception:
            pass
        try:
            stream_receiver.stop_server()
        except Exception:
            pass

    stop_thread = threading.Thread(target=stop, daemon=True)
    stop_thread.start()
    stop_thread.join(timeout=5)

    if "data" not in captured_frame:
        print("No frame captured.")
        return

    print("Frame captured.")

    # Encode frame as JPEG for Claude
    _, buffer = cv2.imencode(".jpg", captured_frame["data"])
    image_b64 = base64.standard_b64encode(buffer).decode("utf-8")

    # Send to Claude
    print("Sending to Claude...")
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_b64,
                    },
                },
                {
                    "type": "text",
                    "text": (
                        "Describe what is in front of the user in 1-2 concise sentences, "
                        "focus on the most important things "
                        "in the scene — obstacles, people, objects, or text. "
                        "Do not use any markdown formatting, asterisks, or special characters — plain text only."
                    )
                }
            ],
        }],
    )

    description = message.content[0].text
    print(f"Description: {description}")

    # Generate speech as MP3 and play through Mac speakers
    print("Generating and playing speech...")
    mp3_data = asyncio.run(generate_speech(description))

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name
    with open(tmp_path, "wb") as f:
        f.write(mp3_data)
    subprocess.run(["afplay", tmp_path])
    os.unlink(tmp_path)

    print("Done.")

if __name__ == "__main__":
    main()