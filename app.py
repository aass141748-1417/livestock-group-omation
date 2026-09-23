import csv
from pathlib import Path

GROUP_LINK = "https://chat.whatsapp.com/LIEGIoWWBNLFfARCZYVGWC"

FIELDS = [
    "name",
    "phone",
    "interest",
    "city",
    "source",
    "consent",
    "status",
]

FILE = Path("leads.csv")


def create_database():
    if not FILE.exists():
        with FILE.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()


def add_lead(name, phone, interest, city, source, consent):
    create_database()

    row = {
        "name": name,
        "phone": phone,
        "interest": interest,
        "city": city,
        "source": source,
        "consent": "yes" if consent else "no",
        "status": "new",
    }

    with FILE.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writerow(row)


def invitation_message(name):
    return f"""السلام عليكم {name}

عندنا قروب متخصص في بيع وشراء المواشي والحلال،
وننشر فيه عروض البيع والطلبات.

إذا مهتم، تقدر تنضم من الرابط:
{GROUP_LINK}
"""


if __name__ == "__main__":
    create_database()
    print("Livestock Group Automation is ready.")
    print("Database:", FILE)
