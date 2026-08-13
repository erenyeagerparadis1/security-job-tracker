import os
import re
import time
import json
import urllib.parse
from datetime import datetime
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
    "Singapore",
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

CACHE_FILE = "teamblind_cache.json"
COMPANY_CACHE = {}


def log_audit(category: str, message: str):
    """Prints timestamped audit logs."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{category:<14}] {message}")


def load_cache():
    """Loads persistent cache from disk."""
    global COMPANY_CACHE
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                COMPANY_CACHE = json.load(f)
            log_audit("CACHE LOAD", f"Loaded {len(COMPANY_CACHE)} cached company entries.")
        except Exception as e:
            log_audit("CACHE WARN", f"Failed reading cache file: {e}")


def save_cache():
    """Saves cache back to disk."""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(COMPANY_CACHE, f, indent=2, ensure_ascii=False)
        log_audit("CACHE SAVE", f"Saved {len(COMPANY_CACHE)} entries to {CACHE_FILE}")
    except Exception as e:
        log_audit("CACHE ERROR", f"Failed saving cache file: {e}")


def is_security_role(title: str) -> bool:
    """Strictly validates if job title contains security keywords."""
    clean_title = title.lower()
    security_keywords = ["security", "secops", "cybersecurity", "infosec", "securityanalyst"]
    return any(kw in clean_title for kw in security_keywords)


def get_teamblind_score(company_name: str) -> str:
    """Fetches rating from TeamBlind search page."""
    clean_company = company_name.strip()
    search_url = f"https://www.teamblind.com/search/{urllib.parse.quote(clean_company)}"

    try:
        response = requests.get(search_url, headers=HEADERS, timeout=(4, 6))
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            company_link = soup.find("a", href=re.compile(r"^/company/"))
            if company_link:
                parent = company_link.find_parent("div")
                if parent:
                    rating_container = parent.find("div", class_=lambda c: c and "flex" in c and "text-sm" in c)
                    if rating_container:
                        score_text = rating_container.get_text(strip=True)
                        match = re.search(r"(\d\.\d)", score_text)
                        if match:
                            return f"★ {match.group(1)}"

            score_match = re.search(r'href="/company/[^"]*"[^>]*>.*?<div[^>]*class="[^"]*flex[^"]*text-sm[^"]*"[^>]*>.*?([1-5]\.\d)', response.text, re.DOTALL | re.IGNORECASE)
            if score_match:
                return f"★ {score_match.group(1)}"
    except Exception:
        pass

    return "N/A"


def get_levels_fyi_details(company_name: str) -> dict:
    """Fetches stock quote summary, security role salaries, rating, and benefits from Levels.fyi public data."""
    clean_company = company_name.strip().lower()
    slug = re.sub(r'[^a-z0-9]+', '-', clean_company).strip('-')
    
    url = f"https://www.levels.fyi/companies/{slug}/salaries/software-engineer"

    try:
        response = requests.get(url, headers=HEADERS, timeout=(4, 6))
        if response.status_code == 200:
            html = response.text
            soup = BeautifulSoup(html, "html.parser")

            ticker_match = re.search(r'\(NASDAQ:\s*([A-Z]+)\)|\(NYSE:\s*([A-Z]+)\)', html)
            stock_symbol = ticker_match.group(1) or ticker_match.group(2) if ticker_match else None
            stock_summary = f"${stock_symbol}" if stock_symbol else "Private / N/A"

            rating_match = re.search(r'([1-5]\.\d)\s*out of 5', html, re.I) or re.search(r'Rating:\s*([1-5]\.\d)', html, re.I)
            rating = f"★ {rating_match.group(1)}" if rating_match else "N/A"

            salary_match = re.search(r'Median Total Compensation\s*\$([\d,]+)', html, re.I) or re.search(r'\$([\d,]+)\s*/\s*yr', html)
            sec_salary = f"${salary_match.group(1)}/yr (Median)" if salary_match else "Data Not Disclosed"

            benefits = []
            for item in soup.find_all(["span", "div"], class_=re.compile(r"benefit|perk", re.I)):
                text = item.get_text(strip=True)
                if text and len(text) < 40 and text not in benefits:
                    benefits.append(text)

            return {
                "stock_summary": stock_summary,
                "rating": rating,
                "security_salary": sec_salary,
                "benefits": ", ".join(benefits[:4]) if benefits else "Standard Tech Benefits (Health, 401k/PF, Equity)"
            }
    except Exception:
        pass

    return {
        "stock_summary": "N/A",
        "rating": "N/A",
        "security_salary": "Data Not Disclosed",
        "benefits": "Standard Industry Perks"
    }


def get_company_intelligence(company_name: str) -> dict:
    """Uses cached intelligence or performs fresh HTTP queries for TeamBlind & Levels.fyi."""
    norm_key = company_name.strip().lower()

    # Case 1: Valid dictionary in cache (CACHE HIT)
    if norm_key in COMPANY_CACHE and isinstance(COMPANY_CACHE[norm_key], dict):
        log_audit("CACHE HIT", f"Using cached scores for '{company_name}'")
        return COMPANY_CACHE[norm_key]

    # Case 2: Legacy string format in cache (upgrade entry)
    if norm_key in COMPANY_CACHE and isinstance(COMPANY_CACHE[norm_key], str):
        log_audit("CACHE UPGRADE", f"Upgrading legacy string cache for '{company_name}' with fresh Levels.fyi data")
        blind_score = COMPANY_CACHE[norm_key]
        levels_data = get_levels_fyi_details(company_name)
    # Case 3: Completely missing from cache (FRESH HIT)
    else:
        log_audit("FRESH FETCH", f"No cache entry. Querying TeamBlind & Levels.fyi for '{company_name}'")
        blind_score = get_teamblind_score(company_name)
        levels_data = get_levels_fyi_details(company_name)

    intel = {
        "blind_score": blind_score,
        "levels_stock": levels_data["stock_summary"],
        "levels_rating": levels_data["rating"],
        "levels_salary": levels_data["security_salary"],
        "levels_benefits": levels_data["benefits"]
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
                        "levels_stock": intel["levels_stock"],
                        "levels_rating": intel["levels_rating"],
                        "levels_salary": intel["levels_salary"],
                        "levels_benefits": intel["levels_benefits"]
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


def generate_html_report(job_listings: list, discarded_listings: list, location_counts: dict, output_filename: str = "index.html"):
    """Generates tabbed HTML dashboard with Levels.fyi data drawer and discarded jobs tab."""
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
            .subtitle { color: #94a3b8; font-size: 0.9rem; margin-bottom: 1.5rem; }
            
            .tab-header { display: flex; gap: 1rem; border-bottom: 2px solid var(--border); margin-bottom: 1.5rem; }
            .tab-btn { background: none; border: none; color: #94a3b8; font-size: 1rem; font-weight: 600; padding: 0.75rem 1.25rem; cursor: pointer; border-bottom: 3px solid transparent; }
            .tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }

            .metrics-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 0.75rem; margin-bottom: 1.5rem; }
            .metric-card { background: var(--card-bg); border: 1px solid var(--border); padding: 0.75rem 1rem; border-radius: 6px; }
            .metric-card .loc-name { font-size: 0.8rem; color: #94a3b8; }
            .metric-card .loc-count { font-size: 1.25rem; font-weight: bold; color: var(--accent); }

            table { width: 100%; border-collapse: collapse; background: var(--card-bg); border-radius: 8px; overflow: hidden; margin-top: 0.5rem; }
            th, td { padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid var(--border); }
            th { background-color: #0284c7; color: white; font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; }
            
            .clickable-row { cursor: pointer; transition: background 0.2s; }
            .clickable-row:hover { background-color: #334155; }
            
            .detail-row { display: none; background-color: #0284c715; }
            .detail-container { padding: 1rem; font-size: 0.85rem; border-left: 4px solid var(--accent); }
            .detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }

            .col-filter { width: 100%; padding: 0.4rem; margin-top: 0.4rem; border-radius: 4px; border: 1px solid var(--border); background: #0f172a; color: var(--text); font-size: 0.8rem; box-sizing: border-box; }
            .badge { background: #0369a1; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; }
            .badge-danger { background: #9f1239; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; }
            .score { color: #facc15; font-weight: bold; }
            a { color: var(--accent); text-decoration: none; font-weight: 500; }
        </style>
    </head>
    <body>
        <h1>Security Engineering Job Dashboard</h1>
        <div class="subtitle">Generated on {{ timestamp }}</div>

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
                        <th>Job Title <input type="text" class="col-filter" onkeyup="filterTable('jobsTable', 0)" placeholder="Filter..."></th>
                        <th>Company <input type="text" class="col-filter" onkeyup="filterTable('jobsTable', 1)" placeholder="Filter..."></th>
                        <th>Blind Score</th>
                        <th>Stock & Rating (Levels.fyi)</th>
                        <th>Location <input type="text" class="col-filter" onkeyup="filterTable('jobsTable', 3)" placeholder="Filter..."></th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    {% for job in jobs %}
                    <tr class="clickable-row" onclick="toggleDrawer('drawer-{{ loop.index }}')">
                        <td><strong>{{ job.title }}</strong> <br><small style="color:#94a3b8">▼ Click row for Levels.fyi perks</small></td>
                        <td>{{ job.company }}</td>
                        <td><span class="score">{{ job.blind_score }}</span></td>
                        <td><span class="badge">{{ job.levels_stock }}</span> <span class="score">{{ job.levels_rating }}</span></td>
                        <td><span class="badge">{{ job.location }}</span></td>
                        <td><a href="{{ job.link }}" target="_blank" onclick="event.stopPropagation()">View Job &rarr;</a></td>
                    </tr>
                    <tr id="drawer-{{ loop.index }}" class="detail-row">
                        <td colspan="6">
                            <div class="detail-container">
                                <strong>Levels.fyi Detailed Intelligence for {{ job.company }}:</strong>
                                <div class="detail-grid" style="margin-top:0.5rem">
                                    <div><strong>Security Salary Range:</strong> {{ job.levels_salary }}</div>
                                    <div><strong>Stock / Ticker:</strong> {{ job.levels_stock }}</div>
                                    <div><strong>Top Benefits:</strong> {{ job.levels_benefits }}</div>
                                </div>
                            </div>
                        </td>
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
                        <th>Filtered Job Title <input type="text" class="col-filter" onkeyup="filterTable('discardedTable', 0)" placeholder="Filter..."></th>
                        <th>Company <input type="text" class="col-filter" onkeyup="filterTable('discardedTable', 1)" placeholder="Filter..."></th>
                        <th>Location</th>
                        <th>Exclusion Reason</th>
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
            function switchTab(tabId, btn) {
                document.getElementById('activeTab').style.display = tabId === 'activeTab' ? 'block' : 'none';
                document.getElementById('discardedTab').style.display = tabId === 'discardedTab' ? 'block' : 'none';
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            }

            function toggleDrawer(drawerId) {
                const drawer = document.getElementById(drawerId);
                drawer.style.display = drawer.style.display === 'table-row' ? 'none' : 'table-row';
            }

            function filterTable(tableId, colIndex) {
                const table = document.getElementById(tableId);
                const input = table.querySelectorAll('thead input')[colIndex];
                const filter = input.value.toLowerCase();
                const rows = table.querySelectorAll('tbody tr:not(.detail-row)');

                rows.forEach(row => {
                    const cell = row.cells[colIndex];
                    if (cell) {
                        const text = cell.innerText.toLowerCase();
                        row.style.display = text.includes(filter) ? '' : 'none';
                    }
                });
            }
        </script>
    </body>
    </html>
    """

    template = Template(template_str)
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    rendered_html = template.render(
        jobs=job_listings,
        total_jobs=len(job_listings),
        discarded=discarded_listings,
        total_discarded=len(discarded_listings),
        location_counts=location_counts,
        timestamp=timestamp_str
    )

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    log_audit("HTML REPORT", f"Updated dashboard: {output_filename}")


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
