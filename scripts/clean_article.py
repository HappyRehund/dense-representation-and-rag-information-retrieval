"""
Script untuk membersihkan konten artikel dari noise/outliers.
Menghapus:
- SCROLL TO CONTINUE WITH CONTENT
- ADVERTISEMENT
- Teks dalam kurung (...)
- Baca juga: ...
- Video ... (di akhir artikel)
- Tag/keyword di akhir artikel
- [Gambas:...]
- Inisial penulis seperti (nds/krs), (aff/nds), dll
"""

import json
import re
import os


def clean_content(text: str) -> str:
    """
    Membersihkan konten artikel dari berbagai noise.

    Args:
        text: Teks konten mentah dari artikel

    Returns:
        Teks yang sudah dibersihkan
    """
    if not text:
        return ""

    cleaned = text

    # 1. Hapus "SCROLL TO CONTINUE WITH CONTENT"
    cleaned = cleaned.replace("SCROLL TO CONTINUE WITH CONTENT", "")

    # 2. Hapus "ADVERTISEMENT"
    cleaned = cleaned.replace("ADVERTISEMENT", "")

    # 3. Hapus "[Gambas:...]" pattern
    cleaned = re.sub(r'\[Gambas:[^\]]*\]', '', cleaned)

    # 4. Hapus "Baca juga: ..." sampai akhir kalimat
    cleaned = re.sub(r'Baca juga:\s*[^.!?]*[.!?]?', '', cleaned)

    # 5. Hapus "Video ..." di akhir artikel (biasanya judul video yang diulang)
    # Pattern: Video [judul] Video [judul yang sama]
    cleaned = re.sub(r'Video\s+[^V]+Video\s+[^\(]+', '', cleaned)
    # Juga hapus single "Video ..." di akhir
    cleaned = re.sub(r'Video:\s*[^\(]+$', '', cleaned)

    # 6. Hapus "Saksikan Live DetikSore :"
    cleaned = re.sub(r'Saksikan Live[^:]*:\s*', '', cleaned)

    # 7. Hapus teks dalam kurung biasa (...) - termasuk inisial penulis
    # Ini akan menghapus (nds/krs), (aff/nds), (Foto: ...), dll
    cleaned = re.sub(r'\([^)]*\)', '', cleaned)

    # 8. Hapus tag/keyword di akhir artikel (biasanya kata-kata tanpa spasi yang berurutan)
    # Pattern: kata kata kata di akhir string (lowercase tags)
    # Contoh: "marcus rashford barcelona manchester united deco"
    # Ini biasanya muncul di akhir artikel sebagai tags

    # 9. Hapus multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned)

    # 10. Hapus leading/trailing whitespace
    cleaned = cleaned.strip()

    # 11. Hapus trailing tags (biasanya kata-kata lowercase di akhir)
    # Deteksi dan hapus tag jika ada pattern tags di akhir
    # Tags biasanya: "nama nama liga klub" format lowercase
    lines = cleaned.split('.')
    if lines:
        last_sentence = lines[-1].strip()
        # Jika kalimat terakhir hanya berisi kata-kata lowercase tanpa punctuation
        # dan terlihat seperti tags (lebih dari 2 kata, semua lowercase)
        words = last_sentence.split()
        if len(words) >= 3:
            # Cek apakah terlihat seperti tags (banyak proper nouns tanpa struktur kalimat)
            # Tags biasanya tidak punya kata kerja atau struktur gramatikal
            is_likely_tags = all(
                word[0].islower() or word.lower() in [
                    'ac', 'as', 'fc', 'vs', 'mu', 'manchester', 'real', 'barcelona',
                    'liga', 'serie', 'premier', 'league', 'spanyol', 'italia', 'inggris',
                    'piala', 'dunia', 'timnas', 'indonesia'
                ] for word in words if word.isalpha()
            )
            if is_likely_tags and not any(
                verb in last_sentence.lower()
                for verb in ['adalah', 'akan', 'sudah', 'telah', 'sedang', 'bisa', 'harus']
            ):
                cleaned = '.'.join(lines[:-1]).strip()
                if not cleaned.endswith('.'):
                    cleaned += '.'

    return cleaned


def clean_articles_file(input_path: str, output_path: str) -> dict:
    """
    Membersihkan semua artikel dalam file JSON.

    Args:
        input_path: Path ke file JSON input
        output_path: Path ke file JSON output

    Returns:
        Dictionary dengan statistik pembersihan
    """
    # Load data
    with open(input_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    print(f"Loaded {len(articles)} articles from {input_path}")

    # Statistics
    stats = {
        'total_articles': len(articles),
        'total_chars_before': 0,
        'total_chars_after': 0,
        'articles_cleaned': 0
    }

    # Clean each article
    cleaned_articles = []
    for article in articles:
        original_content = article.get('content', '')
        stats['total_chars_before'] += len(original_content)

        cleaned_content = clean_content(original_content)
        stats['total_chars_after'] += len(cleaned_content)

        if original_content != cleaned_content:
            stats['articles_cleaned'] += 1

        # Create cleaned article
        cleaned_article = {
            'url': article.get('url', ''),
            'title': article.get('title', ''),
            'date': article.get('date', ''),
            'author': article.get('author', ''),
            'content': cleaned_content
        }
        cleaned_articles.append(cleaned_article)

    # Save cleaned data
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cleaned_articles, f, ensure_ascii=False, indent=2)

    print(f"\nCleaning Statistics:")
    print(f"  Total articles: {stats['total_articles']}")
    print(f"  Articles modified: {stats['articles_cleaned']}")
    print(f"  Characters before: {stats['total_chars_before']:,}")
    print(f"  Characters after: {stats['total_chars_after']:,}")
    print(f"  Characters removed: {stats['total_chars_before'] - stats['total_chars_after']:,}")
    print(f"  Reduction: {((stats['total_chars_before'] - stats['total_chars_after']) / stats['total_chars_before'] * 100):.2f}%")
    print(f"\nCleaned data saved to {output_path}")

    return stats


def preview_cleaning(input_path: str, num_samples: int = 3) -> None:
    """
    Preview hasil pembersihan untuk beberapa artikel.

    Args:
        input_path: Path ke file JSON input
        num_samples: Jumlah sampel untuk ditampilkan
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    print("=" * 80)
    print("PREVIEW CLEANING RESULTS")
    print("=" * 80)

    for i, article in enumerate(articles[:num_samples]):
        print(f"\n{'='*80}")
        print(f"Article {i+1}: {article.get('title', 'No title')}")
        print("-" * 80)

        original = article.get('content', '')
        cleaned = clean_content(original)

        print("\n[ORIGINAL]:")
        print(original[:500] + "..." if len(original) > 500 else original)

        print("\n[CLEANED]:")
        print(cleaned[:500] + "..." if len(cleaned) > 500 else cleaned)

        print(f"\n[STATS]: {len(original)} chars -> {len(cleaned)} chars (removed {len(original) - len(cleaned)} chars)")


def main():
    """Main entry point"""
    INPUT_FILE = "scraping_result/detik_sport_articles.json"
    OUTPUT_FILE = "scraping_result/detik_sport_articles_cleaned.json"

    print("Starting article content cleaning...")
    print("=" * 80)

    # Check if input file exists
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file not found: {INPUT_FILE}")
        return

    # Preview first
    print("\n[STEP 1] Preview cleaning results...")
    preview_cleaning(INPUT_FILE, num_samples=2)

    # Clean all articles
    print("\n" + "=" * 80)
    print("[STEP 2] Cleaning all articles...")
    stats = clean_articles_file(INPUT_FILE, OUTPUT_FILE)

    print("\n" + "=" * 80)
    print("Cleaning complete!")


if __name__ == "__main__":
    main()
