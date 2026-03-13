import argparse
import os
from concurrent.futures import ThreadPoolExecutor

from scrapers.maps_scraper import scrape_maps
from scrapers.maps_grid_scraper import scrape_maps_grid
from scrapers.instagram_scraper import scrape_instagram
from scrapers.linkedin_scraper import scrape_linkedin
from scrapers.universal_supplier_search_scraper import scrape_supplier_search

from utils.merger import merge_outputs
from utils.query_normalizer import normalize_query


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--source", default="all")
    # NEW: Expose the start_page argument!
    parser.add_argument("--start_page", type=int, default=0, help="Pages to skip for Google-based scrapers")

    args = parser.parse_args()
    os.makedirs("output", exist_ok=True)
    normalized = normalize_query(args.query)

    tasks = []

    # since Playwright will open 4 separate browser windows simultaneously!
    with ThreadPoolExecutor(max_workers=4) as executor:

        # UPDATED: Only run the basic maps scraper if specifically requested. 
        # Excluded from "all" to prevent duplicate work with maps_grid.
        if args.source == "maps":
            tasks.append(
                executor.submit(
                    scrape_maps,
                    normalized["maps_query"],
                    args.limit,
                    normalized["location"]
                )
            )

        # Maps Grid is the default map scraper for "all"
        if args.source in ["maps_grid", "all"]:
            tasks.append(
                executor.submit(
                    scrape_maps_grid,
                    normalized["maps_query"],
                    args.limit,
                    normalized["location"]
                )
            )

        if args.source in ["supplier_search", "all"]:
            tasks.append(
                executor.submit(
                    scrape_supplier_search,
                    normalized["maps_query"], # You could also use normalized["indiamart_query"] here
                    args.limit,
                    args.start_page           # Passed start_page!
                )
            )

        if args.source in ["linkedin", "all"]:
            tasks.append(
                executor.submit(
                    scrape_linkedin,
                    normalized["linkedin_query"],
                    args.limit,
                    args.start_page           # Passed start_page!
                )
            )

        if args.source in ["instagram", "all"]:
            tasks.append(
                executor.submit(
                    scrape_instagram,
                    normalized["instagram_query"], 
                    args.limit,
                    args.start_page           # Passed start_page!
                )
            )

        print("[MASTER] All scrapers launched. Waiting for completion...")
        for task in tasks:
            try:
                task.result() 
            except Exception as e:
                print(f"[!] A scraper thread crashed: {e}")
        
    print("[MASTER] All scraping threads closed. Merging outputs...")
    merge_outputs()

    print("[MASTER] Lead collection finished successfully.")

if __name__ == "__main__":
    main()