import csv
import re
import time
from pathlib import Path
from urllib.parse import quote_plus

import feedparser
import requests
from bs4 import BeautifulSoup


FILE = Path("leads.csv")

FIELDS = [
    "name",
    "phone",
    "interest",
    "category",
    "deal_type",
    "city",
    "source",
    "consent",
    "status",
]

CITY = "المدينة المنورة"

SEARCH_QUERIES = [
    ("مواشي المدينة المنورة", "مواشي"),
    ("بيع أغنام المدينة المنورة", "أغنام"),
    ("شراء أغنام المدينة المنورة", "أغنام"),
    ("حراج مواشي المدينة المنورة", "مواشي"),
    ("مربي أغنام المدينة المنورة", "مواشي"),
    ("تاجر أغنام المدينة المنورة", "مواشي"),
    ("حلال المدينة المنورة", "حلال"),
    ("مواشي للبيع المدينة المنورة", "مواشي"),
]

PHONE_RE = re.compile(
    r"(?:(?:\+?966|00966)[\s\-]?(?:5\d|1\d|8\d)"
    r"[\s\-]?\d{3}[\s\-]?\d{4}|"
    r"05\d[\s\-]?\d{3}[\s\-]?\d{4})"
)

BUSINESS_WORDS = [
    "مؤسسة",
    "شركة",
    "مزرعة",
    "مسلخ",
    "مربى",
    "مربي",
    "تاجر",
    "مواشي",
    "أغنام",
    "حلال",
    "للبيع",
    "للتواصل",
    "واتساب",
    "اتصل",
]


def classify_deal(text):
    text = text.lower()

    if "شراء" in text or "مطلوب" in text or "نشتري" in text:
        return "شراء"

    if "بيع" in text or "للبيع" in text:
        return "بيع"

    if "مزاد" in text:
        return "مزاد"

    return "غير محدد"


def normalize_phone(phone):
    digits = re.sub(r"\D", "", phone)

    if digits.startswith("00966"):
        digits = digits[2:]

    if digits.startswith("9665") and len(digits) == 12:
        return "+" + digits

    if digits.startswith("05") and len(digits) == 10:
        return "+966" + digits[1:]

    return ""


def extract_phones(text):
    phones = []

    for match in PHONE_RE.findall(text or ""):
        phone = normalize_phone(match)

        if phone and phone not in phones:
            phones.append(phone)

    return phones


def clean_name(title):
    if not title:
        return ""

    title = re.sub(r"\s+", " ", title).strip()

    for separator in [" - ", " | ", " :: "]:
        if separator in title:
            title = title.split(separator)[0].strip()

    return title[:150]


def looks_like_business(text):
    text = text or ""

    return any(
        word in text
        for word in BUSINESS_WORDS
    )


def fetch_page(url):
    try:
        response = requests.get(
            url,
            timeout=12,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(compatible; LivestockResearch/1.0)"
                )
            },
        )

        if response.status_code != 200:
            return ""

        return response.text

    except Exception as error:
        print(f"تعذر فتح المصدر: {error}")
        return ""


def extract_business_contact(url, title, summary):
    page_html = fetch_page(url)

    if not page_html:
        return "", ""

    soup = BeautifulSoup(
        page_html,
        "html.parser"
    )

    for tag in soup(
        ["script", "style", "noscript"]
    ):
        tag.decompose()

    text = soup.get_text(
        " ",
        strip=True
    )

    combined = (
        f"{title} "
        f"{summary} "
        f"{text}"
    )

    if not looks_like_business(combined):
        return "", ""

    phones = extract_phones(combined)

    if not phones:
        return "", ""

    name = clean_name(title)

    if soup.title:
        site_name = soup.title.get_text(
            strip=True
        )

        if site_name and looks_like_business(
            site_name
        ):
            name = clean_name(site_name)

    return name, phones[0]


def create_database():
    if not FILE.exists():
        with FILE.open(
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=FIELDS
            )
            writer.writeheader()


def get_existing_sources():
    sources = set()

    if not FILE.exists():
        return sources

    with FILE.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as f:
        reader = csv.DictReader(f)

        for row in reader:
            source = (
                row.get("source") or ""
            ).strip()

            if source:
                sources.add(source)

    return sources


def get_existing_phones():
    phones = set()

    if not FILE.exists():
        return phones

    with FILE.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as f:
        reader = csv.DictReader(f)

        for row in reader:
            phone = (
                row.get("phone") or ""
            ).strip()

            if phone:
                phones.add(phone)

    return phones


def search_public_results(query):
    url = (
        "https://news.google.com/rss/search?"
        f"q={quote_plus(query)}"
        "&hl=ar&gl=SA&ceid=SA:ar"
    )

    feed = feedparser.parse(url)

    return feed.entries


def main():
    create_database()

    existing_sources = (
        get_existing_sources()
    )

    existing_phones = (
        get_existing_phones()
    )

    new_count = 0

    with FILE.open(
        "a",
        newline="",
        encoding="utf-8-sig",
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=FIELDS
        )

        for query, category in SEARCH_QUERIES:

            print(
                f"البحث عن: {query}"
            )

            entries = search_public_results(
                query
            )

            for entry in entries:

                source = (
                    entry.get("link") or ""
                ).strip()

                title = (
                    entry.get("title") or ""
                ).strip()

                summary = (
                    entry.get("summary") or ""
                ).strip()

                if not source:
                    continue

                if source in existing_sources:
                    continue

                deal_type = classify_deal(
                    f"{query} {title}"
                )

                name, phone = (
                    extract_business_contact(
                        source,
                        title,
                        summary,
                    )
                )

                if not phone:
                    continue

                if phone in existing_phones:
                    continue

                writer.writerow(
                    {
                        "name": name,
                        "phone": phone,
                        "interest": query,
                        "category": category,
                        "deal_type": deal_type,
                        "city": CITY,
                        "source": source,
                        "consent": "no",
                        "status": "discovered",
                    }
                )

                existing_sources.add(
                    source
                )

                existing_phones.add(
                    phone
                )

                new_count += 1

                print(
                    f"تم العثور على جهة: "
                    f"{name} | {phone}"
                )

                time.sleep(1)

    print(
        f"تم اكتشاف {new_count} "
        f"جهة تجارية جديدة."
    )


if __name__ == "__main__":
    main()
