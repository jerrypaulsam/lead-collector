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

- Python 3.8 or higher
- Internet connection for web scraping

## Installation

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd lead-finder
   ```

2. **Set up the environment:**
   - **On Windows:**
     Run `setup.bat` to create a virtual environment, install dependencies, and set up Playwright browsers.
   - **On macOS/Linux:**
     Run `setup.sh` to create a virtual environment, install dependencies, and set up Playwright browsers.

   These scripts will:
   - Create a virtual environment (`venv`)
   - Install required Python packages from `requirements.txt`
   - Install Playwright browsers for web automation

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

   - `--query`: The search query (required)
   - `--limit`: Maximum number of leads to collect (default: 100)
   - `--source`: Source to scrape from (maps, maps_grid, instagram, linkedin, supplier_search, or all; default: all)

### Output

Results are saved in the `output/` directory as Excel files. The application merges outputs from different sources when applicable.

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

- If you encounter issues with Playwright, try running `playwright install` manually after activating the virtual environment.
- Ensure all dependencies are installed correctly by checking `pip list`.
- For GUI issues on some systems, try running with `python -m gui_app.py`.

## License

MIT License. See the LICENSE file for details.