"""PDF (fpdf2) and CSV report generation.

fpdf2's `cells`/`multi_cell` do the layout; we keep fonts standard so no
external font files are needed (₹ is written as "Rs." for WinAnsi safety).
"""
import csv
import io
from datetime import datetime

from fpdf import FPDF

from app.services.finance import CropFinancials


def _money(v: float | None) -> str:
    return f"Rs. {v:,.0f}" if v is not None else "-"


class _ReportPDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 16)
        self.cell(0, 10, "KisanProfit Report", align="C")
        self.ln(4)
        self.set_font("helvetica", "I", 9)
        self.cell(0, 6, f"Generated {datetime.now().strftime('%d %b %Y %H:%M')}", align="C")
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()} of {{nb}}", align="C")


def _table(pdf: _ReportPDF, headers: list[str], rows: list[list[str]], widths: list[float]):
    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(235, 245, 230)
    for h, w in zip(headers, widths):
        pdf.cell(w, 8, h, border=1, fill=True)
    pdf.ln()
    pdf.set_font("helvetica", "", 10)
    for row in rows:
        for cell, w in zip(row, widths):
            pdf.cell(w, 8, cell, border=1)
        pdf.ln()
    pdf.ln(2)


def crop_profitability_pdf(crop_name: str, fin: CropFinancials) -> bytes:
    pdf = _ReportPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, f"Crop Profitability: {crop_name}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    _table(
        pdf,
        ["Metric", "Value"],
        [
            ["Area", f"{fin.area_acres:.2f} acres"],
            ["Total cost", _money(fin.total_cost)],
            ["Gross revenue", _money(fin.gross_revenue)],
            ["Selling costs (transport etc.)", _money(fin.selling_costs)],
            ["Net revenue", _money(fin.revenue)],
            ["Net profit", _money(fin.profit)],
            ["ROI", f"{fin.roi_percent:.1f}%"],
            ["Cost per acre", _money(fin.cost_per_acre)],
            ["Profit per acre", _money(fin.profit_per_acre)],
            ["Produced", f"{fin.produced_quintal:.2f} quintal"],
            ["Sold", f"{fin.sold_quintal:.2f} quintal"],
            ["Break-even price", _money(fin.break_even_price_per_quintal)],
        ],
        [90, 80],
    )

    if fin.expense_by_category:
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 8, "Expenses by category", new_x="LMARGIN", new_y="NEXT")
        _table(
            pdf,
            ["Category", "Amount"],
            [[c, _money(a)] for c, a in sorted(fin.expense_by_category.items(), key=lambda kv: -kv[1])],
            [90, 80],
        )
    return bytes(pdf.output())


def summary_pdf(title: str, headers: list[str], rows: list[list[str]]) -> bytes:
    pdf = _ReportPDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    widths = [180 / len(headers)] * len(headers)
    _table(pdf, headers, rows, widths)
    return bytes(pdf.output())


def csv_bytes(headers: list[str], rows: list[list[str]]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(headers)
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8-sig")  # BOM so Excel opens it cleanly
