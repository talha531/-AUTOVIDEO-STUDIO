# 🎬 Script to Video Pexels App

An AI-powered **Script-to-Video Generator** built with **Python and Streamlit**.

The application takes a written video script, uses a **Groq AI model** to break it into scenes, searches for suitable stock footage from **Pexels**, and creates a complete video with voiceover, captions and transitions.

---

## ✨ Features

* 📝 Enter or generate a video script
* 🧠 Groq AI reads the script and decides how many scenes it needs
* 🎬 Automatically organize the script into scenes
* 🔎 Search Pexels for relevant stock videos and photos
* 🖼️ Automatically pick suitable footage for each scene
* 🎙️ Voice-over in several languages, male or female, with speed control
* 🔇 Silent mode with captions, for people who cannot use sound
* 🎵 Add background music
* ⏱️ Organize scenes according to the narration
* 🎥 Generate a complete video from multiple clips
* 🌐 Simple Streamlit web interface
* 🔑 Groq and Pexels API integration
* 🐍 Built with Python

---

## 🏗️ Project Architecture

```text
script_to_video_pexels_app/
│
├── .streamlit/
│   └── config.toml
│
├── script_to_video/
│   ├── app.py
│   └── core/
│       ├── analyzer.py     # Groq: script -> scenes
│       ├── pexels.py       # Pexels search and downloads
│       ├── tts.py          # voices and speed
│       └── render.py       # captions, transitions, FFmpeg
│
├── .gitignore
├── README.md
└── requirements.txt
```

---

## ⚙️ Requirements

Make sure you have the following installed:

* Python 3.10+
* pip
* Git
* **Groq API Key** (free)
* **Pexels API Key** (free)
* FFmpeg (needed to build the video)

Python packages (`requirements.txt`):

```text
streamlit>=1.40
groq>=0.11
requests>=2.31
Pillow>=10.0
edge-tts>=6.1
arabic-reshaper>=3.0
python-bidi>=0.4.2
python-dotenv>=1.0
```

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/script-to-video-pexels-app.git
```

Go into the project directory:

```bash
cd script-to-video-pexels-app
```

---

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

---

## 🔑 API Keys

The application needs two free API keys.

| Key | Used for | Get it here |
| --- | --- | --- |
| **Groq API Key** | AI scene planning from your script | https://console.groq.com/keys |
| **Pexels API Key** | Searching stock videos and photos | https://www.pexels.com/api/ |

### Easiest way: enter the keys in the app

Run the app, then paste both keys into the **sidebar** under **Setup**.
A green check ✅ appears when a key is added.

### Optional: save the keys so you don't type them every time

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
PEXELS_API_KEY=your_pexels_api_key_here
```

Then add these two lines at the very top of `script_to_video/app.py`:

```python
from dotenv import load_dotenv
load_dotenv()
```

Or set them for the current PowerShell window only:

```powershell
$env:GROQ_API_KEY="your_groq_api_key_here"
$env:PEXELS_API_KEY="your_pexels_api_key_here"
```

**Never upload your API keys to GitHub.**

The `.env` file must stay inside `.gitignore`.

---

## ▶️ Run the Application

The main Streamlit application is located at:

```text
script_to_video/app.py
```

From the project root, run:

```powershell
streamlit run .\script_to_video\app.py
```

The application will normally open at:

```text
http://localhost:8501
```

> The theme file `.streamlit/config.toml` must be in the folder you run the command from (the project root). Restart Streamlit after changing it.

---

## 🧪 Check Python Files Before Running

You can compile all Python files first:

```powershell
python -m compileall .\script_to_video
```

If there are no compilation errors, start Streamlit:

```powershell
streamlit run .\script_to_video\app.py
```

You can also run both commands together:

```powershell
python -m compileall .\script_to_video; if ($LASTEXITCODE -eq 0) { streamlit run .\script_to_video\app.py }
```

---

## 🎥 Example Workflow

The application workflow is designed around the following process:

```text
        ┌──────────────────┐
        │   Enter Script   │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ Groq AI Analyzes │
        │  the Script      │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │   Create Scenes  │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ Search Pexels API│
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ Auto-Pick Footage│
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ Add Narration    │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ Add Music / Audio│
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │ Render Final Video│
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │   Final Video    │
        └──────────────────┘
```

---

## 📝 Example Script

Example input:

```text
As the sun rises over the African savanna,
a family of elephants begins its journey.

The herd searches for water and food while
the young calves stay close to their mothers.

Elephants communicate using sounds, body
language, and low-frequency calls.

Their remarkable memory allows older elephants
to remember important water sources and
migration routes.
```

The Groq AI model organizes this into scenes such as:

```text
Scene 1 → African savanna sunrise
Scene 2 → Elephant family walking
Scene 3 → Baby elephant with mother
Scene 4 → Elephants communicating
Scene 5 → Elephants searching for water
```

Pexels footage is then searched and picked for each scene.

---

## 🛠️ Technology Stack

| Technology | Purpose                        |
| ---------- | ------------------------------ |
| Python     | Core programming language      |
| Streamlit  | Web application interface      |
| Groq API   | AI scene planning from scripts |
| Pexels API | Stock video and photo search   |
| edge-tts   | Voice-over generation          |
| FFmpeg     | Video/audio processing         |
| Git        | Version control                |
| GitHub     | Source-code hosting            |

---

## 🔐 Security

Do **not** commit sensitive information to GitHub.

Never upload:

```text
.env
API keys (Groq, Pexels)
passwords
tokens
private credentials
.venv/
```

Example `.gitignore`:

```gitignore
.venv/
__pycache__/
*.pyc
.env
.streamlit/secrets.toml

*.mp4
*.avi
*.mov
*.mkv

output/
temp/
.cache/
media_cache/
```

If an API key is accidentally pushed to GitHub, revoke it immediately and create a new key.

---

## 📂 Generated Files

Generated videos and temporary media should normally be stored outside Git tracking.

Recommended folders:

```text
output/
temp/
downloads/
media_cache/
```

These folders should be included in `.gitignore`.

---

## 🧑‍💻 Development

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Compile the application:

```powershell
python -m compileall .\script_to_video
```

Run Streamlit:

```powershell
streamlit run .\script_to_video\app.py
```

---

## 🐛 Troubleshooting

### Streamlit says `File does not exist: app.py`

Make sure you are running:

```powershell
streamlit run .\script_to_video\app.py
```

rather than:

```powershell
streamlit run app.py
```

The main application is located inside the `script_to_video` directory.

---

### "Add both API keys" or the scenes look like plain sentence splits

* Check that both keys are entered in the sidebar (both show ✅).
* A wrong Groq key makes the app fall back to splitting the script by sentences.
* A wrong Pexels key gives a 401 or 403 error. Create a new key and paste it without spaces.

---

### Groq error or "rate limit"

The free Groq plan has usage limits. Wait a minute and try again, pick a smaller model such as `llama-3.1-8b-instant` in the sidebar, or split a very long script into parts.

---

### Video download fails halfway (`IncompleteRead`)

This is a network drop. The app retries automatically. If it keeps failing, set **Footage type** to **Photo**, and delete the `media_cache` folder once.

---

### FFmpeg not found

Check it is installed:

```powershell
ffmpeg -version
```

If it is missing, install it with:

```powershell
winget install ffmpeg
```

Then close and reopen PowerShell.

---

### Virtual environment is not activated

Run:

```powershell
.\.venv\Scripts\Activate.ps1
```

You should see:

```text
(.venv) PS C:\Users\ASH\...
```

---

### Check the location of `app.py`

Run:

```powershell
Get-ChildItem -Recurse -Filter app.py
```

---

### Check installed packages

```powershell
pip list
```

---

## 🚧 Future Improvements

Planned improvements may include:

* 🎯 Better semantic video matching
* 🎵 Automatic background music selection
* 🎨 More transitions
* 🖼️ Image-to-video support
* 🎞️ Automatic upload to YouTube
* 🧠 AI-generated scripts
* ☁️ Cloud rendering
* 📦 Batch video generation

---

## 📜 License

This project is intended for educational and development purposes.

Add your preferred open-source license before distributing the project publicly.

---

## 👨‍💻 Author

**ASH**

GitHub:

```text
https://github.com/YOUR_USERNAME
```

---

## ⭐ Support

If you find this project useful, consider giving the repository a ⭐ on GitHub.

Contributions, ideas, and improvements are welcome.
