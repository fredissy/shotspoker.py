from playwright.sync_api import sync_playwright
import time

def verify_fr_js():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(locale="fr")
        page = context.new_page()

        try:
            page.goto("http://localhost:5000")
            page.wait_for_load_state("networkidle")

            # Check H3 text (HTML translation)
            text = page.locator("h3").inner_text()
            print(f"H3 text: {text}")

            if "Shots Poker (FR)" not in text:
                print("Verification Failed: HTML text not translated.")
            else:
                print("Verification Passed: HTML text translated.")

            # Check JS translations object
            translations = page.evaluate("window.translations")
            if translations and translations.get("Room not found") == "Salle introuvable":
                print("Verification Passed: JS translations loaded correctly.")
            else:
                print(f"Verification Failed: JS translations missing or incorrect. Got: {translations.get('Room not found') if translations else 'None'}")

            page.screenshot(path="verification/fr_verification_full.png")

        except Exception as e:
            print(f"Error: {e}")

        finally:
            browser.close()

if __name__ == "__main__":
    verify_fr_js()
