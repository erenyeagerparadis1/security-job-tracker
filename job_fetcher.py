import os

def generate_html_report(job_listings: list, location_counts: dict, output_filename: str = "index.html"):
    """Generates dynamic HTML dashboard and creates a date-stamped archive copy."""
    template_str = """
    <!-- ... (your existing Jinja template stays unchanged) ... -->
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

    # 1. Write current/latest file
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    log_audit("HTML REPORT", f"Updated primary dashboard: {output_filename}")

    # 2. Save a date-stamped copy in an archive directory
    archive_dir = "archive"
    os.makedirs(archive_dir, exist_ok=True)
    archive_filename = os.path.join(archive_dir, f"index_{today_str}.html")

    with open(archive_filename, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    log_audit("HTML REPORT", f"Saved historical copy to: {archive_filename}")