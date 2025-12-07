# 🕸️ Universal Web Scraper

A powerful and modular web scraping tool that supports both **static** and **JavaScript-rendered** websites using **Playwright**.  

## Features

- **Static Scraping**: Fast extraction from static HTML pages
- **JS Rendering**: Automatic fallback to Playwright for JavaScript-heavy sites
- **Smart Section Detection**: Identifies page sections by semantic HTML and content structure
- **Click Flows**: Handles tabs and "Load more" buttons
- **Scroll/Pagination**: Supports infinite scroll and pagination to depth ≥ 3
- **Noise Filtering**: Removes cookie banners, modals, and other overlay elements
- **JSON Viewer**: Beautiful frontend to view and download scraped data

## Tech Stack

### Backend
- **Python 3.10+**
- **FastAPI** - Modern web framework
- **httpx** - HTTP client for static scraping
- **beautifulsoup4** - Fast HTML parser
- **Playwright** - Browser automation for JS rendering

### Frontend
- **React 19** with **Vite**
- **JavaScript**
- **Tailwind CSS**

## 🚀 How to Set Up & Run the Project

### Run this command in frontend directory 

```bash
#Build frontend
npm install
npm run build
```

This project includes a `run.sh` & `run.ps1` script for linux/macOS & Windows systems that includes:

1. Creates a virtual environment (if it doesn’t exist)  
2. Activates it  
3. Installs all dependencies using `requirements.txt`  
4. Runs Playwright setup (`playwright install`)  
5. Starts the web server on **http://localhost:8000**

---

## ▶️ Running on macOS / Linux

### Step 1 — Make the script executable

```bash
chmod +x run.sh
```
### Step 2 — Run the project

```bash
./run.sh
```

## ▶️ Running on Windows

```bash
./run.ps1
```

## ▶️ Manually setup Project
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Build frontend in frontend directory
npm install
npm run build

# Start server
uvicorn backend.main:app --reload --port 8000
```

## API Endpoints

### GET /healthz
Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

### POST /scrape
Scrape a URL and return structured JSON data.

```json
{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "result": {
    "url": "https://example.com",
    "scrapedAt": "2025-12-05T00:00:00Z",
    "meta": {
      "title": "Page Title",
      "description": "Page description",
      "language": "en",
      "canonical": "https://example.com",
      "strategy": "static"
    },
    "sections": [...],
    "interactions": {
      "clicks": [],
      "scrolls": 0,
      "pages": ["https://example.com"]
    },
    "errors": []
  }
}
```

## Testing URLs

The scraper has been tested with the following URLs:

### 1. Static Page
**URL:** https://en.wikipedia.org/wiki/Artificial_intelligence

Well-structured static HTML page with clear sections, headings, and semantic markup. Tests basic static scraping capabilities.

### 2. JS-Rendered Marketing Page
**URL:** https://vercel.com/

JavaScript-heavy marketing page with dynamic content loading. Tests the JS fallback strategy and ability to extract content after client-side rendering.

### 3. Pagination
**URL:** https://news.ycombinator.com/

Classic pagination example with "More" links. Tests the ability to follow pagination links and scrape multiple pages to the required depth of 3.


## Project Structure

```
.
├── backend/
│   ├── main.py            
│   └── scraper/
|       ├── static_fetch.py 
│       ├── playwright_scraper.py     
│       ├── utils.py 
|       └── parsers/ 
│           ├── images.py 
|           ├── links.py
|           ├── lists.py
|           ├── sections.py
│           └── utils.py 
|── frontend/
│     ├── src/
│     │   └── components/
|     │        ├── JsonBlock.jsx
│     │        ├── ScrapeForm.jsx  
│     │        ├── SectionsList.jsx  
│     │        └── SectionDetails.jsx
|     ├── api.js
│     ├── App.jsx
│     └── main.jsx
|       
├── run.sh                   
├── requirements.txt                   
├── README.md               
├── design_notes.md         
└── capabilities.json       
```

## Known Limitations

- Only HTTP(S) URLs are supported (file:// and other schemes are rejected)
- Scraping is limited to a single domain (same origin policy)
- Some sites may block automation (403/bot detection)
- Very large pages may take longer to process
- Infinite scroll detection may not work on all sites
- Some heavily obfuscated JavaScript sites may not render correctly

## Error Handling

The scraper implements graceful error handling:
- Timeouts return partial data when possible
- Network errors are reported in the `errors` array
- Invalid URLs return clear error messages
- JS rendering failures fall back to static content when available

## Performance

- Static scraping: Fast (< 2 seconds for most pages)
- JS rendering: Moderate (5-15 seconds depending on page complexity)
- Pagination depth 3: Variable (depends on site response times)