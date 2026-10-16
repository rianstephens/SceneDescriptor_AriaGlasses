# SceneDescriptor_AriaGlasses
A Python script for Meta Project Aria Gen 2 smart glasses that describes the objects in front of the user.

## How it works

The script streams a first-person RGB image from the Aria glasses to a connected computer via USB, sends the frame to Claude's vision API for scene analysis, and reads the description aloud through the Mac's speakers using neural text-to-speech — all in a single command.

## Features

- Real-time scene description using Claude Sonnet (claude-sonnet-4-6)
- Text to Speech
- Single command to capture, describe and speak
- Runs entirely over USB 

## Requirements

- Meta Project Aria Gen 2 glasses with ARK research access
- Mac with Apple Silicon (M-series or A-series chip), macOS 14+
- Python 3.12
- Claude API key from [console.anthropic.com](https://console.anthropic.com)

## Setup

**1. Install Homebrew:**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**2. Install Python 3.12:**
```bash
brew install python@3.12
```

**3. Create a virtual environment:**
```bash
python3.12 -m venv ~/aria_env
source ~/aria_env/bin/activate
```

**4. Install dependencies:**
```bash
pip install projectaria-client-sdk anthropic edge-tts opencv-python numpy
```

**5. Pair your glasses (one time only):**
```bash
aria_gen2 auth pair
```
Approve the connection in the Aria companion app on your phone.

**6. Add your Claude API key:**
Open `Aria_Scene_Describer.py` and replace `your-api-key-here` with your key.

## Usage

Run:

```bash
source ~/aria_env/bin/activate
python3 Aria_Scene_Describer.py
```

If you get a "User session already started" error:
```bash
aria_gen2 streaming stop
```
Then run the script again.
