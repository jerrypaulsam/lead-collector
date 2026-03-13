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

    args = parser.parse_args()
    os.makedirs("output", exist_ok=True)
    normalized = normalize_query(args.query)

    tasks = []

    # since Playwright will open 4 separate browser windows simultaneously!
    with ThreadPoolExecutor(max_workers=4) as executor:

        # NOTE: Running 'maps' and 'maps_grid' simultaneously on 'all' will duplicate effort 
        # and doubly hit Google. You might want to choose one over the other in your logic.
        if args.source in ["maps", "all"]:
            tasks.append(
                executor.submit(
                    scrape_maps,
                    normalized["maps_query"],
                    args.limit,
                    normalized["location"]
                )
            )

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
                    normalized["maps_query"],
                    args.limit
                )
            )

        if args.source in ["linkedin", "all"]:
            tasks.append(
                executor.submit(
                    scrape_linkedin,
                    normalized["linkedin_query"],
                    args.limit
                )
            )

        if args.source in ["instagram", "all"]:
            tasks.append(
                executor.submit(
                    scrape_instagram,
                    normalized["instagram_query"], 
                    args.limit
                )
            )

        print("All scrapers launched. Waiting for completion...")
        for task in tasks:
            try:
                task.result() 
            except Exception as e:
                print(f"A scraper thread crashed: {e}")
        
    print("All scraping threads closed. Merging outputs...")
    merge_outputs()

    print("Lead collection finished successfully.")

if __name__ == "__main__":
    main()