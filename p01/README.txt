MINI STORY GAME - QUICK START

FILES
- app.py      Python story engine + local server + optional desktop window.
- index.html  Interface, CSS and JavaScript.
- assets/     Put your character portraits and backgrounds here.

RUN AS A WEB APP
1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Run: python app.py --mode web
4. Your browser opens the game. Keep the terminal open while playing.

RUN AS A DESKTOP WINDOW
1. Install dependencies: pip install pywebview
2. Run: python app.py --mode desktop

WRITE YOUR STORY
Open app.py and edit the STORY dictionary near the top of the file.
Each scene has a unique ID, dialogue list, and choices. Each choice's "next"
value must match the ID of another scene.

IMAGE PATH EXAMPLES
"avatar": "assets/characters/alex.png"
"background": "assets/backgrounds/bedroom.jpg"
Store those files inside the matching folders under assets/.

BUILD A WINDOWS EXE (run this on Windows)
1. Install: pip install pywebview pyinstaller
2. Run this command in the project folder:
   pyinstaller --noconfirm --clean --onedir --windowed --name MyStoryGame --add-data "index.html;." --collect-all webview app.py
3. Copy your assets/ folder into dist/MyStoryGame/ beside MyStoryGame.exe.
4. Open dist/MyStoryGame/MyStoryGame.exe.

The .exe is built on your own Windows computer. This source project is
cross-platform for development; the Windows build command is shown above.
