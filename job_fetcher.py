import os
import re
import time
import json
import urllib.parse
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from jinja2 import Template

# Configured Target Titles
TARGET_TITLES = [
    "Security Engineer",
    "Application Security Engineer"
]

# Configured Locations (US excluded)
TARGET_LOCATIONS = [
    "Bengaluru, India",
    "Hyderabad, India",
    "Chennai, India",
    "Coimbatore, India",
    "Singapore",
    "Malaysia",
    "Canada",
    "United Kingdom",
    "Australia",
    "Netherlands",
    "Ireland",
    "Japan",
    "Germany",
    "United Arab Emirates",
    "New Zealand"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(BASE_DIR, "teamblind_cache.json")
FAILED_FILE = os.path.join(BASE_DIR, "teamblind_failed.json")
OUTPUT_FILE = os.path.join(BASE_DIR, "index.html")
ARCHIVE_DIR = os.path.join(BASE_DIR, "archive")
COMPANY_CACHE = {}
FAILED_ORGS = {}


def log_audit(category: str, message: str):
    """Prints timestamped audit logs."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{category:<14}] {message}")


def load_cache():
    """Loads persistent cache and failed-org list from disk."""
    global COMPANY_CACHE, FAILED_ORGS
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                COMPANY_CACHE = json.load(f)
            log_audit("CACHE LOAD", f"Loaded {len(COMPANY_CACHE)} cached company entries.")
        except Exception as e:
            log_audit("CACHE WARN", f"Failed reading cache file: {e}")
    _load_failed_orgs()


def save_cache():
    """Saves cache and failed-org list, dropping leftover Levels.fyi keys."""
    try:
        slim = {}
        for key, value in COMPANY_CACHE.items():
            if isinstance(value, dict):
                slim[key] = {k: v for k, v in value.items() if not str(k).startswith("levels_")}
            else:
                slim[key] = value
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(slim, f, indent=2, ensure_ascii=False)
        log_audit("CACHE SAVE", f"Saved {len(slim)} entries to {CACHE_FILE}")
    except Exception as e:
        log_audit("CACHE ERROR", f"Failed saving cache file: {e}")
    _save_failed_orgs()


def _load_failed_orgs():
    """Loads teamblind_failed.json, or seeds it from cached N/A scores."""
    global FAILED_ORGS
    if os.path.exists(FAILED_FILE):
        try:
            with open(FAILED_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            FAILED_ORGS = data if isinstance(data, dict) else {}
            log_audit("FAILED LOAD", f"Loaded {len(FAILED_ORGS)} failed TeamBlind orgs.")
            return
        except Exception as e:
            log_audit("FAILED WARN", f"Failed reading {FAILED_FILE}: {e}")
            FAILED_ORGS = {}
            return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    seeded = {}
    for key, value in COMPANY_CACHE.items():
        score = value if isinstance(value, str) else (value or {}).get("blind_score")
        if _is_good_blind_score(score):
            continue
        fetched_at = value.get("fetched_at") if isinstance(value, dict) else None
        seeded[key] = {
            "company": key,
            "last_failed_at": fetched_at or now,
            "fail_count": 1,
        }
    FAILED_ORGS = seeded
    if seeded:
        log_audit("FAILED SEED", f"Seeded {len(seeded)} failed orgs from cache N/A entries.")


def _save_failed_orgs():
    """Writes the failed TeamBlind org list next to the script."""
    try:
        with open(FAILED_FILE, "w", encoding="utf-8") as f:
            json.dump(FAILED_ORGS, f, indent=2, ensure_ascii=False, sort_keys=True)
        log_audit("FAILED SAVE", f"Saved {len(FAILED_ORGS)} failed orgs to {FAILED_FILE}")
    except Exception as e:
        log_audit("FAILED ERROR", f"Failed saving {FAILED_FILE}: {e}")


def _mark_blind_failure(company_name: str, norm_key: str):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    prev = FAILED_ORGS.get(norm_key) or {}
    FAILED_ORGS[norm_key] = {
        "company": company_name.strip(),
        "last_failed_at": now,
        "fail_count": int(prev.get("fail_count") or 0) + 1,
    }


def _clear_blind_failure(norm_key: str):
    FAILED_ORGS.pop(norm_key, None)


def is_security_role(title: str) -> bool:
    """Strictly validates if job title contains security keywords."""
    clean_title = title.lower()
    security_keywords = ["security", "secops", "cybersecurity", "infosec", "securityanalyst"]
    return any(kw in clean_title for kw in security_keywords)


def _is_good_blind_score(score) -> bool:
    """True when a cached/fetched value contains a 1.x-5.x rating."""
    if not isinstance(score, str):
        return False
    return bool(re.search(r"[1-5]\.\d", score))


def _extract_jsonld_rating(html: str):
    """Reads EmployerAggregateRating.ratingValue from public company-page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text() or ""
        try:
            data = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get("@type") == "EmployerAggregateRating":
                value = item.get("ratingValue")
                if value is not None:
                    return f"★ {value}"
    match = re.search(
        r'"@type"\s*:\s*"EmployerAggregateRating".{0,160}"ratingValue"\s*:\s*"?([1-5](?:\.\d)?)"?',
        html,
        re.S,
    )
    if match:
        return f"★ {match.group(1)}"
    return None


def _extract_star_overall(html: str, company_name: str):
    """Matches companyName to starOverall in TeamBlind search HTML/RSC payload."""
    pairs = re.findall(
        r'companyName\\?"\s*:\s*\\?"([^"\\]+)\\?".{0,500}?starOverall\\?"\s*:\s*\\?"([1-5]\.\d)\\?"',
        html,
        re.I | re.S,
    )
    if not pairs:
        pairs = re.findall(
            r'"companyName"\s*:\s*"([^"]+)".{0,500}?"starOverall"\s*:\s*"([1-5]\.\d)"',
            html,
            re.I | re.S,
        )
    target = company_name.strip().lower()
    for name, score in pairs:
        if name.lower() == target:
            return f"★ {score}"
    for name, score in pairs:
        n, t = name.lower(), target
        if n in t or t in n:
            return f"★ {score}"
    return None


def _extract_url_alias(html: str, company_name: str):
    """Finds the TeamBlind company slug that matches a LinkedIn employer name."""
    pairs = re.findall(
        r'companyName\\?"\s*:\s*\\?"([^"\\]+)\\?".{0,240}?urlAlias\\?"\s*:\s*\\?"([^"\\]+)\\?"',
        html,
        re.I | re.S,
    )
    target = company_name.strip().lower()
    for name, alias in pairs:
        n = name.lower()
        if n == target or n in target or target in n:
            return alias
    return None


def _fetch_company_page_rating(slug: str):
    """GET /company/{slug} and parse the public JSON-LD rating."""
    if not slug:
        return None
    url = f"https://www.teamblind.com/company/{urllib.parse.quote(slug)}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=(6, 10))
        if response.status_code == 200:
            return _extract_jsonld_rating(response.text)
    except Exception:
        return None
    return None


def get_teamblind_score(company_name: str) -> str:
    """Fetches rating from TeamBlind search HTML, then the public company page."""
    clean_company = company_name.strip()
    if not clean_company:
        return "N/A"

    search_url = f"https://www.teamblind.com/search/{urllib.parse.quote(clean_company)}"
    try:
        response = requests.get(search_url, headers=HEADERS, timeout=(6, 10))
        if response.status_code == 200:
            html = response.text
            score = _extract_star_overall(html, clean_company)
            if score:
                return score
            alias = _extract_url_alias(html, clean_company)
            score = _fetch_company_page_rating(alias) if alias else None
            if score:
                return score
    except Exception:
        pass

    first = re.split(r"[\s,/|&]+", clean_company, maxsplit=1)[0]
    if first:
        score = _fetch_company_page_rating(first)
        if score:
            return score
    return "N/A"


def get_company_intelligence(company_name: str) -> dict:
    """Uses a stored Blind star rating, or retries when the cache is N/A/missing."""
    norm_key = company_name.strip().lower()
    cached = COMPANY_CACHE.get(norm_key)
    prev_score = None
    if isinstance(cached, str):
        prev_score = cached
    elif isinstance(cached, dict):
        prev_score = cached.get("blind_score")

    if _is_good_blind_score(prev_score):
        log_audit("CACHE HIT", f"Using cached Blind score for '{company_name}'")
        _clear_blind_failure(norm_key)
        return {"blind_score": prev_score}

    log_audit("FRESH FETCH", f"Querying TeamBlind for '{company_name}'")
    fresh_score = get_teamblind_score(company_name)
    if _is_good_blind_score(fresh_score):
        score = fresh_score
        _clear_blind_failure(norm_key)
    elif _is_good_blind_score(prev_score):
        score = prev_score
        log_audit("CACHE KEEP", f"Refresh failed; keeping last Blind score for '{company_name}'")
    else:
        score = "N/A"
        _mark_blind_failure(company_name, norm_key)
        log_audit("FAILED ORG", f"No TeamBlind score for '{company_name}'")

    intel = {
        "blind_score": score,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    COMPANY_CACHE[norm_key] = intel
    return intel


def fetch_linkedin_jobs(title: str, location: str, max_results_per_query: int = 50) -> tuple:
    """Scrapes LinkedIn, splitting listings into active security roles vs discarded roles."""
    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    valid_jobs = []
    discarded_jobs = []
    start = 0
    page_size = 25

    log_audit("SEARCH START", f"Title: '{title}' | Location: '{location}'")

    while (len(valid_jobs) + len(discarded_jobs)) < max_results_per_query:
        params = {
            "keywords": title,
            "location": location,
            "start": start,
            "f_TPR": "r86400"  # Last 24 hours
        }

        try:
            response = requests.get(base_url, headers=HEADERS, params=params, timeout=(5, 8))
            if response.status_code != 200:
                break

            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.find_all("li")
            if not cards:
                break

            parsed_in_page = 0
            for card in cards:
                title_elem = card.find("h3", class_=re.compile(r"base-search-card__title", re.I))
                company_elem = card.find("h4", class_=re.compile(r"base-search-card__subtitle", re.I))
                location_elem = card.find("span", class_=re.compile(r"job-search-card__location", re.I))
                link_elem = card.find("a", class_=re.compile(r"base-card__full-link", re.I))
                date_elem = card.find("time")

                if title_elem and company_elem and link_elem:
                    job_title = title_elem.text.strip()
                    company_name = company_elem.text.strip()
                    job_link = link_elem["href"].split("?")[0]
                    intel = get_company_intelligence(company_name)

                    job_data = {
                        "title": job_title,
                        "company": company_name,
                        "location": location_elem.text.strip() if location_elem else location,
                        "link": job_link,
                        "posted": date_elem.text.strip() if date_elem else "Today",
                        "blind_score": intel["blind_score"],
                    }

                    if is_security_role(job_title):
                        valid_jobs.append(job_data)
                    else:
                        job_data["reason"] = "Title missing 'security' keyword"
                        discarded_jobs.append(job_data)

                    parsed_in_page += 1

            if parsed_in_page == 0:
                break

            start += page_size
            time.sleep(1.0)

        except Exception as e:
            log_audit("ERROR", f"Error during pagination for '{location}': {e}")
            break

    return valid_jobs, discarded_jobs


def _list_archive_dates():
    """Returns dated archive snapshots as YYYY-MM-DD, newest first."""
    if not os.path.isdir(ARCHIVE_DIR):
        return []
    dates = []
    for name in os.listdir(ARCHIVE_DIR):
        match = re.fullmatch(r"index_(\d{4}-\d{2}-\d{2})\.html", name)
        if match:
            dates.append(match.group(1))
    return sorted(dates, reverse=True)


def generate_html_report(job_listings: list, discarded_listings: list, location_counts: dict, output_filename: str = None):
    """Generates tabbed HTML dashboard with TeamBlind scores and discarded jobs."""
    if not output_filename:
        output_filename = OUTPUT_FILE
    elif not os.path.isabs(output_filename):
        output_filename = os.path.join(BASE_DIR, output_filename)

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    archive_dates = _list_archive_dates()
    if today_str not in archive_dates:
        archive_dates = [today_str] + archive_dates

    template_str = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Daily Security Engineering Dashboard</title>
        <style>
            :root {
                --bg: #0f172a;
                --card-bg: #1e293b;
                --text: #f8fafc;
                --accent: #38bdf8;
                --border: #334155;
            }
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); padding: 2rem; margin: 0; }
            h1 { font-size: 1.75rem; margin-bottom: 0.25rem; color: var(--accent); }
            .subtitle { color: #94a3b8; font-size: 0.9rem; margin-bottom: 0.5rem; }
            
            .archive-row { color: #94a3b8; font-size: 0.8rem; margin-bottom: 1.5rem; display: flex; flex-wrap: wrap; gap: 0.45rem 0.75rem; align-items: center; }
            .archive-row a { color: var(--accent); }

            .tab-header { display: flex; gap: 1rem; border-bottom: 2px solid var(--border); margin-bottom: 1.5rem; }
            .tab-btn { background: none; border: none; color: #94a3b8; font-size: 1rem; font-weight: 600; padding: 0.75rem 1.25rem; cursor: pointer; border-bottom: 3px solid transparent; }
            .tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }

            .metrics-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 0.75rem; margin-bottom: 1.5rem; }
            .metric-card { background: var(--card-bg); border: 1px solid var(--border); padding: 0.75rem 1rem; border-radius: 6px; }
            .metric-card .loc-name { font-size: 0.8rem; color: #94a3b8; }
            .metric-card .loc-count { font-size: 1.25rem; font-weight: bold; color: var(--accent); }

            table { width: 100%; border-collapse: collapse; background: var(--card-bg); border-radius: 8px; overflow: visible; margin-top: 0.5rem; }
            th, td { padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid var(--border); vertical-align: top; }
            th { background-color: #0284c7; color: white; font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; position: relative; }

            .col-filter-box { margin-top: 0.45rem; font-weight: 400; text-transform: none; letter-spacing: 0; }
            .col-search { width: 100%; padding: 0.4rem; border-radius: 4px; border: 1px solid var(--border); background: #0f172a; color: var(--text); font-size: 0.8rem; box-sizing: border-box; }
            .ms-wrap { position: relative; margin-top: 0.3rem; }
            .ms-toggle { width: 100%; padding: 0.35rem 0.45rem; border-radius: 4px; border: 1px solid var(--border); background: #0f172a; color: #cbd5e1; font-size: 0.75rem; text-align: left; cursor: pointer; }
            .ms-panel { display: none; position: absolute; z-index: 30; left: 0; min-width: 100%; max-height: 220px; overflow: auto; background: #0f172a; border: 1px solid var(--border); border-radius: 4px; padding: 0.4rem; box-shadow: 0 8px 24px rgba(0,0,0,0.35); }
            .ms-wrap.open .ms-panel { display: block; }
            .ms-option { display: flex; gap: 0.4rem; align-items: flex-start; padding: 0.2rem 0; color: #e2e8f0; font-size: 0.75rem; cursor: pointer; }
            .ms-option input { margin-top: 0.15rem; }
            .badge { background: #0369a1; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; }
            .badge-danger { background: #9f1239; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; }
            .score { color: #facc15; font-weight: bold; }
            a { color: var(--accent); text-decoration: none; font-weight: 500; }
        </style>
    </head>
    <body>
        <h1>Security Engineering Job Dashboard</h1>
        <div class="subtitle">Generated on {{ timestamp }}</div>
        <div class="archive-row">
            <a href="{{ home_href }}">Latest</a>
            {% for day in archive_dates %}
            <a href="{{ archive_prefix }}index_{{ day }}.html">{{ day }}</a>
            {% endfor %}
        </div>

        <div class="tab-header">
            <button class="tab-btn active" onclick="switchTab('activeTab', this)">Active Security Roles ({{ total_jobs }})</button>
            <button class="tab-btn" onclick="switchTab('discardedTab', this)">Discarded Roles ({{ total_discarded }})</button>
        </div>

        <!-- TAB 1: ACTIVE JOBS -->
        <div id="activeTab">
            <h2>Location Breakdown</h2>
            <div class="metrics-grid">
                {% for loc, count in location_counts.items() %}
                <div class="metric-card">
                    <div class="loc-name">{{ loc }}</div>
                    <div class="loc-count">{{ count }}</div>
                </div>
                {% endfor %}
            </div>

            <table id="jobsTable">
                <thead>
                    <tr>
                        <th>Job Title
                            <div class="col-filter-box">
                                <input type="text" class="col-search" placeholder="Search..." oninput="filterTable('jobsTable')">
                                <div class="ms-wrap">
                                    <button type="button" class="ms-toggle" onclick="toggleMulti(this)">All values</button>
                                    <div class="ms-panel"></div>
                                </div>
                            </div>
                        </th>
                        <th>Company
                            <div class="col-filter-box">
                                <input type="text" class="col-search" placeholder="Search..." oninput="filterTable('jobsTable')">
                                <div class="ms-wrap">
                                    <button type="button" class="ms-toggle" onclick="toggleMulti(this)">All values</button>
                                    <div class="ms-panel"></div>
                                </div>
                            </div>
                        </th>
                        <th>Blind Score
                            <div class="col-filter-box">
                                <input type="text" class="col-search" placeholder="Search..." oninput="filterTable('jobsTable')">
                                <div class="ms-wrap">
                                    <button type="button" class="ms-toggle" onclick="toggleMulti(this)">All values</button>
                                    <div class="ms-panel"></div>
                                </div>
                            </div>
                        </th>
                        <th>Location
                            <div class="col-filter-box">
                                <input type="text" class="col-search" placeholder="Search..." oninput="filterTable('jobsTable')">
                                <div class="ms-wrap">
                                    <button type="button" class="ms-toggle" onclick="toggleMulti(this)">All values</button>
                                    <div class="ms-panel"></div>
                                </div>
                            </div>
                        </th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {% for job in jobs %}
                    <tr>
                        <td><strong>{{ job.title }}</strong></td>
                        <td>{{ job.company }}</td>
                        <td><span class="score">{{ job.blind_score }}</span></td>
                        <td><span class="badge">{{ job.location }}</span></td>
                        <td><a href="{{ job.link }}" target="_blank">View Job &rarr;</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- TAB 2: DISCARDED JOBS -->
        <div id="discardedTab" style="display: none;">
            <p style="color:#94a3b8; font-size:0.9rem">Roles excluded because title lacks 'security' (e.g. Solutions Architect, generic Software Engineer).</p>
            <table id="discardedTable">
                <thead>
                    <tr>
                        <th>Filtered Job Title
                            <div class="col-filter-box">
                                <input type="text" class="col-search" placeholder="Search..." oninput="filterTable('discardedTable')">
                                <div class="ms-wrap">
                                    <button type="button" class="ms-toggle" onclick="toggleMulti(this)">All values</button>
                                    <div class="ms-panel"></div>
                                </div>
                            </div>
                        </th>
                        <th>Company
                            <div class="col-filter-box">
                                <input type="text" class="col-search" placeholder="Search..." oninput="filterTable('discardedTable')">
                                <div class="ms-wrap">
                                    <button type="button" class="ms-toggle" onclick="toggleMulti(this)">All values</button>
                                    <div class="ms-panel"></div>
                                </div>
                            </div>
                        </th>
                        <th>Location
                            <div class="col-filter-box">
                                <input type="text" class="col-search" placeholder="Search..." oninput="filterTable('discardedTable')">
                                <div class="ms-wrap">
                                    <button type="button" class="ms-toggle" onclick="toggleMulti(this)">All values</button>
                                    <div class="ms-panel"></div>
                                </div>
                            </div>
                        </th>
                        <th>Exclusion Reason
                            <div class="col-filter-box">
                                <input type="text" class="col-search" placeholder="Search..." oninput="filterTable('discardedTable')">
                                <div class="ms-wrap">
                                    <button type="button" class="ms-toggle" onclick="toggleMulti(this)">All values</button>
                                    <div class="ms-panel"></div>
                                </div>
                            </div>
                        </th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {% for job in discarded %}
                    <tr>
                        <td><strong>{{ job.title }}</strong></td>
                        <td>{{ job.company }}</td>
                        <td><span class="badge">{{ job.location }}</span></td>
                        <td><span class="badge-danger">{{ job.reason }}</span></td>
                        <td><a href="{{ job.link }}" target="_blank">View Job &rarr;</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <script>
            function cellText(cell) {
                return (cell ? cell.innerText : '').replace(/\\s+/g, ' ').trim();
            }

            function switchTab(tabId, btn) {
                document.getElementById('activeTab').style.display = tabId === 'activeTab' ? 'block' : 'none';
                document.getElementById('discardedTab').style.display = tabId === 'discardedTab' ? 'block' : 'none';
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            }

            function toggleMulti(btn) {
                const wrap = btn.closest('.ms-wrap');
                document.querySelectorAll('.ms-wrap.open').forEach(w => {
                    if (w !== wrap) w.classList.remove('open');
                });
                wrap.classList.toggle('open');
            }

            function initFilters(tableId) {
                const table = document.getElementById(tableId);
                if (!table) return;
                const rows = Array.from(table.querySelectorAll('tbody tr'));
                table.querySelectorAll('thead th').forEach((th, col) => {
                    const box = th.querySelector('.col-filter-box');
                    if (!box) return;
                    const panel = box.querySelector('.ms-panel');
                    panel.innerHTML = '';
                    const values = Array.from(new Set(rows.map(row => cellText(row.cells[col])).filter(Boolean)))
                        .sort((a, b) => a.localeCompare(b));
                    values.forEach(value => {
                        const label = document.createElement('label');
                        label.className = 'ms-option';
                        const checkbox = document.createElement('input');
                        checkbox.type = 'checkbox';
                        checkbox.value = value;
                        checkbox.addEventListener('change', () => filterTable(tableId));
                        const span = document.createElement('span');
                        span.textContent = value;
                        label.appendChild(checkbox);
                        label.appendChild(span);
                        panel.appendChild(label);
                    });
                });
            }

            function filterTable(tableId) {
                const table = document.getElementById(tableId);
                if (!table) return;
                const specs = [];
                table.querySelectorAll('thead th').forEach((th, col) => {
                    const box = th.querySelector('.col-filter-box');
                    if (!box) return;
                    const query = (box.querySelector('.col-search').value || '').trim().toLowerCase();
                    const selected = Array.from(box.querySelectorAll('.ms-panel input:checked')).map(input => input.value);
                    const toggle = box.querySelector('.ms-toggle');
                    toggle.textContent = selected.length ? selected.length + ' selected' : 'All values';
                    specs.push({ col, query, selected });
                });
                table.querySelectorAll('tbody tr').forEach(row => {
                    const show = specs.every(spec => {
                        const text = cellText(row.cells[spec.col]);
                        if (spec.query && !text.toLowerCase().includes(spec.query)) return false;
                        if (spec.selected.length && !spec.selected.includes(text)) return false;
                        return true;
                    });
                    row.style.display = show ? '' : 'none';
                });
            }

            document.addEventListener('click', event => {
                if (!event.target.closest('.ms-wrap')) {
                    document.querySelectorAll('.ms-wrap.open').forEach(wrap => wrap.classList.remove('open'));
                }
            });

            initFilters('jobsTable');
            initFilters('discardedTable');
        </script>
    </body>
    </html>
    """

    template = Template(template_str)
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    render_kwargs = {
        "jobs": job_listings,
        "total_jobs": len(job_listings),
        "discarded": discarded_listings,
        "total_discarded": len(discarded_listings),
        "location_counts": location_counts,
        "timestamp": timestamp_str,
        "archive_dates": archive_dates,
    }

    rendered_html = template.render(
        home_href="index.html",
        archive_prefix="archive/",
        **render_kwargs
    )
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    log_audit("HTML REPORT", f"Updated dashboard: {output_filename}")

    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    archive_filename = os.path.join(ARCHIVE_DIR, f"index_{today_str}.html")
    archive_html = template.render(
        home_href="../index.html",
        archive_prefix="",
        **render_kwargs
    )
    with open(archive_filename, "w", encoding="utf-8") as f:
        f.write(archive_html)
    log_audit("HTML REPORT", f"Saved archive copy: {archive_filename}")


def main():
    load_cache()

    log_audit("SCRIPT INIT", "Starting Daily Security Job Collector...")
    all_valid_jobs = []
    all_discarded_jobs = []
    location_counts = {loc: 0 for loc in TARGET_LOCATIONS}

    for location in TARGET_LOCATIONS:
        log_audit("LOCATION RUN", f"Processing location: {location}")
        loc_valid_count = 0

        for title in TARGET_TITLES:
            valid, discarded = fetch_linkedin_jobs(title, location, max_results_per_query=50)
            all_valid_jobs.extend(valid)
            all_discarded_jobs.extend(discarded)
            loc_valid_count += len(valid)

        location_counts[location] = loc_valid_count

    # Deduplicate entries by job link URL
    unique_valid = list({job["link"]: job for job in all_valid_jobs}.values())
    unique_discarded = list({job["link"]: job for job in all_discarded_jobs}.values())

    generate_html_report(unique_valid, unique_discarded, location_counts)
    save_cache()


if __name__ == "__main__":
    main()
