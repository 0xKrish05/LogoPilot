"""Clipster campaign submission via Playwright.

Per-automation flow: launch a temporary headless Chromium session, load the
automation's cookies, open the submission URL, click "Submit Content", fill
the uploaded reel URL into the modal, submit, wait for confirmation, and tear
the browser down. Sessions never outlive a single submission.
"""

import re

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


class ClipsterCookiesExpired(RuntimeError):
    """The session cookies no longer authenticate — user must re-upload."""


class ClipsterSubmissionError(RuntimeError):
    """Transient/page failure — safe to retry."""


_LOGIN_URL_HINTS = ("login", "signin", "sign-in", "sign_in", "auth")


def submit_reel(
    cookies: list[dict],
    submission_url: str,
    reel_url: str,
    proxy_url: str | None = None,
) -> None:
    with sync_playwright() as p:
        launch_kwargs: dict = {"headless": True, "args": ["--no-sandbox"]}
        if proxy_url:
            launch_kwargs["proxy"] = {"server": proxy_url}
        browser = p.chromium.launch(**launch_kwargs)
        try:
            context = browser.new_context()
            context.add_cookies(cookies)
            page = context.new_page()

            page.goto(submission_url, wait_until="domcontentloaded", timeout=60_000)
            try:
                page.wait_for_load_state("networkidle", timeout=20_000)
            except PlaywrightTimeout:
                pass  # long-polling pages never go idle; proceed anyway

            if any(hint in page.url.lower() for hint in _LOGIN_URL_HINTS):
                raise ClipsterCookiesExpired(
                    "Clipster redirected to the login page — cookies have expired."
                )

            submit_button = page.locator(
                "button:has-text('Submit Content'), a:has-text('Submit Content'), "
                "[role='button']:has-text('Submit Content')"
            ).first
            try:
                submit_button.wait_for(state="visible", timeout=20_000)
            except PlaywrightTimeout:
                if page.locator("input[type='password']").count() > 0:
                    raise ClipsterCookiesExpired(
                        "Clipster is showing a login form — cookies have expired."
                    )
                raise ClipsterSubmissionError(
                    "Couldn't find the 'Submit Content' button on the submission page."
                )
            submit_button.click()

            url_field = page.locator(
                "[role='dialog'] input, dialog input, [class*='modal' i] input, "
                "input[type='url'], input[placeholder*='url' i], input[placeholder*='link' i], "
                "[role='dialog'] textarea"
            ).first
            try:
                url_field.wait_for(state="visible", timeout=15_000)
            except PlaywrightTimeout:
                raise ClipsterSubmissionError("Submission dialog did not open.")
            url_field.fill(reel_url)

            confirm_button = page.locator(
                "[role='dialog'] button:has-text('Submit'), dialog button:has-text('Submit'), "
                "[class*='modal' i] button:has-text('Submit'), "
                "[role='dialog'] button[type='submit'], [class*='modal' i] button[type='submit']"
            ).first
            try:
                confirm_button.wait_for(state="visible", timeout=10_000)
            except PlaywrightTimeout:
                raise ClipsterSubmissionError("Couldn't find the submit button in the dialog.")
            confirm_button.click()

            try:
                page.wait_for_selector(
                    "text=/success|submitted|thank you|received/i", timeout=20_000
                )
            except PlaywrightTimeout:
                # Some flows just close the modal on success — treat a closed
                # dialog with no visible error as success.
                error_banner = page.locator("text=/error|failed|invalid/i").first
                if error_banner.count() > 0 and error_banner.is_visible():
                    raise ClipsterSubmissionError(
                        f"Clipster reported an error: {error_banner.inner_text()[:200]}"
                    )
                if url_field.is_visible():
                    raise ClipsterSubmissionError(
                        "No success confirmation appeared after submitting."
                    )
        finally:
            browser.close()


def parse_cookie_header(raw_cookies_txt: str) -> list[dict]:
    """Compat wrapper kept for callers that import from this module."""
    from app.services.cookies import parse_netscape_cookies

    return parse_netscape_cookies(raw_cookies_txt)


def sanitize_cookies(cookies: list[dict]) -> list[dict]:
    """Playwright rejects cookies with empty domains or bad fields."""
    cleaned = []
    for c in cookies:
        if not c.get("name") or not c.get("domain"):
            continue
        if not re.match(r"^\.?[\w.-]+$", c["domain"]):
            continue
        cleaned.append(c)
    return cleaned
