import os
import uuid
from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)

# Configure MS SQL database connection
DATABASE_URL = "mssql+pyodbc://app_user:YourStrongPassword!@(localdb)\\MSSQLLocalDB/screenshots_db?driver=ODBC+Driver+17+for+SQL+Server"

engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Screenshot database model
class ScreenshotRun(Base):
    __tablename__ = 'screenshot_runs'
    id = Column(String(36), primary_key=True)
    file_paths = Column(Text, nullable=False)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db_session = Session()

# Directory to save screenshots
SCREENSHOT_DIR = "screenshots"
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

# Route: Server health check
@app.route('/isalive', methods=['GET'])
def is_alive():
    return jsonify({"status": "Server is running"}), 200

# Function to accept Google cookies
def accept_google_cookies(page):
    try:
        # Wait for the cookie banner and accept it
        accept_button = page.wait_for_selector('text="Приемане на всички"', timeout=5000)
        accept_button.click()
        print("Cookies accepted!")
    except:
        print("No cookie banner found or already accepted.")


# Function to take a screenshot
def take_screenshot(url, screenshot_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        page.screenshot(path=screenshot_path)

    # Function to extract links from a webpage
def extract_links(url, max_links):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = [a['href'] for a in soup.find_all('a', href=True)]
        absolute_links = [link if link.startswith('http') else requests.compat.urljoin(url, link) for link in links]
        return absolute_links[:max_links]
    except Exception as e:
        print(f"Error extracting links: {e}")
        return []

# Route: Crawl and take screenshots
@app.route('/screenshots', methods=['POST'])
def create_screenshots():
    data = request.get_json()
    start_url = data.get('start_url')
    num_links = data.get('number_of_links_to_follow')

    if not start_url or not num_links:
        return jsonify({"error": "Missing 'start_url' or 'number_of_links_to_follow' parameter"}), 400

    try:
        num_links = int(num_links)
    except ValueError:
        return jsonify({"error": "'number_of_links_to_follow' must be an integer"}), 400

    # Generate a unique ID for this run
    run_id = str(uuid.uuid4())
    screenshot_paths = []

    with sync_playwright() as p:
        # Launch the browser once at the start
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Go to the starting page and accept cookies once
        page.goto(start_url)
        accept_google_cookies(page)  # Accept cookies before navigating

        # Take a screenshot of the start URL
        start_screenshot_path = os.path.join(SCREENSHOT_DIR, f"{run_id}_start.png")
        page.screenshot(path=start_screenshot_path)
        screenshot_paths.append(start_screenshot_path)

        # Extract links from the start URL
        links = extract_links(start_url, num_links)

        # Loop through the first 2 links and click them
        for idx, link in enumerate(links[:num_links]):  # Iterate based on num_links
            # Ensure that the link is clickable and navigate to it
            try:
                # Navigate to the link (simulating clicking)
                page.goto(link)
                accept_google_cookies(page)  # Accept cookies before navigating
                # Wait for the page to load completely
                page.wait_for_load_state('networkidle')

                # Take a screenshot of the new page
                screenshot_path = os.path.join(SCREENSHOT_DIR, f"{run_id}_link_{idx + 1}.png")
                page.screenshot(path=screenshot_path)
                screenshot_paths.append(screenshot_path)
            except Exception as e:
                print(f"Error clicking link {link}: {e}")

        browser.close()

    # Save metadata to the database
    screenshot_run = ScreenshotRun(id=run_id, file_paths=";".join(screenshot_paths))
    db_session.add(screenshot_run)
    db_session.commit()

    return jsonify({
        "message": "Screenshots captured",
        "run_id": run_id
    }), 200

# Route: Retrieve screenshots by run ID
@app.route('/screenshots/<run_id>', methods=['GET'])
def get_screenshots(run_id):
    screenshot_run = db_session.query(ScreenshotRun).filter_by(id=run_id).first()

    if not screenshot_run:
        return jsonify({"error": "Run ID not found"}), 404

    return jsonify({
        "run_id": screenshot_run.id,
        "file_paths": screenshot_run.file_paths.split(";")
    }), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
