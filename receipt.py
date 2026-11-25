"""
receipt.py
-----------
Generates a printable shopping-list summary (shelf locations) as both
plain text and PDF, satisfying functional requirement #4 ("display and
optionally print a list of items with their shelf numbers").
"""

from datetime import datetime
from reportlab.lib.pagesizes import A6
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def build_text_receipt(found_items, not_found_items):
    """Return a plain-text, printer-friendly receipt string."""
    lines = []
    lines.append("=" * 40)
    lines.append("   SUPERMARKET SHELF LOCATOR - RECEIPT")
    lines.append("=" * 40)
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("-" * 40)

    if found_items:
        sorted_items = sorted(found_items, key=lambda x: x["shelf"])
        lines.append(f"{'ITEM':<18}{'CATEGORY':<20}{'SHELF':<6}")
        lines.append("-" * 40)
        for it in sorted_items:
            lines.append(f"{it['item'].title():<18}{it['category']:<20}{it['shelf']:<6}")
    else:
        lines.append("No items matched.")

    if not_found_items:
        lines.append("-" * 40)
        lines.append("Items not found in store database:")
        for nf in not_found_items:
            lines.append(f"  - {nf}")

    lines.append("=" * 40)
    lines.append(f"Total items located: {len(found_items)}")
    lines.append("Thank you for shopping with us!")
    lines.append("=" * 40)
    return "\n".join(lines)


def build_pdf_receipt(found_items, not_found_items, output_path):
    """Render the shelf list as a small printable PDF (receipt-size page)."""
    width, height = A6
    c = canvas.Canvas(output_path, pagesize=A6)
    margin = 8 * mm
    y = height - margin

    def line(text, size=9, bold=False, gap=5.2 * mm):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(margin, y, text)
        y -= gap

    line("SUPERMARKET SHELF LOCATOR", size=11, bold=True, gap=6 * mm)
    line(datetime.now().strftime("%Y-%m-%d %H:%M"), size=8)
    y -= 1 * mm
    c.line(margin, y, width - margin, y)
    y -= 4 * mm

    line(f"{'Item':<16}{'Shelf':<8}", size=9, bold=True)
    c.line(margin, y + 2 * mm, width - margin, y + 2 * mm)
    y -= 2 * mm

    sorted_items = sorted(found_items, key=lambda x: x["shelf"])
    for it in sorted_items:
        line(f"{it['item'].title():<16}{it['shelf']:<8}")

    if not_found_items:
        y -= 2 * mm
        line("Not found:", size=9, bold=True)
        for nf in not_found_items:
            line(f" - {nf}", size=8)

    y -= 2 * mm
    c.line(margin, y, width - margin, y)
    y -= 5 * mm
    line(f"Total located: {len(found_items)}", size=8)
    line("Thank you for shopping with us!", size=8)

    c.showPage()
    c.save()
    return output_path
