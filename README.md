# Flask Screenshot Service

A simple Flask-based web service that takes screenshots of webpages. This service uses Playwright to capture screenshots from a starting URL and its subsequent links.

## Features

- Accepts a starting URL and captures a screenshot of the page.
- Extracts links from the starting page and takes screenshots of up to a specified number of linked pages.
- Saves the screenshots to a local directory.
- Stores metadata (file paths) of the screenshots in a SQL Server database.
- Exposes an API for creating screenshots and retrieving them by run ID.

## Requirements

- Python 3.9+
- Docker
- Docker Compose (optional but recommended)

## Installation

### Clone the Repository

```bash
git clone https://github.com/your-username/screenshot-service.git
cd screenshot-service
```
### Set Up the Virtual Environment

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   
2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt

### Database Setup

  #### Ensure you have a running SQL Server instance to store screenshot metadata. Update the DATABASE_URL in the app.py file with your connection details.


# API Endpoints

## `GET /isalive`
Check if the server is running.

### Response
```json
{
  "status": "Server is running"
}
```

## `POST /screenshots`
Crawl the starting URL and capture screenshots of the page and its links.

### Request Body
```json
{
  "start_url": "https://example.com",
  "number_of_links_to_follow": 5
}
```
### Response
```json
{
  "message": "Screenshots captured",
  "run_id": "unique-run-id"
}
```
## `GET /screenshots/<run_id>`
Retrieve the screenshots captured during a specific run.

### Response
```json
{
  "run_id": "unique-run-id",
  "file_paths": [
    "screenshots/run-id_start.png",
    "screenshots/run-id_link_1.png",
    "screenshots/run-id_link_2.png"
  ]
}
```

