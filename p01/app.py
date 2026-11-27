"""Mini visual-novel engine.

Run as a local web app:
    python app.py --mode web

Run in a desktop window (requires pywebview):
    python app.py --mode desktop

Edit the STORY dictionary below to write your own story.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import socket
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


# When packaged with PyInstaller, the HTML file is bundled in _MEIPASS.
# Keep the assets/ folder beside the executable so you can replace images easily.
if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
else:
    APP_DIR = Path(__file__).resolve().parent
    RESOURCE_DIR = APP_DIR

HTML_FILE = RESOURCE_DIR / "index.html"
ASSETS_DIR = APP_DIR / "assets"
ASSETS_DIR.mkdir(exist_ok=True)


# ============================================================================
# STORY CONTENT: EDIT THIS PART
# ============================================================================
# A scene contains:
#   chapter      Optional chapter label.
#   background   Image path inside assets/, e.g. "assets/backgrounds/room.jpg".
#   dialogue     A list of dialogue lines. Each line has speaker, avatar, text.
#   choices      A list of choices. Each choice has label and next (scene ID).
#   next         Optional automatic next scene when there are no choices.
#   ending       Set True to mark an ending scene.
#
# Avatar paths are optional. Use "" if the line has no portrait.
# Keep scene IDs unique. Every choice's "next" must match a scene ID below.

STORY = {
    "title": "MY STORY",
    "start": "intro",
    "scenes": {
        "intro": {
            "chapter": "CHAPTER 01 · START",
            "background": "assets/backgrounds/room.jpg",
            "dialogue": [
                {
                    "speaker": "NARRATOR",
                    "avatar": "",
                    "text": "[Viết lời dẫn mở đầu của mày ở đây.]",
                },
                {
                    "speaker": "CHARACTER A",
                    "avatar": "assets/characters/character_a.png",
                    "text": "[Viết câu thoại đầu tiên ở đây.]",
                },
            ],
            "choices": [
                {"label": "[Lựa chọn thứ nhất]", "next": "branch_a"},
                {"label": "[Lựa chọn thứ hai]", "next": "branch_b"},
            ],
        },
        "branch_a": {
            "chapter": "CHAPTER 01 · ROUTE A",
            "background": "",
            "dialogue": [
                {
                    "speaker": "CHARACTER A",
                    "avatar": "assets/characters/character_a.png",
                    "text": "[Viết nội dung nhánh A.]",
                }
            ],
            "choices": [
                {"label": "[Đi đến kết thúc A]", "next": "ending_a"},
                {"label": "[Quay sang nhánh B]", "next": "branch_b"},
            ],
        },
        "branch_b": {
            "chapter": "CHAPTER 01 · ROUTE B",
            "background": "",
            "dialogue": [
                {
                    "speaker": "CHARACTER B",
                    "avatar": "assets/characters/character_b.png",
                    "text": "[Viết nội dung nhánh B.]",
                }
            ],
            "choices": [
                {"label": "[Đi đến kết thúc B]", "next": "ending_b"},
            ],
        },
        "ending_a": {
            "chapter": "ENDING A",
            "background": "assets/backgrounds/ending.jpg",
            "dialogue": [
                {
                    "speaker": "SYSTEM",
                    "avatar": "",
                    "text": "[Viết nội dung kết thúc A.]",
                }
            ],
            "choices": [],
            "ending": True,
        },
        "ending_b": {
            "chapter": "ENDING B",
            "background": "assets/backgrounds/ending.jpg",
            "dialogue": [
                {
                    "speaker": "SYSTEM",
                    "avatar": "",
                    "text": "[Viết nội dung kết thúc B.]",
                }
            ],
            "choices": [],
            "ending": True,
        },
    },
}


# ============================================================================
# GAME ENGINE: NORMALLY YOU DO NOT NEED TO EDIT BELOW THIS LINE
# ============================================================================


def validate_story() -> None:
    """Fail early when a scene or branch points to an invalid scene ID."""
    scenes = STORY.get("scenes")
    start = STORY.get("start")

    if not isinstance(scenes, dict) or not scenes:
        raise ValueError("STORY['scenes'] must be a non-empty dictionary.")
    if start not in scenes:
        raise ValueError(f"Start scene '{start}' does not exist.")

    for scene_id, scene in scenes.items():
        if not isinstance(scene, dict):
            raise ValueError(f"Scene '{scene_id}' must be a dictionary.")

        dialogue = scene.get("dialogue", [])
        choices = scene.get("choices", [])
        if not isinstance(dialogue, list):
            raise ValueError(f"Scene '{scene_id}': 'dialogue' must be a list.")
        if not isinstance(choices, list):
            raise ValueError(f"Scene '{scene_id}': 'choices' must be a list.")

        for line_number, line in enumerate(dialogue, start=1):
            if not isinstance(line, dict) or not isinstance(line.get("text", ""), str):
                raise ValueError(
                    f"Scene '{scene_id}', dialogue line {line_number}: "
                    "each line needs a text string."
                )

        for choice_number, choice in enumerate(choices, start=1):
            if not isinstance(choice, dict):
                raise ValueError(f"Scene '{scene_id}': choice {choice_number} is invalid.")
            target = choice.get("next")
            if target not in scenes:
                raise ValueError(
                    f"Scene '{scene_id}', choice {choice_number}: "
                    f"target scene '{target}' does not exist."
                )

        next_scene = scene.get("next")
        if next_scene is not None and next_scene not in scenes:
            raise ValueError(f"Scene '{scene_id}' points to missing next scene '{next_scene}'.")
        if choices and next_scene:
            raise ValueError(
                f"Scene '{scene_id}' cannot use both 'choices' and 'next'. Use one or the other."
            )


def json_response(handler: BaseHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


class StoryRequestHandler(BaseHTTPRequestHandler):
    server_version = "MiniStoryGame/1.0"

    def log_message(self, fmt: str, *args) -> None:
        # Keep the terminal clean while the game is running.
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)

        if parsed.path == "/" or parsed.path == "/index.html":
            self._send_file(HTML_FILE)
            return

        if parsed.path == "/api/story":
            json_response(
                self,
                {"title": STORY.get("title", "STORY"), "start": STORY["start"]},
            )
            return

        if parsed.path == "/api/scene":
            query = parse_qs(parsed.query)
            scene_id = query.get("id", [""])[0]
            scene = STORY["scenes"].get(scene_id)
            if scene is None:
                json_response(self, {"error": f"Unknown scene: {scene_id}"}, 404)
                return
            json_response(self, {"id": scene_id, "scene": scene})
            return

        if parsed.path.startswith("/assets/"):
            relative_path = unquote(parsed.path[len("/assets/"):])
            self._send_asset(relative_path)
            return

        json_response(self, {"error": "Not found"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length > 64_000:
                json_response(self, {"error": "Request too large"}, 413)
                return
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8") or "{}")
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            json_response(self, {"error": "Invalid JSON request"}, 400)
            return

        scene_id = payload.get("scene_id") if isinstance(payload, dict) else None
        scene = STORY["scenes"].get(scene_id)
        if scene is None:
            json_response(self, {"error": "Current scene does not exist"}, 404)
            return

        if parsed.path == "/api/choose":
            try:
                choice_index = int(payload.get("choice_index"))
                choices = scene.get("choices", [])
                choice = choices[choice_index]
            except (TypeError, ValueError, IndexError):
                json_response(self, {"error": "Invalid choice"}, 400)
                return
            target_id = choice["next"]
            json_response(
                self,
                {"id": target_id, "scene": STORY["scenes"][target_id]},
            )
            return

        if parsed.path == "/api/continue":
            target_id = scene.get("next")
            if not target_id:
                json_response(self, {"error": "This scene has no next scene"}, 400)
                return
            json_response(
                self,
                {"id": target_id, "scene": STORY["scenes"][target_id]},
            )
            return

        json_response(self, {"error": "Not found"}, 404)

    def _send_file(self, path: Path) -> None:
        try:
            data = path.read_bytes()
        except FileNotFoundError:
            json_response(self, {"error": "index.html was not found"}, 404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_asset(self, relative_path: str) -> None:
        # Block path traversal so requests cannot read files outside assets/.
        root = ASSETS_DIR.resolve()
        candidate = (root / relative_path).resolve()
        if candidate != root and root not in candidate.parents:
            json_response(self, {"error": "Invalid asset path"}, 403)
            return
        if not candidate.is_file():
            json_response(self, {"error": "Asset not found"}, 404)
            return

        data = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(data)


def make_server() -> ThreadingHTTPServer:
    # Port 0 asks the OS to assign an available local port.
    server = ThreadingHTTPServer(("127.0.0.1", 0), StoryRequestHandler)
    return server


def main() -> None:
    validate_story()

    parser = argparse.ArgumentParser(description="Run your mini story game.")
    parser.add_argument(
        "--mode",
        choices=("web", "desktop", "server"),
        default="web",
        help="web: open in browser; desktop: open a desktop window; server: serve without opening a window",
    )
    args = parser.parse_args()

    if not HTML_FILE.is_file():
        raise FileNotFoundError(
            f"Cannot find {HTML_FILE}. Keep index.html beside app.py, "
            "or bundle it with PyInstaller."
        )

    server = make_server()
    host, port = server.server_address
    url = f"http://{host}:{port}/"

    if args.mode == "server":
        print(f"Game server running at {url}")
        print("Press Ctrl+C to stop.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    try:
        if args.mode == "web":
            print(f"Opening game at {url}")
            webbrowser.open(url)
            print("Keep this terminal open while playing. Press Ctrl+C to stop the server.")
            try:
                server_thread.join()
            except KeyboardInterrupt:
                pass
        else:
            try:
                import webview  # type: ignore
            except ImportError as exc:
                raise SystemExit(
                    "Desktop mode needs pywebview. Install it with: pip install pywebview"
                ) from exc

            webview.create_window(
                STORY.get("title", "MY STORY"),
                url,
                width=1100,
                height=760,
                min_size=(720, 520),
                resizable=True,
                background_color="#f3f4f6",
            )
            webview.start()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
