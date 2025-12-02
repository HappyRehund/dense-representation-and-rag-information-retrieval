import requests
from bs4 import BeautifulSoup
import json
import os
import time

def clean_html(raw_html):
    """Remove HTML tags from content"""
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(" ", strip=True)

def scrape_detik_sport():
    """Main scraping function"""

    OUTPUT_DIR = "scraping_result"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    OUTPUT_FILE = os.path.join(OUTPUT_DIR, "detik_sport_articles.json")

    # Muat data lama (jika ada) dan siapkan set URL untuk deduplikasi lintas-run
    all_articles = []
    existing_urls = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            all_articles = json.load(f)
        existing_urls = {a.get("url") for a in all_articles if a.get("url")}
        print(f"Loaded {len(all_articles)} existing articles from {OUTPUT_FILE}")
    else:
        print("Starting with an empty list for new articles.")

    # Kategori (mengadopsi daftar dari potongan kode Anda)
    categories = [
        "https://sport.detik.com/sepakbola",
        "https://sport.detik.com/sepakbola/liga-spanyol",
        "https://sport.detik.com/sepakbola/bola-dunia",
        "https://sport.detik.com/raket",
        "https://sport.detik.com/moto-gp",
        "https://sport.detik.com/f1",
        "https://sport.detik.com/basket",
        "https://sport.detik.com/sport-lain"
    ]

    new_articles_added_count = 0

    # Scraping per kategori
    for category_url in categories:
        print(f"\nScraping category: {category_url}")

        try:
            response = requests.get(category_url, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to fetch {category_url}: {e}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        # Cari semua link artikel di halaman kategori
        potential_links = []
        for selector in [
            "article a.media__link",          # selector utama
            "article a",                      # fallback
            ".list-content__item a.media__link",
            ".list-content__item a"
        ]:
            links = soup.select(selector)
            if links:
                potential_links.extend([a["href"] for a in links if a.get("href")])

        # Buang duplikat internal & filter hanya link artikel detik sport
        article_links = list(set([
            link for link in potential_links
            if link.startswith("https://sport.detik.com")
        ]))

        if not article_links:
            print(f"No potential article links found on {category_url} with the current selectors.")
            continue

        print(f"Found {len(article_links)} potential article links on {category_url}")

        # Scraping tiap artikel
        for article_url in article_links:
            # Skip jika sudah ada (baik dari file lama maupun sesi ini)
            if article_url in existing_urls:
                continue

            try:
                article_response = requests.get(article_url, timeout=10)
                article_response.raise_for_status()
            except Exception as e:
                print(f"Failed to fetch article {article_url}: {e}")
                continue

            article_soup = BeautifulSoup(article_response.text, "html.parser")

            # Ekstraksi data artikel
            title_tag = article_soup.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else "N/A"

            date_tag = article_soup.find("div", class_="detail__date")
            if not date_tag:
                date_tag = article_soup.find("time")
            date = date_tag.get_text(strip=True) if date_tag else "N/A"

            author_tag = article_soup.find("div", class_="detail__author")
            if not author_tag:
                author_tag = article_soup.select_one(".author, .meta__author, span[itemprop='author']")
            author = author_tag.get_text(strip=True) if author_tag else "N/A"

            content_div = article_soup.find("div", class_="detail__body")
            if not content_div:
                content_div = article_soup.select_one(".detail__body, .detail__content, .article__body")
            content = clean_html(str(content_div)) if content_div else "N/A"

            # Simpan hasil artikel baru
            article_data = {
                "url": article_url,
                "title": title,
                "date": date,
                "author": author,
                "content": content
            }

            all_articles.append(article_data)
            existing_urls.add(article_url)
            new_articles_added_count += 1
            print(f"Scraped new article: {title}")

            time.sleep(1)  # hindari terlalu agresif

    # Simpan gabungan artikel lama + baru
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)

    print(f"\nScraping complete! Data saved to {OUTPUT_FILE}.")
    print(f"New articles added in this run: {new_articles_added_count}")
    print(f"Total articles in file: {len(all_articles)}")
    return all_articles

def main():
    """Main entry point"""
    print("Starting Detik Sport article scraping...")
    articles = scrape_detik_sport()
    print(f"Finished! Scraped {len(articles)} articles total.")

if __name__ == "__main__":
    main()