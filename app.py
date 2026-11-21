from __future__ import annotations

import html
import json
import os
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse


ROOT = Path(__file__).parent
STATE_FILE = ROOT / "data" / "state.json"
TEMPLATE_FILE = ROOT / "templates" / "index.html"
INVENTORY_ITEMS = ("puupalikat", "kangas", "kuivaruoka", "kolikko")
STATIC_FILES = {
    "/static/style.css": (ROOT / "static" / "style.css", "text/css; charset=utf-8"),
    "/pictures/kissatodo.png": (ROOT / "pictures" / "kissatodo.png", "image/png"),
}

DIFFICULTIES = {
    "super_easy": {
        "label": "Super helppo",
        "minutes": 5,
        "duration": "1–5 min",
        "xp": 5,
        "rewards": {"puupalikat": 0, "kangas": 0, "kuivaruoka": 1, "kolikko": 1},
    },
    "easy": {
        "label": "Helppo",
        "minutes": 10,
        "duration": "10 min",
        "xp": 10,
        "rewards": {"puupalikat": 1, "kangas": 0, "kuivaruoka": 1, "kolikko": 1},
    },
    "medium": {
        "label": "Keskivaikea",
        "minutes": 30,
        "duration": "30 min",
        "xp": 30,
        "rewards": {"puupalikat": 2, "kangas": 1, "kuivaruoka": 2, "kolikko": 3},
    },
    "hard": {
        "label": "Vaikea",
        "minutes": 60,
        "duration": "1 tunti",
        "xp": 60,
        "rewards": {"puupalikat": 4, "kangas": 3, "kuivaruoka": 3, "kolikko": 6},
    },
    "kill": {
        "label": "Kill",
        "minutes": 121,
        "duration": "yli 2 tuntia",
        "xp": 150,
        "rewards": {"puupalikat": 10, "kangas": 8, "kuivaruoka": 10, "kolikko": 20},
    },
}

PRESET_TASKS = (
    ("Kasvin kastelu", "super_easy"),
    ("Tiskit", "easy"),
    ("Imurointi", "easy"),
    ("Sängyn petaus", "easy"),
    ("Kaupassakäynti", "medium"),
    ("Koulutehtävä", "hard"),
    ("Vaatekaapin siivous", "hard"),
    ("Koko kodin suursiivous", "kill"),
)


def new_state() -> dict:
    return {
        "tasks": [],
        "inventory": {item: 0 for item in INVENTORY_ITEMS},
        "xp": 0,
    }


def load_state() -> dict:
    if not STATE_FILE.exists():
        return new_state()
    with STATE_FILE.open(encoding="utf-8") as state_file:
        state = json.load(state_file)
    if (
        not isinstance(state, dict)
        or not isinstance(state.get("tasks"), list)
        or not isinstance(state.get("inventory"), dict)
        or not isinstance(state.get("xp"), int)
    ):
        raise ValueError("Tallennettu sovellustila on virheellinen.")
    for item in INVENTORY_ITEMS:
        if not isinstance(state["inventory"].get(item), int):
            raise ValueError("Tallennetut inventaariotiedot ovat virheelliset.")
    return state


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = STATE_FILE.with_suffix(".tmp")
    with temporary_file.open("w", encoding="utf-8") as state_file:
        json.dump(state, state_file, ensure_ascii=False, indent=2)
    os.replace(temporary_file, STATE_FILE)


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def parse_subtasks(value: str) -> list[str]:
    subtasks = [line.strip() for line in value.splitlines() if line.strip()]
    if subtasks and len(subtasks) < 2:
        raise ValueError("Kirjoita vähintään kaksi osatehtävää.")
    if len(subtasks) > 10:
        raise ValueError("Tehtävässä voi olla enintään 10 osaa.")
    if any(len(subtask) > 80 for subtask in subtasks):
        raise ValueError("Osatehtävän nimi voi olla enintään 80 merkkiä.")
    return subtasks


def render_subtasks(task: dict, difficulty: dict) -> str:
    subtasks = task.get("subtasks", [])
    if not subtasks:
        return ""

    completed_count = sum(subtask["completed"] for subtask in subtasks)
    rows = []
    for subtask in subtasks:
        name = escape(subtask["name"])
        if subtask["completed"]:
            action = '<span class="subtask-done">Valmis ✓</span>'
            row_class = "subtask-row subtask-row-done"
        else:
            action = f"""
              <form method="post" class="subtask-complete-form">
                <input type="hidden" name="action" value="complete_subtask">
                <input type="hidden" name="task_id" value="{escape(task["id"])}">
                <input type="hidden" name="subtask_id" value="{escape(subtask["id"])}">
                <button class="button button-subtask" type="submit">Valmis · +5 XP</button>
              </form>
            """
            row_class = "subtask-row"
        rows.append(f'<li class="{row_class}"><span class="subtask-name">{name}</span>{action}</li>')

    return f"""
      <div class="subtasks-panel">
        <div class="subtasks-heading">
          <strong>Osatehtävät</strong>
          <span>{completed_count} / {len(subtasks)} valmiina</span>
        </div>
        <ul class="subtask-list">{"".join(rows)}</ul>
        <p class="subtask-reward-note">Jokaisesta osasta +5 XP, 1 kuivaruoka ja 1 kolikko. Kaikkien osien valmistumisesta lisäksi +{difficulty["xp"]} XP:n kokonaisbonus palkintoineen.</p>
      </div>
    """


def render_task(task: dict) -> str:
    difficulty = DIFFICULTIES[task["difficulty"]]
    subtasks = task.get("subtasks", [])
    if subtasks:
        completed_count = sum(subtask["completed"] for subtask in subtasks)
        task_meta = (
            f'{difficulty["label"]} · {difficulty["duration"]} · '
            f'{completed_count}/{len(subtasks)} osaa · kokonaisbonus +{difficulty["xp"]} XP'
        )
        subtask_html = render_subtasks(task, difficulty)
        action_html = ""
    else:
        task_meta = f'{difficulty["label"]} · {difficulty["duration"]} · +{difficulty["xp"]} tassupistettä'
        subtask_html = ""
        action_html = f"""
          <form method="post" class="complete-form">
            <input type="hidden" name="action" value="complete">
            <input type="hidden" name="task_id" value="{escape(task["id"])}">
            <button class="button button-complete" type="submit">Valmis!</button>
          </form>
        """

    return f"""
      <li class="task-card">
        <div class="task-main">
          <div class="task-info">
            <strong>{escape(task["name"])}</strong>
            <span class="task-meta">{task_meta}</span>
          </div>
          {action_html}
        </div>
        {subtask_html}
      </li>
    """


def render_page(state: dict, error: str = "") -> bytes:
    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    tasks = "\n".join(render_task(task) for task in state["tasks"])
    if not tasks:
        tasks = '<li class="empty-state">Lista on tyhjä. Lisää ensimmäinen tehtäväsi!</li>'

    level = state["xp"] // 100 + 1
    progress = state["xp"] % 100
    cat_size = 96 * (1 + 0.03 * (state["xp"] // 30))
    inventory = "\n".join(
        f'<li><span>{label}</span><strong>{state["inventory"][key]}</strong></li>'
        for key, label in (
            ("puupalikat", "🪵 Puupalikat"),
            ("kangas", "🧵 Kangas"),
            ("kuivaruoka", "🐟 Kuivaruoka"),
            ("kolikko", "🪙 Kolikot"),
        )
    )
    preset_options = "\n".join(
        f'<option value="{escape(name)}" data-difficulty="{difficulty}">{escape(name)} ({DIFFICULTIES[difficulty]["label"].lower()})</option>'
        for name, difficulty in PRESET_TASKS
    )
    difficulty_options = "\n".join(
        f'<option value="{key}">{item["label"]} · {item["duration"]}</option>'
        for key, item in DIFFICULTIES.items()
    )
    error_html = f'<p class="form-error" role="alert">{escape(error)}</p>' if error else ""

    page = (
        template.replace("{{TASKS}}", tasks)
        .replace("{{INVENTORY}}", inventory)
        .replace("{{PRESET_OPTIONS}}", preset_options)
        .replace("{{DIFFICULTY_OPTIONS}}", difficulty_options)
        .replace("{{ERROR}}", error_html)
        .replace("{{LEVEL}}", str(level))
        .replace("{{XP}}", str(state["xp"]))
        .replace("{{PROGRESS}}", str(progress))
        .replace("{{CAT_SIZE}}", f"{cat_size:.1f}")
    )
    return page.encode("utf-8")


class TodoHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        asset = STATIC_FILES.get(urlparse(self.path).path)
        if asset is not None:
            asset_path, content_type = asset
            try:
                body = asset_path.read_bytes()
            except OSError as exc:
                self.send_error(404, f"Tiedoston lataaminen epäonnistui: {exc}")
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        try:
            state = load_state()
            error = parse_qs(urlparse(self.path).query).get("error", [""])[0]
            body = render_page(state, error)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self.send_error(500, f"Sovelluksen tietojen lataaminen epäonnistui: {exc}")
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        form = parse_qs(self.rfile.read(length).decode("utf-8"))
        try:
            action = form.get("action", [""])[0]
            if action == "reset":
                save_state(new_state())
                self.redirect()
                return

            state = load_state()
            if action == "add_preset":
                name = form.get("preset", [""])[0]
                difficulty = next((level for preset, level in PRESET_TASKS if preset == name), None)
                if difficulty is None:
                    raise ValueError("Valitse tehtävä valmiista listasta.")
                subtasks = parse_subtasks(form.get("subtasks", [""])[0])
                add_task(state, name, difficulty, subtasks)
            elif action == "add_custom":
                name = form.get("name", [""])[0].strip()
                difficulty = form.get("difficulty", [""])[0]
                if not name or len(name) > 80:
                    raise ValueError("Kirjoita tehtävän nimi (1–80 merkkiä).")
                if difficulty not in DIFFICULTIES:
                    raise ValueError("Valitse tehtävälle vaikeustaso.")
                subtasks = parse_subtasks(form.get("subtasks", [""])[0])
                add_task(state, name, difficulty, subtasks)
            elif action == "complete":
                task_id = form.get("task_id", [""])[0]
                task = next((task for task in state["tasks"] if task["id"] == task_id), None)
                if task is None:
                    raise ValueError("Tehtävää ei löytynyt. Päivitä sivu ja yritä uudelleen.")
                if task.get("subtasks"):
                    raise ValueError("Viimeistele kaikki osatehtävät ennen kokonaisbonusta.")
                reward = DIFFICULTIES[task["difficulty"]]
                for item, amount in reward["rewards"].items():
                    state["inventory"][item] += amount
                state["xp"] += reward["xp"]
                state["tasks"].remove(task)
            elif action == "complete_subtask":
                task_id = form.get("task_id", [""])[0]
                subtask_id = form.get("subtask_id", [""])[0]
                task = next((task for task in state["tasks"] if task["id"] == task_id), None)
                if task is None or not task.get("subtasks"):
                    raise ValueError("Jaettua tehtävää ei löytynyt.")
                subtask = next(
                    (part for part in task["subtasks"] if part["id"] == subtask_id),
                    None,
                )
                if subtask is None or subtask["completed"]:
                    raise ValueError("Osatehtävä on jo valmis tai sitä ei löytynyt.")
                subtask["completed"] = True
                state["xp"] += 5
                state["inventory"]["kuivaruoka"] += 1
                state["inventory"]["kolikko"] += 1
                if all(part["completed"] for part in task["subtasks"]):
                    reward = DIFFICULTIES[task["difficulty"]]
                    for item, amount in reward["rewards"].items():
                        state["inventory"][item] += amount
                    state["xp"] += reward["xp"]
                    state["tasks"].remove(task)
            else:
                raise ValueError("Tuntematon toiminto.")
            save_state(state)
            self.redirect()
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self.redirect(str(exc))

    def redirect(self, error: str = "") -> None:
        location = "/" if not error else "/?" + urlencode({"error": error})
        self.send_response(303)
        self.send_header("Location", location)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def add_task(
    state: dict,
    name: str,
    difficulty: str,
    subtasks: list[str] | None = None,
) -> None:
    state["tasks"].append(
        {
            "id": uuid.uuid4().hex,
            "name": name,
            "difficulty": difficulty,
            "subtasks": [
                {"id": uuid.uuid4().hex, "name": subtask, "completed": False}
                for subtask in (subtasks or [])
            ],
        }
    )


if __name__ == "__main__":
    print("meoww: http://127.0.0.1:8000")
    HTTPServer(("127.0.0.1", 8000), TodoHandler).serve_forever()
