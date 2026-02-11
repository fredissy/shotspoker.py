from playwright.sync_api import sync_playwright
import time

def verify_fr():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(locale="fr")
        page = context.new_page()

        try:
            page.goto("http://localhost:5000")
            page.wait_for_selector("h3")

            text = page.locator("h3").inner_text()
            print(f"H3 text: {text}")

            page.screenshot(path="verification/fr_verification.png")

            if "Shots Poker (FR)" in text:
                print("Verification Passed: Found French text.")
            else:
                print("Verification Failed: French text not found.")

        except Exception as e:
            print(f"Error: {e}")

        finally:
            browser.close()

if __name__ == "__main__":
    verify_fr()
