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
HOME_TEMPLATE_FILE = ROOT / "templates" / "home.html"
INVENTORY_ITEMS = ("puupalikat", "kangas", "kuivaruoka", "kolikko")
WEEKLY_TASK_GOAL = 15
WEEKLY_GOAL_REWARD = 15
STATIC_FILES = {
    "/static/style.css": (ROOT / "static" / "style.css", "text/css; charset=utf-8"),
    "/pictures/kissatodo.png": (ROOT / "pictures" / "kissatodo.png", "image/png"),
    "/pictures/lemon.png": (ROOT / "pictures" / "lemon.png", "image/png"),
    "/pictures/kapy.png": (ROOT / "pictures" / "kapy.png", "image/png"),
    "/pictures/fih.png": (ROOT / "pictures" / "fih.png", "image/png"),
    "/pictures/raha.png": (ROOT / "pictures" / "raha.png", "image/png"),
    "/pictures/paketti1.png": (ROOT / "pictures" / "paketti1.png", "image/png"),
    "/pictures/paketti2.png": (ROOT / "pictures" / "paketti2.png", "image/png"),
    "/pictures/paketti3.png": (ROOT / "pictures" / "paketti3.png", "image/png"),
}

DIFFICULTIES = {
    "super_easy": {
        "label": "Super eezy",
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
PET_TYPES = {
    "cat": {"label": "Kissa", "image": "kissatodo.png"},
    "lemon": {"label": "Sitruuna", "image": "lemon.png"},
    "pinecone": {"label": "Käpy", "image": "kapy.png"},
}
RECIPES = {
    "refined_wood": {
        "name": "Jalostettu puu",
        "icon": "🪵",
        "output": "jalostettu_puu",
        "ingredients": {"puupalikat": 3},
    },
    "pet_bed": {
        "name": "Lemmikin sänky",
        "icon": "🛏️",
        "output": "lemmikin_sanky",
        "ingredients": {"puupalikat": 3, "kangas": 2},
    },
    "pet_toy": {
        "name": "Pehmolelu",
        "icon": "🧸",
        "output": "pehmolelu",
        "ingredients": {"kangas": 3},
    },
    "small_plant": {
        "name": "Pieni kasvi",
        "icon": "🌱",
        "output": "pieni_kasvi",
        "ingredients": {"puupalikat": 2},
    },
    "big_plant": {
        "name": "Iso kasvi",
        "icon": "🪴",
        "output": "iso_kasvi",
        "ingredients": {"puupalikat": 4},
    },
    "treat": {
        "name": "Herkku",
        "icon": "🍪",
        "output": "herkku",
        "ingredients": {"kuivaruoka": 3},
    },
}
CRAFTED_ITEMS = {
    "jalostettu_puu": "Jalostettu puu",
    "lemmikin_sanky": "Lemmikin sänky",
    "pehmolelu": "Pehmolelu",
    "pieni_kasvi": "Pieni kasvi",
    "iso_kasvi": "Iso kasvi",
    "herkku": "Herkku",
}
HOME_ITEMS = {
    "lemmikin_sanky": {"name": "Lemmikin sänky", "icon": "🛏️"},
    "pehmolelu": {"name": "Pehmolelu", "icon": "🧸"},
    "pieni_kasvi": {"name": "Pieni kasvi", "icon": "🌱"},
    "iso_kasvi": {"name": "Iso kasvi", "icon": "🪴"},
}
RESOURCE_LABELS = {
    "puupalikat": "Puupalikka",
    "kangas": "Kangas",
    "kuivaruoka": "Kala",
    "kolikko": "Raha",
}
TREAT_XP = 20


def new_state() -> dict:
    return {
        "tasks": [],
        "inventory": {item: 0 for item in INVENTORY_ITEMS},
        "xp": 0,
        "daily_surprise": None,
        "pet": None,
        "weekly_goal": None,
        "crafted_items": {item: 0 for item in CRAFTED_ITEMS},
        "discovered_recipes": [],
        "home_items": [],
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
    crafted_items = state.setdefault("crafted_items", {})
    if not isinstance(crafted_items, dict):
        raise ValueError("Tallennetut askartelutiedot ovat virheelliset.")
    for item in CRAFTED_ITEMS:
        crafted_items.setdefault(item, 0)
        if type(crafted_items[item]) is not int or crafted_items[item] < 0:
            raise ValueError("Tallennetut askartelutiedot ovat virheelliset.")
    discovered_recipes = state.setdefault("discovered_recipes", [])
    if not isinstance(discovered_recipes, list) or any(
        recipe_id not in RECIPES for recipe_id in discovered_recipes
    ):
        raise ValueError("Tallennetut reseptitiedot ovat virheelliset.")
    home_items = state.setdefault("home_items", [])
    if not isinstance(home_items, list) or any(
        not isinstance(item, str) or item not in HOME_ITEMS
        for item in home_items
    ):
        raise ValueError("Tallennetut lemmikin kodin tiedot ovat virheelliset.")
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


def ensure_weekly_goal(state: dict) -> dict:
    iso_year, iso_week, _ = date.today().isocalendar()
    current_week = f"{iso_year}-W{iso_week:02d}"
    weekly_goal = state.get("weekly_goal")
    if (
        not isinstance(weekly_goal, dict)
        or weekly_goal.get("week") != current_week
        or type(weekly_goal.get("completed")) is not int
        or weekly_goal["completed"] < 0
    ):
        weekly_goal = {
            "week": current_week,
            "completed": 0,
            "reward_claimed": False,
        }
        state["weekly_goal"] = weekly_goal
        save_state(state)
    elif "reward_claimed" not in weekly_goal:
        already_complete = weekly_goal["completed"] >= WEEKLY_TASK_GOAL
        weekly_goal["reward_claimed"] = already_complete
        if already_complete:
            state["inventory"]["kolikko"] += WEEKLY_GOAL_REWARD
            save_state(state)
    return weekly_goal


def register_completed_task(state: dict) -> None:
    weekly_goal = ensure_weekly_goal(state)
    weekly_goal["completed"] += 1
    if (
        weekly_goal["completed"] >= WEEKLY_TASK_GOAL
        and not weekly_goal["reward_claimed"]
    ):
        state["inventory"]["kolikko"] += WEEKLY_GOAL_REWARD
        weekly_goal["reward_claimed"] = True


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


def is_valid_pet_profile(pet: object) -> bool:
    return (
        isinstance(pet, dict)
        and pet.get("type") in PET_TYPES
        and isinstance(pet.get("name"), str)
        and bool(pet["name"].strip())
        and len(pet["name"]) <= 24
    )


def render_pet_setup(error: str = "") -> str:
    choices = []
    for pet_type, pet in PET_TYPES.items():
        if "image" in pet:
            visual = f'<img src="/pictures/{pet["image"]}" alt="">'
        choices.append(
            f"""
            <label class="pet-choice">
              <input type="radio" name="pet_type" value="{pet_type}" required>
              <span class="pet-choice-art">{visual}</span>
              <strong>{pet["label"]}</strong>
            </label>
            """
        )
    error_html = f'<p class="form-error" role="alert">{escape(error)}</p>' if error else ""
    return f"""
      <section class="pet-setup" aria-labelledby="pet-setup-title">
        <p class="eyebrow">TERVETULOA TASSUTEHTÄVIIN</p>
        <h1 id="pet-setup-title">Valitse lemmikkisi</h1>
        <p class="pet-setup-intro">Valitse kissa, sitruuna tai käpy ja anna lemmikillesi oma nimi.</p>
        <form method="post" class="pet-setup-form">
          <input type="hidden" name="action" value="save_pet">
          <div class="pet-choice-grid">{"".join(choices)}</div>
          <label for="pet-name">Lemmikin nimi</label>
          <input id="pet-name" name="pet_name" type="text" maxlength="24" autocomplete="off" required placeholder="Kirjoita nimi">
          {error_html}
          <button class="button button-primary" type="submit">Jatka sovellukseen</button>
        </form>
      </section>
    """


def render_pet_visual(pet: dict, size: float) -> str:
    pet_type = pet["type"]
    pet_name = escape(pet["name"])
    pet_kind = PET_TYPES[pet_type]
    return (
        f'<img class="pet-image" src="/pictures/{pet_kind["image"]}" '
        f'alt="{pet_name}, {pet_kind["label"].lower()}" '
        f'style="width: {size:.1f}px">'
    )


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


def render_recipe_card(state: dict, recipe_id: str, recipe: dict) -> str:
    discovered = recipe_id in state["discovered_recipes"]
    ingredients_available = all(
        state["inventory"][item] >= amount
        for item, amount in recipe["ingredients"].items()
    )
    ingredient_rows = "\n".join(
        f'<li><span>{amount} × {RESOURCE_LABELS[item]}</span>'
        f'<strong>{state["inventory"][item]} / {amount}</strong></li>'
        for item, amount in recipe["ingredients"].items()
    )
    recipe_class = "recipe-card discovered" if discovered else "recipe-card locked"
    output_name = recipe["name"] if discovered else "???"
    if ingredients_available:
        button_label = "Valmista" if discovered else "Kokeile reseptiä"
        action = f"""
          <form method="post" class="craft-form">
            <input type="hidden" name="action" value="craft">
            <input type="hidden" name="recipe_id" value="{recipe_id}">
            <button class="button button-craft" type="submit">{button_label}</button>
          </form>
        """
    else:
        action = '<button class="button button-craft" type="button" disabled>Ainekset puuttuvat</button>'
    treat_note = (
        f'<p class="recipe-note">Anna herkku lemmikillesi: +{TREAT_XP} XP.</p>'
        if recipe["output"] == "herkku" and discovered
        else ""
    )
    return f"""
      <article class="{recipe_class}">
        <div class="recipe-output">
          <span class="recipe-icon" aria-hidden="true">{recipe["icon"]}</span>
          <h4>{output_name}</h4>
        </div>
        <ul class="ingredient-list">{ingredient_rows}</ul>
        {treat_note}
        {action}
      </article>
    """


def render_crafting_section(state: dict) -> str:
    crafted_items = "\n".join(
        f'<li><span>{recipe["icon"]} {name}</span><strong>{state["crafted_items"][item]}</strong></li>'
        for item, name in CRAFTED_ITEMS.items()
        for recipe in RECIPES.values()
        if recipe["output"] == item
    )
    treat_count = state["crafted_items"]["herkku"]
    if treat_count:
        treat_action = f"""
          <form method="post" class="use-treat-form">
            <input type="hidden" name="action" value="use_treat">
            <button class="button button-craft" type="submit">Anna herkku lemmikille (+{TREAT_XP} XP)</button>
          </form>
        """
    else:
        treat_action = ""
    recipes = "\n".join(
        render_recipe_card(state, recipe_id, recipe)
        for recipe_id, recipe in RECIPES.items()
    )
    return f"""
      <section class="crafting-section" aria-labelledby="crafting-title">
        <div class="section-heading">
          <div>
            <p class="eyebrow">YHDISTÄ RESURSSEJA</p>
            <h2 id="crafting-title">Askartelu</h2>
          </div>
        </div>
        <div class="crafting-stock">
          <h3>Valmistetut palkinnot</h3>
          <ul class="crafted-list">{crafted_items}</ul>
          {treat_action}
        </div>
        <h3 class="recipe-book-title">Reseptikirja</h3>
        <p class="recipe-book-hint">Tuntemattomat palkinnot näkyvät siluetteina. Kokeile reseptiä, kun ainekset riittävät.</p>
        <div class="recipe-grid">{recipes}</div>
      </section>
    """


def render_home_item(item_id: str) -> str:
    item = HOME_ITEMS[item_id]
    return f"""
      <article class="home-object">
        <span class="home-object-icon" aria-hidden="true">{item["icon"]}</span>
        <strong>{item["name"]}</strong>
        <form method="post">
          <input type="hidden" name="action" value="remove_from_home">
          <input type="hidden" name="item_id" value="{item_id}">
          <button class="button button-secondary" type="submit">Siirrä reppuun</button>
        </form>
      </article>
    """


def render_home_page(state: dict, error: str = "") -> bytes:
    pet = state.get("pet")
    if not is_valid_pet_profile(pet):
        return render_page(state, error)

    placed_items = "\n".join(
        render_home_item(item_id) for item_id in state["home_items"]
    )
    if not placed_items:
        placed_items = """
          <p class="home-empty">Koti odottaa vielä ensimmäisiä tavaroitaan.
          Askartele lemmikille sänky, pehmolelu tai kasvi, niin voit tuoda sen tänne.</p>
        """

    available_items = []
    for item_id, item in HOME_ITEMS.items():
        count = state["crafted_items"][item_id]
        if count:
            available_items.append(
                f"""
                  <li class="home-build-item">
                    <span><span aria-hidden="true">{item["icon"]}</span> {item["name"]}</span>
                    <strong>{count} repussa</strong>
                    <form method="post">
                      <input type="hidden" name="action" value="add_to_home">
                      <input type="hidden" name="item_id" value="{item_id}">
                      <button class="button button-primary" type="submit">Lisää kotiin</button>
                    </form>
                  </li>
                """
            )
    if not available_items:
        available_items_html = (
            '<p class="home-build-empty">Askarteluvarastossasi ei ole vielä '
            'sisustusesineitä. Valmista sänky, pehmolelu tai kasvi tehtäväsivulla.</p>'
        )
    else:
        available_items_html = f'<ul class="home-build-list">{"".join(available_items)}</ul>'

    template = HOME_TEMPLATE_FILE.read_text(encoding="utf-8")
    page = (
        template.replace("{{PET_NAME}}", escape(pet["name"]))
        .replace("{{PET_VISUAL}}", render_pet_visual(pet, 120))
        .replace("{{PLACED_ITEMS}}", placed_items)
        .replace("{{AVAILABLE_ITEMS}}", available_items_html)
        .replace("{{ERROR}}", f'<p class="form-error" role="alert">{escape(error)}</p>' if error else "")
    )
    return page.encode("utf-8")


def render_page(
    state: dict,
    error: str = "",
    reward_package: tuple[str, int] | None = None,
) -> bytes:
    template = TEMPLATE_FILE.read_text(encoding="utf-8")
    pet = state.get("pet")
    has_pet = is_valid_pet_profile(pet)
    if has_pet:
        pet_name = pet["name"]
        pet_visual = render_pet_visual(pet, 96 * (1 + 0.03 * (state["xp"] // 30)))
        daily_surprise = ensure_daily_surprise(state)
        weekly_goal = ensure_weekly_goal(state)
        completed_this_week = weekly_goal["completed"]
        weekly_progress = min(
            completed_this_week / WEEKLY_TASK_GOAL * 100,
            100,
        )
        if completed_this_week >= WEEKLY_TASK_GOAL:
            weekly_message = (
                f"Tavoite saavutettu — hienoa! "
                f"{WEEKLY_GOAL_REWARD} rahaa on lisätty reppuusi. "
                "Voit jatkaa tai levätä, kuten sinulle sopii."
            )
        else:
            weekly_message = "Yksi tehtävä kerrallaan riittää. Vapaapäivä ei nollaa edistymistä."
        weekly_goal_html = f"""
          <section class="weekly-goal-card" aria-labelledby="weekly-goal-title">
            <div class="section-heading">
              <div>
                <p class="eyebrow">VIIKKOTAVOITE</p>
                <h2 id="weekly-goal-title">Viikon tavoite</h2>
              </div>
            </div>
            <p class="weekly-goal-description">Tee vähintään {WEEKLY_TASK_GOAL} tehtävää viikon aikana. Palkinto: {WEEKLY_GOAL_REWARD} rahaa.</p>
            <div class="progress-label">
              <span>Valmiit tehtävät tällä viikolla</span>
              <span>{completed_this_week} / {WEEKLY_TASK_GOAL}</span>
            </div>
            <div class="progress-track weekly-progress-track" role="progressbar" aria-label="Viikon tehtävätavoite" aria-valuenow="{min(completed_this_week, WEEKLY_TASK_GOAL)}" aria-valuemin="0" aria-valuemax="{WEEKLY_TASK_GOAL}">
              <span style="width: {weekly_progress:.1f}%"></span>
            </div>
            <p class="weekly-goal-message">{weekly_message}</p>
          </section>
        """
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
    else:
        pet_name = ""
        pet_visual = ""
        daily_surprise_html = ""
        weekly_goal_html = ""

    tasks = "\n".join(render_task(task) for task in state["tasks"])
    if not tasks:
        tasks = '<li class="empty-state">Lista on tyhjä. Lisää ensimmäinen tehtäväsi!</li>'

    level = state["xp"] // 100 + 1
    progress = state["xp"] % 100
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
    pet_setup = render_pet_setup(error) if not has_pet else ""
    crafting_html = render_crafting_section(state)

    page = (
        template.replace("{{TASKS}}", tasks)
        .replace("{{PET_SETUP}}", pet_setup)
        .replace("{{DASHBOARD_HIDDEN}}", "" if has_pet else "hidden")
        .replace(
            "{{REWARD_PACKAGE}}",
            render_surprise_package(reward_package) if has_pet else "",
        )
        .replace("{{DAILY_SURPRISE}}", daily_surprise_html)
        .replace("{{WEEKLY_GOAL}}", weekly_goal_html)
        .replace("{{INVENTORY}}", inventory)
        .replace("{{CRAFTING}}", crafting_html)
        .replace("{{PRESET_OPTIONS}}", preset_options)
        .replace("{{DIFFICULTY_OPTIONS}}", difficulty_options)
        .replace("{{ERROR}}", error_html)
        .replace("{{LEVEL}}", str(level))
        .replace("{{XP}}", str(state["xp"]))
        .replace("{{PROGRESS}}", str(progress))
        .replace("{{PET_VISUAL}}", pet_visual)
    )
    page = page.replace("{{PET_NAME}}", escape(pet_name))
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

        if parsed_url.path not in ("/", "/home"):
            self.send_error(404)
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
            if parsed_url.path == "/home":
                if not is_valid_pet_profile(state.get("pet")):
                    self.send_response(303)
                    self.send_header("Location", "/")
                    self.end_headers()
                    return
                body = render_home_page(state, error)
            else:
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
            redirect_path = (
                "/home"
                if action in ("add_to_home", "remove_from_home")
                else "/"
            )
            if action == "reset":
                save_state(new_state())
                self.redirect()
                return

            state = load_state()
            if action == "save_pet":
                pet_type = form.get("pet_type", [""])[0]
                pet_name = form.get("pet_name", [""])[0].strip()
                if pet_type not in PET_TYPES:
                    raise ValueError("Valitse lemmikiksi kissa, sitruuna tai käpy.")
                if not pet_name or len(pet_name) > 24:
                    raise ValueError("Kirjoita lemmikille nimi (1–24 merkkiä).")
                if is_valid_pet_profile(state.get("pet")):
                    raise ValueError("Lemmikki on jo valittu.")
                state["pet"] = {"type": pet_type, "name": pet_name}
            elif action == "craft":
                recipe_id = form.get("recipe_id", [""])[0]
                recipe = RECIPES.get(recipe_id)
                if recipe is None:
                    raise ValueError("Reseptiä ei löytynyt.")
                if any(
                    state["inventory"][item] < amount
                    for item, amount in recipe["ingredients"].items()
                ):
                    raise ValueError("Reseptiin ei ole riittävästi aineksia.")
                for item, amount in recipe["ingredients"].items():
                    state["inventory"][item] -= amount
                state["crafted_items"][recipe["output"]] += 1
                if recipe_id not in state["discovered_recipes"]:
                    state["discovered_recipes"].append(recipe_id)
            elif action == "use_treat":
                if state["crafted_items"]["herkku"] < 1:
                    raise ValueError("Inventaarioissa ei ole herkkua käytettäväksi.")
                state["crafted_items"]["herkku"] -= 1
                state["xp"] += TREAT_XP
            elif action == "add_to_home":
                item_id = form.get("item_id", [""])[0]
                if item_id not in HOME_ITEMS:
                    raise ValueError("Tätä esinettä ei voi lisätä lemmikin kotiin.")
                if state["crafted_items"][item_id] < 1:
                    raise ValueError("Askarteluvarastossa ei ole tätä esinettä.")
                state["crafted_items"][item_id] -= 1
                state["home_items"].append(item_id)
                redirect_path = "/home"
            elif action == "remove_from_home":
                item_id = form.get("item_id", [""])[0]
                if item_id not in HOME_ITEMS or item_id not in state["home_items"]:
                    raise ValueError("Esinettä ei löytynyt lemmikin kodista.")
                state["home_items"].remove(item_id)
                state["crafted_items"][item_id] += 1
                redirect_path = "/home"
            elif action == "claim_daily_surprise":
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
                register_completed_task(state)
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
                    register_completed_task(state)
                    state["tasks"].remove(task)
            else:
                raise ValueError("Tuntematon toiminto.")
            save_state(state)
            self.redirect(reward_package=reward_package, path=redirect_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self.redirect(str(exc), path=redirect_path)

    def redirect(
        self,
        error: str = "",
        reward_package: tuple[str, int, str] | None = None,
        path: str = "/",
    ) -> None:
        if error:
            location = path + "?" + urlencode({"error": error})
        elif reward_package is not None:
            location = path + "?" + urlencode(
                {
                    "package": reward_package[0],
                    "amount": reward_package[1],
                    "art": reward_package[2],
                }
            )
        else:
            location = path
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
