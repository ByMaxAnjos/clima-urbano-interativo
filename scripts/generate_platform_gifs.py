from pathlib import Path
import re
import shutil
import time

from PIL import Image, ImageDraw
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright


BASE_URL = "http://localhost:8502"
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "assets" / "gifs"
FRAME_DIR = OUT_DIR / "_frames"

SECTIONS = [
    ("Início", "inicio"),
    ("Explorar", "explorar"),
    ("Investigar", "investigar"),
    ("Visualizar", "visualizar"),
    ("Simular", "simular"),
    ("Clima de Bairro", "clima-de-bairro"),
]


def sanitize_page(page):
    page.add_style_tag(
        content="""
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        #MainMenu,
        footer {
          display: none !important;
        }
        .stApp {
          background: #f8fafc;
        }
        """
    )


def menu_frame(page):
    for frame in page.frames:
        if "streamlit_option_menu.option_menu" in frame.url:
            return frame
    raise RuntimeError("Menu da plataforma nao encontrado.")


def wait_for_section(page, label):
    expected = {
        "Início": "Plataforma Interativa de Clima Urbano",
        "Explorar": "Módulo Explorar",
        "Investigar": "Módulo Investigar",
        "Visualizar": "Módulo Visualizar",
        "Simular": "Módulo Simular",
        "Clima de Bairro": "Clima de Bairro",
    }[label]
    page.get_by_text(expected).first.wait_for(timeout=25000)
    page.wait_for_load_state("networkidle", timeout=30000)
    page.wait_for_timeout(900)
    page.evaluate("""() => {
        const scroller = document.querySelector('section.stMain');
        if (scroller) scroller.scrollTo({top: 0, behavior: 'instant'});
    }""")


def click_section(page, label):
    frame = menu_frame(page)
    frame.get_by_text(label, exact=True).click()
    wait_for_section(page, label)


def prepare_explorar(page):
    try:
        if page.get_by_text("Explore por classe").count() > 0:
            return
        city = page.get_by_placeholder(re.compile("Sao Paulo|São Paulo|Juiz", re.I)).first
        city.fill("São Paulo, Brazil")
        page.get_by_text(re.compile("Gerar Mapa LCZ")).first.click()
        page.get_by_text("Explore por classe").wait_for(timeout=120000)
        page.wait_for_timeout(2500)
    except PlaywrightTimeoutError:
        print("Aviso: o mapa LCZ nao terminou a tempo; o GIF de Explorar usara o estado disponivel.")


def prepare_simular(page):
    try:
        buttons = page.get_by_text(re.compile("Executar|Simular", re.I))
        if buttons.count() > 0:
            buttons.first.click(timeout=3000)
            page.wait_for_timeout(1500)
    except Exception:
        pass


def scroll_positions(page):
    metrics = page.evaluate("""() => {
        const scroller = document.querySelector('section.stMain') || document.documentElement;
        return {height: scroller.scrollHeight, viewport: scroller.clientHeight};
    }""")
    height = metrics["height"]
    viewport = metrics["viewport"]
    if height <= viewport:
        return [0]
    max_scroll = max(0, height - viewport)
    steps = min(8, max(4, round(height / viewport) + 1))
    return [round(max_scroll * i / (steps - 1)) for i in range(steps)]


def capture_frames(page, slug):
    section_dir = FRAME_DIR / slug
    if section_dir.exists():
        shutil.rmtree(section_dir)
    section_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    page.evaluate("""() => {
        const scroller = document.querySelector('section.stMain') || document.documentElement;
        scroller.scrollTo({top: 0, behavior: 'instant'});
    }""")
    page.wait_for_timeout(450)
    for index, y in enumerate(scroll_positions(page)):
        page.evaluate("""(y) => {
            const scroller = document.querySelector('section.stMain') || document.documentElement;
            scroller.scrollTo({top: y, behavior: 'instant'});
        }""", y)
        page.wait_for_timeout(650)
        path = section_dir / f"{index:02d}.png"
        page.screenshot(path=str(path), full_page=False)
        frames.append(path)
    return frames


def gif_from_frames(frame_paths, out_path, title):
    images = []
    for frame_path in frame_paths:
        img = Image.open(frame_path).convert("RGB")
        img.thumbnail((1100, 820), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (img.width, img.height + 34), "#f8fafc")
        canvas.paste(img, (0, 34))
        draw = ImageDraw.Draw(canvas)
        draw.rectangle((0, 0, canvas.width, 34), fill="#0f766e")
        draw.text((14, 9), title, fill="#ffffff")
        images.append(canvas.convert("P", palette=Image.Palette.ADAPTIVE, colors=128))

    images[0].save(
        out_path,
        save_all=True,
        append_images=images[1:],
        duration=950,
        loop=0,
        optimize=True,
        disposal=2,
    )


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FRAME_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 820}, device_scale_factor=1)
        page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(1500)
        sanitize_page(page)

        generated = []
        for label, slug in SECTIONS:
            click_section(page, label)
            if label == "Explorar":
                prepare_explorar(page)
            if label == "Simular":
                prepare_simular(page)
            frames = capture_frames(page, slug)
            out_path = OUT_DIR / f"{slug}.gif"
            gif_from_frames(frames, out_path, label)
            generated.append(out_path)
            print(f"GIF criado: {out_path}")

        browser.close()

    print("\nArquivos gerados:")
    for path in generated:
        print(path)


if __name__ == "__main__":
    started = time.time()
    main()
    print(f"Concluido em {time.time() - started:.1f}s")
