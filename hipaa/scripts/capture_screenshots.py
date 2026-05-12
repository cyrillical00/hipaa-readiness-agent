"""Capture portfolio screenshots for the HIPAA Readiness Agent README.

Output is written to ``hipaa/docs/screenshots/`` relative to this file, so it
works for anyone who clones the repo without hard-coded Windows paths.

Prereqs:
    pip install playwright
    playwright install chromium

Run:
    # In one shell, start the app:
    cd hipaa && streamlit run app.py

    # In another shell, run the capture (Meridian persona, 5 PNGs):
    python hipaa/scripts/capture_screenshots.py

The login flow assumes local auth mode with the demo email
``demo@hipaa.example`` present in ``local_allowed_emails`` in
``.streamlit/secrets.toml``.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

# Resolve to hipaa/docs/screenshots regardless of where the script is invoked.
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

BASE = "http://localhost:8501"
EMAIL = "demo@hipaa.example"
VIEWPORT = {"width": 1440, "height": 1000}


def wait_streamlit_idle(page, timeout=15000):
    """Wait for Streamlit's running indicator to disappear."""
    try:
        page.wait_for_function(
            "() => !document.querySelector('[data-testid=\"stStatusWidget\"]') "
            "|| !document.querySelector('[data-testid=\"stStatusWidget\"]').textContent.toLowerCase().includes('running')",
            timeout=timeout,
        )
    except Exception:
        pass
    page.wait_for_timeout(800)


def login(page):
    page.goto(BASE, wait_until="domcontentloaded")
    wait_streamlit_idle(page)
    # Look for the local login dropdown.
    page.wait_for_selector("text=Select an allow listed email", timeout=15000)
    # Click the selectbox.
    sel = page.locator("[data-testid='stSelectbox']").first
    sel.click()
    page.wait_for_timeout(400)
    page.get_by_text(EMAIL, exact=True).first.click()
    wait_streamlit_idle(page)
    print("[login] complete")


def select_persona(page, persona_label):
    """Use the Demo persona dropdown in the sidebar."""
    page.wait_for_selector("text=Demo persona", timeout=10000)
    box = page.locator("[data-testid='stSidebar'] [data-testid='stSelectbox']").first
    box.click()
    page.wait_for_timeout(600)
    # Streamlit renders dropdown options inside [data-baseweb='popover'] as li[role=option].
    option = page.locator("li[role='option']").filter(has_text=persona_label).first
    option.click()
    wait_streamlit_idle(page, timeout=25000)
    page.wait_for_timeout(2000)
    print(f"[persona] selected {persona_label}")


def goto_page(page, page_label):
    """Click a sidebar nav link by its visible text."""
    # Streamlit multipage nav uses anchor tags in the sidebar.
    nav = page.locator("[data-testid='stSidebarNav']")
    nav.get_by_text(page_label, exact=False).first.click()
    wait_streamlit_idle(page, timeout=20000)
    page.wait_for_timeout(1500)
    print(f"[nav] {page_label}")


def shoot(page, name):
    path = OUT / name
    page.screenshot(path=str(path), full_page=True)
    sz = path.stat().st_size
    print(f"[shot] {name} ({sz} bytes)")
    return path


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport=VIEWPORT, device_scale_factor=1)
        page = context.new_page()

        login(page)

        # Pick Meridian persona.
        select_persona(page, "Meridian Health Tech")

        # Gap Assessment (Meridian).
        goto_page(page, "Gap Assessment")
        page.wait_for_timeout(2000)
        shoot(page, "gap_assessment_meridian.png")

        # Integrations + persona picker.
        goto_page(page, "Integrations")
        page.wait_for_timeout(1500)
        shoot(page, "integrations_persona_picker.png")

        # BAA Tracker (Meridian).
        goto_page(page, "BAA Tracker")
        page.wait_for_timeout(1500)
        shoot(page, "baa_tracker_meridian.png")

        # Roadmap (Meridian); do not click Generate, only screenshot the empty state.
        goto_page(page, "Remediation Roadmap")
        page.wait_for_timeout(1500)
        shoot(page, "roadmap_meridian.png")

        # History.
        goto_page(page, "History")
        page.wait_for_timeout(1500)
        shoot(page, "history.png")

        browser.close()


if __name__ == "__main__":
    main()
