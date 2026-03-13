import pandas as pd
import os
import re

def clean_company_name(name):
    """Normalizes company names so 'Shopdibz Pvt Ltd' matches 'Shopdibz'"""
    if pd.isna(name): return ""
    name = str(name).lower()
    name = re.sub(r'[^a-z0-9\s]', '', name)
    # Strip common suffixes that mess up matching
    name = re.sub(r'\bpvt\b|\bprivate\b|\bltd\b|\blimited\b', '', name)
    return " ".join(name.split())

def merge_outputs():
    master_file = "output/master_leads.xlsx"
    
    # UPDATED: File names now perfectly match your upgraded scraper scripts
    files = [
        "output/maps_leads.xlsx",
        "output/maps_grid_leads.xlsx",
        "output/supplier_search_leads.xlsx",
        "output/instagram_leads.xlsx",
        "output/linkedin_leads.xlsx"
    ]
    
    frames = []
    
    # 1. LOAD THE EXISTING MASTER DATABASE (If it exists)
    master_size = 0
    if os.path.exists(master_file):
        try:
            master_df = pd.read_excel(master_file)
            if not master_df.empty:
                frames.append(master_df)
                master_size = len(master_df)
                print(f"[MERGER] Loaded existing master database ({master_size} rows).")
        except Exception as e:
            print(f"[MERGER] Error loading master file: {e}")

    # 2. LOAD TODAY'S FRESH DATA
    daily_count = 0
    for f in files:
        if os.path.exists(f):
            try:
                df = pd.read_excel(f)
                if not df.empty:
                    frames.append(df)
                    daily_count += len(df)
            except Exception as e:
                print(f"[MERGER] Failed to load {f}: {e}")

    if not frames:
        print("[MERGER] No data to merge.")
        return

    print(f"[MERGER] Processing {daily_count} new leads...")
    merged = pd.concat(frames, ignore_index=True)

    # 3. CLEAN UP COLUMNS FOR CROSS-PLATFORM MATCHING
    # Ensure columns exist and fill NaNs to prevent pandas crashing
    for col in ["Company", "Phone", "Email"]:
        if col not in merged.columns:
            merged[col] = ""
        merged[col] = merged[col].fillna("").astype(str)

    # Create temporary normalized columns for strict comparison
    merged["_Norm_Company"] = merged["Company"].apply(clean_company_name)
    merged["_Norm_Phone"] = merged["Phone"].str.replace(r'[\+\-\s]', '', regex=True)

    # 4. DATA PRIORITIZATION (Keep the rows with the most data!)
    # We count how many columns actually have text, and push the richest rows to the top
    merged['Data_Count'] = (merged != "").sum(axis=1)
    merged = merged.sort_values('Data_Count', ascending=False)

    # 5. THE DEDUPLICATION GAUNTLET
    
    # A. Deduplicate by Company Name
    merged = merged.drop_duplicates(subset=["_Norm_Company"], keep="first")
    
    # B. Deduplicate by Phone (But don't drop rows that just have empty phones!)
    merged.loc[merged["_Norm_Phone"] == "", "_Norm_Phone"] = merged["Company"] + "_no_phone"
    merged = merged.drop_duplicates(subset=["_Norm_Phone"], keep="first")

    # C. Deduplicate by Email (Don't drop rows with empty emails)
    merged.loc[merged["Email"] == "", "Email"] = merged["Company"] + "_no_email"
    merged = merged.drop_duplicates(subset=["Email"], keep="first")

    # 6. CLEANUP
    # Revert the temporary placeholders back to empty strings
    merged.loc[merged["Email"].str.contains("_no_email"), "Email"] = ""
    # Drop the temporary calculation columns so the Excel sheet looks clean
    merged = merged.drop(columns=["_Norm_Company", "_Norm_Phone", "Data_Count"], errors='ignore')

    # 7. SAVE THE MASTER
    merged.to_excel(master_file, index=False)
    
    final_count = len(merged)
    new_added = final_count - master_size
    
    print(f"[MERGER] Database updated! Added {new_added} unique new leads.")
    print(f"[MERGER] Total master database size is now: {final_count} leads.")

    # 8. DELETE THE DAILY SHARDS
    # This prevents the script from double-processing yesterday's files if you run it again tomorrow
    for f in files:
        if os.path.exists(f):
            os.remove(f)