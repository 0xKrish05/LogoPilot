"""Parses cookies.txt (Netscape format) exports for use with Playwright.

Users export their logged-in Clipster session cookies with a browser
extension such as "Get cookies.txt LOCALLY" and upload the resulting file.
"""


def parse_netscape_cookies(text: str) -> list[dict]:
    """Returns a list of Playwright-compatible cookie dicts.

    Netscape cookie file lines are tab-separated:
    domain, include_subdomains, path, secure, expires, name, value
    """
    cookies = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split("\t")
        if len(parts) < 7:
            continue

        domain, _include_subdomains, path, secure, expires, name, value = parts[:7]
        cookie = {
            "name": name,
            "value": value,
            "domain": domain,
            "path": path or "/",
            "secure": secure.strip().upper() == "TRUE",
        }
        try:
            expires_int = int(expires)
            if expires_int > 0:
                cookie["expires"] = expires_int
        except ValueError:
            pass

        cookies.append(cookie)

    return cookies
