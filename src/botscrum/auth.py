from __future__ import annotations

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

import httpx

from .config import AUTH_FILE

PROXY_PORT = 8765
_HOP_BY_HOP = frozenset(
    ["connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
     "te", "trailers", "transfer-encoding", "upgrade"]
)


def _host(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def save_cookies(url: str, cookies: dict[str, str]) -> None:
    data: dict = {}
    if AUTH_FILE.exists():
        data = json.loads(AUTH_FILE.read_text())
    data[_host(url)] = cookies
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    AUTH_FILE.write_text(json.dumps(data, indent=2))


def load_cookies(url: str) -> dict[str, str]:
    if not AUTH_FILE.exists():
        return {}
    data = json.loads(AUTH_FILE.read_text())
    return data.get(_host(url), {})


def _make_handler(target: str, proxy_base: str, captured: dict, done: threading.Event):
    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def _proxy(self, method: str, body: bytes | None = None) -> None:
            target_url = f"{target}{self.path}"
            headers = {
                k: v for k, v in self.headers.items()
                if k.lower() not in _HOP_BY_HOP | {"host"}
            }
            headers["Host"] = urlparse(target).netloc

            if captured:
                headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in captured.items())

            try:
                resp = httpx.request(
                    method, target_url, headers=headers,
                    content=body, follow_redirects=False, timeout=30,
                )
            except Exception as exc:
                self.send_error(502, str(exc))
                return

            # Capture Set-Cookie headers
            for raw in resp.headers.get_list("set-cookie"):
                name_val = raw.split(";")[0].strip()
                if "=" in name_val:
                    name, val = name_val.split("=", 1)
                    captured[name.strip()] = val.strip()

            # Signal completion: JSESSIONID set and we left the login page
            if "JSESSIONID" in captured and "seraph.rememberme.cookie" in captured:
                done.set()

            # Build response headers
            out_headers: list[tuple[str, str]] = []
            for k, v in resp.headers.items():
                kl = k.lower()
                if kl in _HOP_BY_HOP | {"content-length", "content-encoding"}:
                    continue
                if kl == "set-cookie":
                    v = v.replace("; Secure", "").replace(";Secure", "")
                    v = v.replace("; secure", "").replace(";secure", "")
                    v = v.replace("; SameSite=None", "").replace("; SameSite=Strict", "").replace("; SameSite=Lax", "")
                elif kl == "location":
                    v = v.replace(target, proxy_base)
                out_headers.append((k, v))

            # Rewrite body for HTML/JS
            content_type = resp.headers.get("content-type", "")
            body_bytes = resp.content
            if any(t in content_type for t in ("html", "javascript", "json")):
                body_bytes = resp.content.replace(target.encode(), proxy_base.encode())

            self.send_response(resp.status_code)
            for k, v in out_headers:
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(body_bytes)))
            self.end_headers()
            if method != "HEAD":
                self.wfile.write(body_bytes)

        def do_GET(self):
            self._proxy("GET")

        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b""
            self._proxy("POST", body)

        def do_HEAD(self):
            self._proxy("HEAD")

    return _Handler


def browser_login(url: str, port: int = PROXY_PORT) -> int:
    """Start a local reverse proxy, open the login page in the browser, capture cookies."""
    target = _host(url)
    proxy_base = f"http://localhost:{port}"
    captured: dict[str, str] = {}
    done = threading.Event()

    handler = _make_handler(target, proxy_base, captured, done)
    httpd = HTTPServer(("0.0.0.0", port), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    login_path = "/login.action" if "confluence" in target else "/login.jsp"
    login_url = f"{proxy_base}{login_path}"

    print(f"\n  Open this URL in your browser to log in:\n\n    {login_url}\n")
    try:
        webbrowser.open(login_url)
    except Exception:
        pass

    print("  Waiting for login to complete (timeout: 5 min)...")
    done.wait(timeout=300)
    httpd.shutdown()

    if not captured:
        raise RuntimeError("No cookies captured — login may not have completed.")

    save_cookies(url, captured)
    return len(captured)
