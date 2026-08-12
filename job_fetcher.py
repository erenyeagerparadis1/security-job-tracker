import os
import re
import time
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# In-memory global cache for TeamBlind ratings
TEAMBLIND_CACHE = {}


def log_audit(category: str, message: str):
    """Prints timestamped audit logs."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{category:<14}] {message}")


def is_security_role(title: str) -> bool:
    """Validates that the job title contains security keywords."""
    clean_title = title.lower()
    security_keywords = ["security", "secops", "cybersecurity", "infosec", "securityanalyst"]
    return any(kw in clean_title for kw in security_keywords)


def get_teamblind_score(company_name: str) -> str:
    """Fetches company rating from TeamBlind search using the DOM structure from DevTools snapshot."""
    clean_company = company_name.strip()
    norm_key = clean_company.lower()

    if norm_key in TEAMBLIND_CACHE:
        log_audit("BLIND CACHE", f"Hit for '{clean_company}' -> {TEAMBLIND_CACHE[norm_key]}")
        return TEAMBLIND_CACHE[norm_key]

    log_audit("BLIND FETCH", f"Querying TeamBlind search for: '{clean_company}'")
    search_url = f"https://www.teamblind.com/search/{urllib.parse.quote(clean_company)}"

    try:
        response = requests.get(search_url, headers=HEADERS, timeout=(15, 15))
        if response.status_code != 200:
            log_audit("BLIND BLOCK", f"HTTP {response.status_code} (Cloudflare block) for '{clean_company}'")
            TEAMBLIND_CACHE[norm_key] = "N/A"
            return "N/A"
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            # 1. Find company link
            company_link = soup.find("a", href=re.compile(r"^/company/"))
            if company_link:
                parent = company_link.find_parent("div")
                if parent:
                    # 2. Target <div class="flex text-sm">
                    rating_container = parent.find("div", class_=lambda c: c and "flex" in c and "text-sm" in c)
                    if rating_container:
                        score_text = rating_container.get_text(strip=True)
                        match = re.search(r"(\d\.\d)", score_text)
                        if match:
                            score = f"★ {match.group(1)}"
                            TEAMBLIND_CACHE[norm_key] = score
                            log_audit("BLIND SUCCESS", f"Retrieved '{clean_company}': {score}")
                            return score

            # Fallback regex search
            score_match = re.search(r'href="/company/[^"]*"[^>]*>.*?<div[^>]*class="[^"]*flex[^"]*text-sm[^"]*"[^>]*>.*?([1-5]\.\d)', response.text, re.DOTALL | re.IGNORECASE)
            if score_match:
                score = f"★ {score_match.group(1)}"
                TEAMBLIND_CACHE[norm_key] = score
                log_audit("BLIND SUCCESS", f"Retrieved '{clean_company}': {score}")
                return score

    except requests.exceptions.Timeout:
        log_audit("BLIND WARN", f"Timeout fetching TeamBlind score for '{clean_company}'")
    except Exception as e:
        log_audit("BLIND ERROR", f"Failed fetching '{clean_company}': {e}")

    TEAMBLIND_CACHE[norm_key] = "N/A"
    return "N/A"


def fetch_linkedin_jobs(title: str, location: str, max_results_per_query: int = 50) -> list:
    """Scrapes LinkedIn Guest API with security filtering, pagination, and non-blocking timeouts."""
    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    jobs = []
    start = 0
    page_size = 25

    log_audit("SEARCH START", f"Title: '{title}' | Location: '{location}'")

    while len(jobs) < max_results_per_query:
        params = {
            "keywords": title,
            "location": location,
            "start": start,
            "f_TPR": "r86400"  # Last 24 hours
        }

        try:
            response = requests.get(base_url, headers=HEADERS, params=params, timeout=(5, 8))
            
            if response.status_code == 429:
                log_audit("LINKEDIN WARN", f"Rate limited (HTTP 429) at start={start}. Skipping.")
                break
            elif response.status_code != 200:
                log_audit("LINKEDIN WARN", f"HTTP {response.status_code} at start={start}. Terminating query.")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            cards = soup.find_all("li")

            if not cards:
                log_audit("PAGINATION", f"End of results reached at start={start}.")
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

                    # Filter out non-security job titles
                    if not is_security_role(job_title):
                        log_audit("FILTER EXCLUDE", f"Skipped non-security role: '{job_title}'")
                        continue

                    company_name = company_elem.text.strip()
                    job_link = link_elem["href"].split("?")[0]

                    job_data = {
                        "title": job_title,
                        "company": company_name,
                        "location": location_elem.text.strip() if location_elem else location,
                        "link": job_link,
                        "posted": date_elem.text.strip() if date_elem else "Today",
                        "blind_score": get_teamblind_score(company_name)
                    }
                    jobs.append(job_data)
                    parsed_in_page += 1

                    if len(jobs) >= max_results_per_query:
                        break

            log_audit("PAGE FETCHED", f"Offset {start}: parsed {parsed_in_page} security jobs (Total: {len(jobs)})")

            if parsed_in_page == 0:
                break

            start += page_size
            time.sleep(1.2)

        except requests.exceptions.Timeout:
            log_audit("TIMEOUT", f"LinkedIn request timed out at start={start} for '{location}'.")
            break
        except Exception as e:
            log_audit("ERROR", f"Error during pagination for '{location}': {e}")
            break

    log_audit("SEARCH COMPLETE", f"Found {len(jobs)} security jobs for '{title}' in '{location}'")
    return jobs


def generate_html_report(job_listings: list, location_counts: dict, output_filename: str = "index.html"):
    """Generates dynamic HTML dashboard with column search inputs and real-time count updates."""
    template_str = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Daily Security Engineering Jobs</title>
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
            h2 { font-size: 1.1rem; color: #cbd5e1; margin-top: 1.5rem; }
            .subtitle { color: #94a3b8; font-size: 0.9rem; margin-bottom: 1.5rem; }
            
            .counter-badge {
                display: inline-block;
                background: #0284c7;
                color: white;
                padding: 0.4rem 0.8rem;
                border-radius: 6px;
                font-weight: bold;
                font-size: 0.95rem;
                margin-bottom: 1rem;
            }

            .metrics-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 0.75rem; margin-bottom: 2rem; }
            .metric-card { background: var(--card-bg); border: 1px solid var(--border); padding: 0.75rem 1rem; border-radius: 6px; }
            .metric-card .loc-name { font-size: 0.8rem; color: #94a3b8; }
            .metric-card .loc-count { font-size: 1.25rem; font-weight: bold; color: var(--accent); }

            table { width: 100%; border-collapse: collapse; background: var(--card-bg); border-radius: 8px; overflow: hidden; margin-top: 0.5rem; }
            th, td { padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid var(--border); }
            th { background-color: #0284c7; color: white; font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.05em; }
            tr:hover { background-color: #334155; }
            
            .col-filter {
                width: 100%;
                padding: 0.4rem 0.5rem;
                margin-top: 0.4rem;
                border-radius: 4px;
                border: 1px solid var(--border);
                background: #0f172a;
                color: var(--text);
                font-size: 0.8rem;
                box-sizing: border-box;
            }
            .col-filter::placeholder { color: #64748b; }

            .badge { background: #0369a1; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; }
            .score { color: #facc15; font-weight: bold; }
            a { color: var(--accent); text-decoration: none; font-weight: 500; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <h1>Security Engineering Job Dashboard</h1>
        <div class="subtitle">Generated on {{ timestamp }}</div>

        <div class="counter-badge">
            Showing <span id="visibleCount">{{ total_jobs }}</span> of {{ total_jobs }} total security jobs
        </div>

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
                    <th>
                        Job Title
                        <input type="text" id="filterTitle" class="col-filter" onkeyup="filterTable()" placeholder="Filter title...">
                    </th>
                    <th>
                        Company
                        <input type="text" id="filterCompany" class="col-filter" onkeyup="filterTable()" placeholder="Filter company...">
                    </th>
                    <th>
                        TeamBlind Score
                        <input type="text" id="filterBlind" class="col-filter" onkeyup="filterTable()" placeholder="Filter score...">
                    </th>
                    <th>
                        Location
                        <input type="text" id="filterLocation" class="col-filter" onkeyup="filterTable()" placeholder="Filter location...">
                    </th>
                    <th>
                        Posted
                        <input type="text" id="filterPosted" class="col-filter" onkeyup="filterTable()" placeholder="Filter date...">
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
                    <td>{{ job.posted }}</td>
                    <td><a href="{{ job.link }}" target="_blank">View Listing &rarr;</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <script>
            function filterTable() {
                const titleQuery = document.getElementById('filterTitle').value.toLowerCase();
                const companyQuery = document.getElementById('filterCompany').value.toLowerCase();
                const blindQuery = document.getElementById('filterBlind').value.toLowerCase();
                const locationQuery = document.getElementById('filterLocation').value.toLowerCase();
                const postedQuery = document.getElementById('filterPosted').value.toLowerCase();

                const rows = document.querySelectorAll('#jobsTable tbody tr');
                let visibleCount = 0;

                rows.forEach(row => {
                    const titleText = row.cells[0].innerText.toLowerCase();
                    const companyText = row.cells[1].innerText.toLowerCase();
                    const blindText = row.cells[2].innerText.toLowerCase();
                    const locationText = row.cells[3].innerText.toLowerCase();
                    const postedText = row.cells[4].innerText.toLowerCase();

                    const matches = titleText.includes(titleQuery) &&
                                    companyText.includes(companyQuery) &&
                                    blindText.includes(blindQuery) &&
                                    locationText.includes(locationQuery) &&
                                    postedText.includes(postedQuery);

                    if (matches) {
                        row.style.display = '';
                        visibleCount++;
                    } else {
                        row.style.display = 'none';
                    }
                });

                document.getElementById('visibleCount').innerText = visibleCount;
            }
        </script>
    </body>
    </html>
    """

    template = Template(template_str)
    today_str = datetime.now().strftime("%Y-%m-%d")
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    rendered_html = template.render(
        jobs=job_listings,
        total_jobs=len(job_listings),
        location_counts=location_counts,
        timestamp=timestamp_str
    )

    # Write primary dashboard
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    log_audit("HTML REPORT", f"Updated primary dashboard: {output_filename}")

    # Write archive copy
    archive_dir = "archive"
    os.makedirs(archive_dir, exist_ok=True)
    archive_filename = os.path.join(archive_dir, f"index_{today_str}.html")

    with open(archive_filename, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    log_audit("HTML REPORT", f"Saved date-stamped copy: {archive_filename}")


def main():
    log_audit("SCRIPT INIT", "Starting Daily Security Job Collector...")
    all_jobs = []
    location_counts = {loc: 0 for loc in TARGET_LOCATIONS}

    for location in TARGET_LOCATIONS:
        log_audit("LOCATION RUN", f"Processing location: {location}")
        location_jobs_count = 0

        for title in TARGET_TITLES:
            jobs = fetch_linkedin_jobs(title, location, max_results_per_query=50)
            all_jobs.extend(jobs)
            location_jobs_count += len(jobs)

        location_counts[location] = location_jobs_count
        log_audit("LOCATION DONE", f"{location} finished -> Total security jobs: {location_jobs_count}")

    # Deduplicate entries by job link URL
    unique_jobs_map = {job["link"]: job for job in all_jobs}
    unique_jobs = list(unique_jobs_map.values())

    log_audit("SUMMARY", "========================================")
    log_audit("SUMMARY", f"Total Valid Security Jobs Collected: {len(all_jobs)}")
    log_audit("SUMMARY", f"Unique Security Jobs (Deduplicated): {len(unique_jobs)}")
    log_audit("SUMMARY", f"Unique Companies Cached on TeamBlind: {len(TEAMBLIND_CACHE)}")
    log_audit("SUMMARY", "========================================")

    generate_html_report(unique_jobs, location_counts)


if __name__ == "__main__":
    main()
