import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────
# 1. CONFIGURATION
# ─────────────────────────────────────────
BASE_URL = "https://books.toscrape.com/catalogue/"
START_URL = "https://books.toscrape.com/catalogue/page-1.html"
MAX_PAGES = 5          # scrape first 5 pages (change to scrape more)
PRICE_FILTER = 50.0    # only save books under £50


# ─────────────────────────────────────────
# 2. SCRAPE A SINGLE PAGE
# ─────────────────────────────────────────
def scrape_page(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to fetch: {url}")
        return [], None

    soup = BeautifulSoup(response.text, "html.parser")
    books = soup.find_all("article", class_="product_pod")

    data = []
    for book in books:
        # Title
        title = book.h3.a["title"]

        # Price — remove £ and convert to float
        price_text = book.find("p", class_="price_color").text.strip()
        price = float(price_text.replace("£", "").replace("Â", "").strip())

        # Rating — convert word to number
        rating_map = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
        rating_class = book.p["class"][1]
        rating = rating_map.get(rating_class, 0)

        # Availability
        availability = book.find("p", class_="instock availability").text.strip()

        data.append({
            "title": title,
            "price_gbp": price,
            "rating": rating,
            "availability": availability
        })

    # Get next page URL
    next_btn = soup.find("li", class_="next")
    next_url = BASE_URL + next_btn.a["href"] if next_btn else None

    return data, next_url


# ─────────────────────────────────────────
# 3. SCRAPE MULTIPLE PAGES
# ─────────────────────────────────────────
def scrape_all_pages():
    all_data = []
    url = START_URL
    page = 1

    while url and page <= MAX_PAGES:
        print(f"📄 Scraping page {page}...")
        data, next_url = scrape_page(url)
        all_data.extend(data)
        url = next_url
        page += 1

    print(f"\n✅ Total books scraped: {len(all_data)}")
    return all_data


# ─────────────────────────────────────────
# 4. CLEAN & FILTER DATA
# ─────────────────────────────────────────
def clean_data(all_data):
    df = pd.DataFrame(all_data)

    # Remove duplicates
    df.drop_duplicates(subset="title", inplace=True)

    # Filter by price
    df_filtered = df[df["price_gbp"] < PRICE_FILTER].copy()

    # Sort by rating (highest first)
    df_filtered.sort_values("rating", ascending=False, inplace=True)

    # Reset index
    df_filtered.reset_index(drop=True, inplace=True)

    print(f"📊 Books after filtering (under £{PRICE_FILTER}): {len(df_filtered)}")
    return df, df_filtered


# ─────────────────────────────────────────
# 5. SAVE TO CSV
# ─────────────────────────────────────────
def save_to_csv(df_all, df_filtered):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save all scraped data
    all_file = f"books_all_{timestamp}.csv"
    df_all.to_csv(all_file, index=False)
    print(f"💾 All books saved to: {all_file}")

    # Save filtered data
    filtered_file = f"books_filtered_{timestamp}.csv"
    df_filtered.to_csv(filtered_file, index=False)
    print(f"💾 Filtered books saved to: {filtered_file}")

    return all_file, filtered_file


# ─────────────────────────────────────────
# 6. SHOW SUMMARY
# ─────────────────────────────────────────
def show_summary(df_filtered):
    print("\n" + "="*50)
    print("         📚 TOP 5 BOOKS BY RATING")
    print("="*50)
    top5 = df_filtered.head(5)[["title", "price_gbp", "rating"]]
    for i, row in top5.iterrows():
        print(f"{i+1}. {row['title'][:45]}")
        print(f"   Price: £{row['price_gbp']} | Rating: {'⭐' * row['rating']}")
        print()

    print("="*50)
    print(f"  Avg Price : £{df_filtered['price_gbp'].mean():.2f}")
    print(f"  Avg Rating: {df_filtered['rating'].mean():.1f} / 5")
    print(f"  Total Books: {len(df_filtered)}")
    print("="*50)


# ─────────────────────────────────────────
# 7. MAIN
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Book Scraper Started!\n")

    # Step 1: Scrape
    all_data = scrape_all_pages()

    # Step 2: Clean & Filter
    df_all, df_filtered = clean_data(all_data)

    # Step 3: Save to CSV
    save_to_csv(df_all, df_filtered)

    # Step 4: Show Summary
    show_summary(df_filtered)

    print("\n✅ Scraping complete!")