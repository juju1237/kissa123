from __future__ import annotations

import html
import json
import os
import random
import uuid
from datetime import date
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
    "/pictures/fih.png": (ROOT / "pictures" / "fih.png", "image/png"),
    "/pictures/raha.png": (ROOT / "pictures" / "raha.png", "image/png"),
    "/pictures/paketti1.png": (ROOT / "pictures" / "paketti1.png", "image/png"),
    "/pictures/paketti2.png": (ROOT / "pictures" / "paketti2.png", "image/png"),
    "/pictures/paketti3.png": (ROOT / "pictures" / "paketti3.png", "image/png"),
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
        "label": "eezy",
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

PACKAGE_RESOURCES = {
    "puupalikat": ("🪵 puupalikka", "🪵 puupalikkaa"),
    "kangas": ("🧵 kangas", "🧵 kangasta"),
    "kuivaruoka": ("kala", "kalaa"),
    "kolikko": ("raha", "rahaa"),
}
RESOURCE_IMAGES = {"kuivaruoka": "fih.png", "kolikko": "raha.png"}
PACKAGE_IMAGES = ("paketti1.png", "paketti2.png", "paketti3.png")


def new_state() -> dict:
    return {
        "tasks": [],
        "inventory": {item: 0 for item in INVENTORY_ITEMS},
        "xp": 0,
        "daily_surprise": None,
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


def grant_reward(state: dict, reward: dict, multiplier: int = 1) -> None:
    for item, amount in reward["rewards"].items():
        state["inventory"][item] += amount * multiplier
    state["xp"] += reward["xp"] * multiplier


def grant_surprise_package(
    state: dict,
    multiplier: int = 1,
) -> tuple[str, int, str]:
    item = random.choice(INVENTORY_ITEMS)
    state["inventory"][item] += multiplier
    package_image = random.choice(PACKAGE_IMAGES)
    return item, multiplier, package_image


def ensure_daily_surprise(state: dict) -> dict:
    today = date.today().isoformat()
    surprise = state.get("daily_surprise")
    valid_preset = (
        isinstance(surprise, dict)
        and (surprise.get("name"), surprise.get("difficulty")) in PRESET_TASKS
    )
    if (
        not valid_preset
        or surprise.get("date") != today
        or not isinstance(surprise.get("claimed"), bool)
    ):
        name, difficulty = random.choice(PRESET_TASKS)
        surprise = {
            "date": today,
            "name": name,
            "difficulty": difficulty,
            "claimed": False,
        }
        state["daily_surprise"] = surprise
        save_state(state)
    return surprise


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def render_surprise_package(
    reward_package: tuple[str, int, str] | None,
) -> str:
    if reward_package is None:
        return ""
    item, amount, package_image = reward_package
    if (
        item not in PACKAGE_RESOURCES
        or amount not in (1, 2)
        or package_image not in PACKAGE_IMAGES
    ):
        return ""
    resource_name = PACKAGE_RESOURCES[item][0 if amount == 1 else 1]
    resource_image = RESOURCE_IMAGES.get(item)
    resource_icon = (
        f'<img class="package-resource-icon" src="/pictures/{resource_image}" alt="">'
        if resource_image
        else ""
    )
    return f"""
      <section class="reward-package" aria-live="polite">
        <details>
          <summary><img class="package-thumb" src="/pictures/{package_image}" alt=""> siis ei voi olla todellista</summary>
          <div class="package-reveal">
            <img class="package-art" src="/pictures/{package_image}" alt="Avattu yllätyspaketti">
            <p>Paketista paljastui:</p>
            <strong>{resource_icon}{amount} {resource_name}</strong>
          </div>
        </details>
      </section>
    """


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
        <p class="subtask-reward-note">Jokaisesta osasta +5 XP, 1 kala ja 1 raha. Kaikkien osien valmistumisesta lisäksi +{difficulty["xp"] * (2 if task.get("double_reward") else 1)} XP:n kokonaisbonus palkintoineen.</p>
      </div>
    """


def render_task(task: dict) -> str:
    difficulty = DIFFICULTIES[task["difficulty"]]
    subtasks = task.get("subtasks", [])
    reward_multiplier = 2 if task.get("double_reward") else 1
    if subtasks:
        completed_count = sum(subtask["completed"] for subtask in subtasks)
        task_meta = (
            f'{difficulty["label"]} · {difficulty["duration"]} · '
            f'{completed_count}/{len(subtasks)} osaa · kokonaisbonus '
            f'+{difficulty["xp"] * reward_multiplier} XP'
        )
        if reward_multiplier == 2:
            task_meta += " (tuplapalkinto)"
        subtask_html = render_subtasks(task, difficulty)
        action_html = ""
    else:
        task_meta = (
            f'{difficulty["label"]} · {difficulty["duration"]} · '
            f'+{difficulty["xp"] * reward_multiplier} tassupistettä'
        )
        if reward_multiplier == 2:
            task_meta += " · päivän yllätys (tuplapalkinto)"
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


def render_page(
    state: dict,
    error: str = "",
    reward_package: tuple[str, int] | None = None,
) -> bytes:
    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    daily_surprise = ensure_daily_surprise(state)
    surprise_difficulty = DIFFICULTIES[daily_surprise["difficulty"]]
    if daily_surprise["claimed"]:
        surprise_action = '<p class="surprise-used">Päivän yllätys on jo käytetty. Uusi ehdotus tulee huomenna!</p>'
    else:
        surprise_action = """
          <form method="post">
            <input type="hidden" name="action" value="claim_daily_surprise">
            <button class="button button-surprise" type="submit">Lisää tehtävälistalle</button>
          </form>
        """
    daily_surprise_html = f"""
      <section class="daily-surprise" aria-labelledby="daily-surprise-title">
        <img class="surprise-image" src="/pictures/paketti1.png" alt="">
        <div class="surprise-content">
          <p class="eyebrow">PÄIVÄN YLLÄTYSTEHTÄVÄ</p>
          <h2 id="daily-surprise-title">{escape(daily_surprise["name"])}</h2>
          <p class="surprise-meta">{surprise_difficulty["label"]} · {surprise_difficulty["duration"]}</p>
          <p class="surprise-reward">Tuplapalkinto: +{surprise_difficulty["xp"] * 2} XP ja kaikki resurssit kaksinkertaisina.</p>
          {surprise_action}
        </div>
      </section>
    """
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
            ("kuivaruoka", '<img class="inventory-icon" src="/pictures/fih.png" alt=""> Kala'),
            ("kolikko", '<img class="inventory-icon" src="/pictures/raha.png" alt=""> Raha'),
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
        .replace("{{REWARD_PACKAGE}}", render_surprise_package(reward_package))
        .replace("{{DAILY_SURPRISE}}", daily_surprise_html)
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
        parsed_url = urlparse(self.path)
        asset = STATIC_FILES.get(parsed_url.path)
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
            query = parse_qs(parsed_url.query)
            error = query.get("error", [""])[0]
            package_item = query.get("package", [None])[0]
            package_image = query.get("art", [None])[0]
            try:
                package_amount = int(query.get("amount", ["0"])[0])
            except ValueError:
                package_amount = 0
            reward_package = (
                (package_item, package_amount, package_image)
                if package_item is not None and package_image is not None
                else None
            )
            body = render_page(state, error, reward_package)
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
            reward_package: tuple[str, int, str] | None = None
            action = form.get("action", [""])[0]
            if action == "reset":
                save_state(new_state())
                self.redirect()
                return

            state = load_state()
            if action == "claim_daily_surprise":
                surprise = ensure_daily_surprise(state)
                if surprise["claimed"]:
                    raise ValueError("Päivän yllätys on jo käytetty.")
                add_task(
                    state,
                    surprise["name"],
                    surprise["difficulty"],
                    double_reward=True,
                )
                surprise["claimed"] = True
            elif action == "add_preset":
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
                reward_multiplier = 2 if task.get("double_reward") else 1
                grant_reward(state, reward, reward_multiplier)
                reward_package = grant_surprise_package(state, reward_multiplier)
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
                reward_package = grant_surprise_package(state)
                if all(part["completed"] for part in task["subtasks"]):
                    reward = DIFFICULTIES[task["difficulty"]]
                    grant_reward(state, reward, 2 if task.get("double_reward") else 1)
                    state["tasks"].remove(task)
            else:
                raise ValueError("Tuntematon toiminto.")
            save_state(state)
            self.redirect(reward_package=reward_package)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self.redirect(str(exc))

    def redirect(
        self,
        error: str = "",
        reward_package: tuple[str, int, str] | None = None,
    ) -> None:
        if error:
            location = "/?" + urlencode({"error": error})
        elif reward_package is not None:
            location = "/?" + urlencode(
                {
                    "package": reward_package[0],
                    "amount": reward_package[1],
                    "art": reward_package[2],
                }
            )
        else:
            location = "/"
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
    double_reward: bool = False,
) -> None:
    state["tasks"].append(
        {
            "id": uuid.uuid4().hex,
            "name": name,
            "difficulty": difficulty,
            "double_reward": double_reward,
            "subtasks": [
                {"id": uuid.uuid4().hex, "name": subtask, "completed": False}
                for subtask in (subtasks or [])
            ],
        }
    )


if __name__ == "__main__":
    print("meoww: http://127.0.0.1:8000")
    HTTPServer(("127.0.0.1", 8000), TodoHandler).serve_forever()
