# Lead Finder

Lead Finder is a Python-based application designed to scrape and collect leads from various online sources such as Google Maps, Instagram, LinkedIn, and universal supplier searches. It provides both a command-line interface (CLI) and a graphical user interface (GUI) for ease of use.

## Features

- Scrape leads from Google Maps
- Extract data from Instagram profiles
- Gather information from LinkedIn
- Perform universal supplier searches
- Merge and normalize query inputs
- Output results in structured formats (e.g., Excel)

## Prerequisites

- Python 3.11 or higher (required by the pinned pandas/numpy versions)
- Internet connection for web scraping
- For GUI mode: tkinter (included with Python on Windows and macOS; may need separate installation on Linux)

### Installing tkinter on Linux

- **Ubuntu/Debian:** `sudo apt-get install python3-tk`
- **Fedora/CentOS:** `sudo dnf install python3-tkinter`
- **Arch Linux:** `sudo pacman -S tk`

If tkinter is not available, you can still use the command-line interface.

## Installation

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd lead-finder
   ```

2. **Set up the environment:**
   - **On Windows:** Run `setup.bat` to create a virtual environment, install dependencies, and set up Playwright browsers.
   - **On macOS/Linux:** Run `setup.sh` to create a virtual environment, install dependencies, and set up Playwright browsers.

   These scripts will:
   - Check for Python 3.11+ installation
   - Create a virtual environment (`venv`) if it doesn't exist
   - Install required Python packages from `requirements.txt`
   - Install the Playwright Chromium browser for web automation
   - On Linux, check for tkinter availability and provide installation instructions if missing

## Usage

### GUI Mode (Recommended for beginners)

1. Activate the virtual environment:
   - **Windows:** `venv\Scripts\activate`
   - **macOS/Linux:** `source venv/bin/activate`

2. Run the GUI application:
   ```
   python gui_app.py
   ```

3. In the GUI:
   - Enter your search query
   - Select the source (maps, instagram, linkedin, supplier_search, or all)
   - Set the lead limit
   - Click "Run Scraper" to start the process
   - View progress in the status box and history table

### CLI Mode

1. Activate the virtual environment (as above).

2. Run the CLI application:
   ```
   python app.py --query "your search query" --limit 100 --source all
   ```

   Or use the run script:
   - **Windows:** `run.bat --query "your search query" --limit 100 --source all`
   - **macOS/Linux:** `./run.sh --query "your search query" --limit 100 --source all`

   - `--query`: The search query (required)
   - `--limit`: Maximum number of leads to collect (default: 100)
   - `--source`: Source to scrape from (maps, maps_grid, instagram, linkedin, supplier_search, or all; default: all)
   - `--start_page`: Number of Google result pages to skip (Instagram, LinkedIn and supplier search only; default: 0)

   **Locations:** put the city in your query (e.g. `"clothing manufacturer in Bengaluru"`). `maps_grid` splits supported cities (see `utils/geo_utils.py`, including aliases like Bengaluru, New Delhi, Cochin) into a 7x7 grid of searches. For other locations it falls back to a single normal Maps search.

### Output

Results are saved in the `output/` directory as Excel files. Each run's results are merged into `output/master_leads.xlsx` (deduplicated by company name, phone and email). URLs that were successfully scraped are recorded in `output/master_seen_urls.txt` and skipped on later runs; delete that file to start fresh.

### Saved sessions

Each scraper saves its browser session (cookies) to `sessions/<scraper>_state.json` so later runs reuse it. These files contain live login/cookie data: they are git-ignored, readable only by your user account, and should never be shared or committed. Delete the `sessions/` folder to start with a clean browser session.

## Project Structure

- `app.py`: CLI entry point
- `gui_app.py`: GUI entry point
- `scrapers/`: Contains scraper modules for different platforms
- `utils/`: Utility functions for data processing, merging, etc.
- `requirements.txt`: Python dependencies
- `setup.bat` / `setup.sh`: Setup scripts for Windows/macOS/Linux
- `run.bat` / `run.sh`: Run scripts (activate venv and start app)

## Notes

- The application uses Playwright for browser automation, which may require additional browser installations.
- Be respectful of website terms of service and rate limits when scraping.
- Some sources may require authentication or have anti-scraping measures.

## Troubleshooting

- If you encounter issues with Playwright, try running `playwright install chromium` manually after activating the virtual environment.
- Ensure all dependencies are installed correctly by checking `pip list`.
- Run the GUI from the project folder (`python gui_app.py`), since it starts `app.py` from the current directory.
- If tkinter is not available on Linux, install it using the commands provided during setup or in the Prerequisites section.
- The setup scripts will check for Python version and tkinter availability and provide helpful error messages.

## License

MIT License. See the LICENSE file for details.