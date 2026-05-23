from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.models.business import Business
from app.models.daily_operation_closure import DailyOperationClosure
from app.models.daily_operation_closure_item import DailyOperationClosureItem


PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_X = 1.15 * cm
TOP_Y = PAGE_HEIGHT - 1.15 * cm
BOTTOM_Y = 1.2 * cm

LOCAL_REPORT_TIMEZONE = ZoneInfo("Europe/Istanbul")

INK = colors.HexColor("#172033")
MUTED = colors.HexColor("#64748B")
LINE = colors.HexColor("#D8E5EA")
WHITE = colors.white

PASTEL_MINT = colors.HexColor("#E8FAF6")
PASTEL_MINT_LINE = colors.HexColor("#B7EFE4")
PASTEL_TEAL = colors.HexColor("#C8F7EF")
PASTEL_TEAL_DARK = colors.HexColor("#14B8A6")
PASTEL_BLUE = colors.HexColor("#E6F0FF")
PASTEL_BLUE_LINE = colors.HexColor("#BFD7FF")
PASTEL_GREEN = colors.HexColor("#E3FBEA")
PASTEL_GREEN_LINE = colors.HexColor("#B9F2C8")
PASTEL_PURPLE = colors.HexColor("#F0EAFE")
PASTEL_PURPLE_LINE = colors.HexColor("#DDD2FE")
PASTEL_ROSE = colors.HexColor("#FFECEF")
PASTEL_ROSE_LINE = colors.HexColor("#FFD0D8")
PASTEL_AMBER = colors.HexColor("#FFF4D6")
PASTEL_AMBER_LINE = colors.HexColor("#FDE59A")
PASTEL_GRAY = colors.HexColor("#F8FAFC")
PASTEL_GRAY_2 = colors.HexColor("#F1F5F9")


TURKISH_TO_ASCII_TRANSLATION = str.maketrans(
    {
        "ç": "c",
        "Ç": "C",
        "ğ": "g",
        "Ğ": "G",
        "ı": "i",
        "İ": "I",
        "ö": "o",
        "Ö": "O",
        "ş": "s",
        "Ş": "S",
        "ü": "u",
        "Ü": "U",
    }
)


def find_existing_font_path(candidates: list[str]) -> str | None:
    for candidate in candidates:
        path = Path(candidate)

        if path.exists():
            return str(path)

    return None


def register_pdf_fonts() -> tuple[str, str, bool]:
    regular_candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    ]

    bold_candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    ]

    regular_path = find_existing_font_path(regular_candidates)
    bold_path = find_existing_font_path(bold_candidates)

    if regular_path:
        pdfmetrics.registerFont(TTFont("MissioRegular", regular_path))

        if bold_path:
            pdfmetrics.registerFont(TTFont("MissioBold", bold_path))
            return "MissioRegular", "MissioBold", True

        return "MissioRegular", "MissioRegular", True

    return "Helvetica", "Helvetica-Bold", False


REGULAR_FONT_NAME, BOLD_FONT_NAME, HAS_TURKISH_FONT = register_pdf_fonts()


def normalize_pdf_text(value: object) -> str:
    if value is None:
        return ""

    text = str(value)

    if HAS_TURKISH_FONT:
        return text

    return text.translate(TURKISH_TO_ASCII_TRANSLATION)


def to_local_datetime(value: Any) -> datetime | None:
    if value is None or not isinstance(value, datetime):
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(LOCAL_REPORT_TIMEZONE)


def format_date(value: object) -> str:
    if value is None:
        return "-"

    if hasattr(value, "strftime"):
        return value.strftime("%d.%m.%Y")

    return str(value)


def format_local_datetime(value: object) -> str:
    local_value = to_local_datetime(value)

    if local_value is None:
        return "-"

    return local_value.strftime("%d.%m.%Y %H:%M")


def get_closure_status_label(status: str) -> str:
    if status == "closed_with_issues":
        return "Sorunlu kapanış"

    if status in {"closed_clean", "closed"}:
        return "Temiz kapanış"

    return "Gün kapatıldı"


def get_task_status_label(status: str, requires_manager_approval: bool) -> str:
    if status == "assigned":
        return "Bekliyor"

    if status == "in_progress":
        return "Devam ediyor"

    if status == "rejected":
        return "Reddedildi"

    if status == "completed" and requires_manager_approval:
        return "Onay bekliyor"

    if status == "completed":
        return "Tamamlandı"

    if status == "approved":
        return "Onaylandı"

    if status == "cancelled":
        return "İptal"

    return status


def get_task_type_label(task_type: str) -> str:
    if task_type == "routine":
        return "Rutin"

    return "Ekstra"


def get_priority_label(priority: str) -> str:
    if priority == "low":
        return "Düşük"

    if priority == "high":
        return "Yüksek"

    if priority == "urgent":
        return "Acil"

    return "Normal"


def is_problem_item(item: DailyOperationClosureItem) -> bool:
    if item.task_status in {"assigned", "in_progress", "rejected"}:
        return True

    if item.task_status == "completed" and item.requires_manager_approval:
        return True

    if item.requires_photo and not item.has_photo_evidence:
        return True

    return False


def is_done_item(item: DailyOperationClosureItem) -> bool:
    if item.task_status == "approved":
        return True

    if item.task_status == "completed" and not item.requires_manager_approval:
        return True

    return False


def get_missing_photo_count(closure: DailyOperationClosure) -> int:
    return max(
        closure.photo_required_task_count - closure.photo_evidence_task_count,
        0,
    )


def get_issue_count(closure: DailyOperationClosure) -> int:
    return (
        closure.open_task_count
        + closure.rejected_task_count
        + closure.approval_pending_task_count
        + get_missing_photo_count(closure)
    )


def get_staff_name(item: DailyOperationClosureItem) -> str:
    return (
        item.assigned_to_user_full_name
        or item.assigned_to_username
        or "Personel yok"
    )


def get_requirement_text(item: DailyOperationClosureItem) -> str:
    requirements = []

    if item.requires_photo:
        requirements.append("Fotoğraf var" if item.has_photo_evidence else "Fotoğraf yok")

    if item.requires_location:
        requirements.append("Konum")

    if item.requires_manager_approval:
        requirements.append("Onay")

    return ", ".join(requirements) if requirements else "-"


def get_problem_reason_text(item: DailyOperationClosureItem) -> str:
    reasons = []

    if item.task_status in {"assigned", "in_progress"}:
        reasons.append("Açık iş")

    if item.task_status == "rejected":
        reasons.append("Red")

    if item.task_status == "completed" and item.requires_manager_approval:
        reasons.append("Onay bekliyor")

    if item.requires_photo and not item.has_photo_evidence:
        reasons.append("Fotoğraf yok")

    return ", ".join(reasons) if reasons else "-"


def build_staff_summary_rows(
    items: list[DailyOperationClosureItem],
) -> list[dict[str, object]]:
    summary: dict[str, dict[str, object]] = {}

    for item in items:
        name = get_staff_name(item)

        if name not in summary:
            summary[name] = {
                "name": name,
                "total": 0,
                "done": 0,
                "open": 0,
                "approval": 0,
                "rejected": 0,
                "missing_photo": 0,
            }

        row = summary[name]
        row["total"] = int(row["total"]) + 1

        if is_done_item(item):
            row["done"] = int(row["done"]) + 1

        if item.task_status in {"assigned", "in_progress"}:
            row["open"] = int(row["open"]) + 1

        if item.task_status == "completed" and item.requires_manager_approval:
            row["approval"] = int(row["approval"]) + 1

        if item.task_status == "rejected":
            row["rejected"] = int(row["rejected"]) + 1

        if item.requires_photo and not item.has_photo_evidence:
            row["missing_photo"] = int(row["missing_photo"]) + 1

    return sorted(summary.values(), key=lambda row: str(row["name"]))


def set_font(pdf: canvas.Canvas, *, bold: bool = False, size: float = 9, color=INK) -> None:
    pdf.setFont(BOLD_FONT_NAME if bold else REGULAR_FONT_NAME, size)
    pdf.setFillColor(color)


def draw_text(
    pdf: canvas.Canvas,
    text: object,
    x: float,
    y: float,
    *,
    size: float = 9,
    bold: bool = False,
    color=INK,
) -> None:
    set_font(pdf, bold=bold, size=size, color=color)
    pdf.drawString(x, y, normalize_pdf_text(text))


def draw_right_text(
    pdf: canvas.Canvas,
    text: object,
    x: float,
    y: float,
    *,
    size: float = 9,
    bold: bool = False,
    color=INK,
) -> None:
    set_font(pdf, bold=bold, size=size, color=color)
    pdf.drawRightString(x, y, normalize_pdf_text(text))


def draw_center_text(
    pdf: canvas.Canvas,
    text: object,
    x: float,
    y: float,
    *,
    size: float = 9,
    bold: bool = False,
    color=INK,
) -> None:
    set_font(pdf, bold=bold, size=size, color=color)
    pdf.drawCentredString(x, y, normalize_pdf_text(text))


def split_text_to_lines(
    pdf: canvas.Canvas,
    text: object,
    max_width: float,
    *,
    size: float,
    bold: bool = False,
    max_lines: int = 2,
) -> list[str]:
    normalized = normalize_pdf_text(text)
    words = normalized.split()

    if not words:
        return [""]

    pdf.setFont(BOLD_FONT_NAME if bold else REGULAR_FONT_NAME, size)

    lines: list[str] = []
    current_line = ""

    for word in words:
        candidate = word if not current_line else f"{current_line} {word}"

        if pdf.stringWidth(candidate, BOLD_FONT_NAME if bold else REGULAR_FONT_NAME, size) <= max_width:
            current_line = candidate
            continue

        if current_line:
            lines.append(current_line)

        current_line = word

        if len(lines) >= max_lines:
            break

    if len(lines) < max_lines and current_line:
        lines.append(current_line)

    if len(lines) > max_lines:
        lines = lines[:max_lines]

    if len(lines) == max_lines:
        original_words = normalized.split()
        rebuilt = " ".join(lines).replace("...", "")
        if len(rebuilt.split()) < len(original_words):
            last_line = lines[-1]
            while pdf.stringWidth(
                f"{last_line}...",
                BOLD_FONT_NAME if bold else REGULAR_FONT_NAME,
                size,
            ) > max_width and len(last_line) > 3:
                last_line = last_line[:-1].rstrip()

            lines[-1] = f"{last_line}..."

    return lines


def draw_wrapped_text(
    pdf: canvas.Canvas,
    text: object,
    x: float,
    y: float,
    max_width: float,
    *,
    size: float = 8,
    bold: bool = False,
    color=INK,
    line_height: float = 10,
    max_lines: int = 2,
) -> float:
    lines = split_text_to_lines(
        pdf,
        text,
        max_width,
        size=size,
        bold=bold,
        max_lines=max_lines,
    )

    for index, line in enumerate(lines):
        draw_text(
            pdf,
            line,
            x,
            y - (index * line_height),
            size=size,
            bold=bold,
            color=color,
        )

    return y - (len(lines) * line_height)


def draw_rounded_rect(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill_color,
    stroke_color,
    radius: float = 8,
    stroke_width: float = 0.8,
) -> None:
    pdf.setFillColor(fill_color)
    pdf.setStrokeColor(stroke_color)
    pdf.setLineWidth(stroke_width)
    pdf.roundRect(x, y, width, height, radius, stroke=1, fill=1)


def draw_logo(pdf: canvas.Canvas, x: float, y: float, size: float = 38) -> None:
    draw_rounded_rect(
        pdf,
        x,
        y,
        size,
        size,
        fill_color=colors.HexColor("#D9FBF7"),
        stroke_color=colors.HexColor("#A7F3D0"),
        radius=9,
    )

    pdf.saveState()

    pdf.setLineCap(1)
    pdf.setLineJoin(1)
    pdf.setLineWidth(5.0)

    left_x = x + size * 0.28
    mid_x = x + size * 0.50
    right_x = x + size * 0.73
    bottom_y = y + size * 0.25
    top_y = y + size * 0.72

    pdf.setStrokeColor(colors.HexColor("#22D3EE"))
    pdf.line(left_x, bottom_y, left_x, top_y)
    pdf.line(left_x, top_y, mid_x, bottom_y)

    pdf.setStrokeColor(colors.HexColor("#14B8A6"))
    pdf.line(mid_x, bottom_y, right_x, top_y)
    pdf.line(right_x, top_y, right_x, bottom_y)

    pdf.setFillColor(colors.HexColor("#8B5CF6"))
    pdf.circle(right_x + 4, top_y + 4, 3.2, stroke=0, fill=1)

    pdf.restoreState()


def draw_page_footer(pdf: canvas.Canvas, page_number: int) -> None:
    pdf.setFillColor(PASTEL_MINT)
    pdf.rect(0, 0, PAGE_WIDTH, 18, fill=1, stroke=0)

    pdf.setStrokeColor(PASTEL_MINT_LINE)
    pdf.setLineWidth(0.5)
    pdf.line(0, 18, PAGE_WIDTH, 18)

    draw_text(
        pdf,
        "Missio - Gün sonu operasyon raporu",
        MARGIN_X,
        7,
        size=7,
        color=MUTED,
    )
    draw_right_text(
        pdf,
        f"Sayfa {page_number}",
        PAGE_WIDTH - MARGIN_X,
        7,
        size=7,
        color=MUTED,
    )


def draw_header(
    pdf: canvas.Canvas,
    *,
    closure: DailyOperationClosure,
    business: Business,
) -> float:
    header_height = 72
    y = TOP_Y - header_height

    draw_rounded_rect(
        pdf,
        MARGIN_X,
        y,
        PAGE_WIDTH - (2 * MARGIN_X),
        header_height,
        fill_color=PASTEL_MINT,
        stroke_color=PASTEL_MINT_LINE,
        radius=10,
    )

    draw_logo(pdf, MARGIN_X + 12, y + 17, size=38)

    draw_text(pdf, "Missio", MARGIN_X + 58, y + 47, size=18, bold=True)
    draw_text(pdf, "Operasyon raporu", MARGIN_X + 58, y + 31, size=8.5, color=MUTED)

    draw_text(pdf, "Gün Sonu Operasyon Raporu", MARGIN_X + 160, y + 49, size=14, bold=True)
    draw_text(
        pdf,
        f"İşletme: {business.name} | Rapor tarihi: {format_date(closure.closure_date)}",
        MARGIN_X + 160,
        y + 32,
        size=8.2,
        color=MUTED,
    )
    draw_text(
        pdf,
        f"Kapatan: {closure.closed_by_user_full_name} (@{closure.closed_by_username})",
        MARGIN_X + 160,
        y + 18,
        size=8.2,
        color=MUTED,
    )
    draw_text(
        pdf,
        f"Yerel saat: {format_local_datetime(closure.closed_at_utc)}",
        MARGIN_X + 160,
        y + 6,
        size=8.2,
        color=MUTED,
    )

    status_fill, status_line = (
        (PASTEL_AMBER, PASTEL_AMBER_LINE)
        if closure.status == "closed_with_issues"
        else (PASTEL_GREEN, PASTEL_GREEN_LINE)
    )

    status_width = 112
    status_height = 46
    status_x = PAGE_WIDTH - MARGIN_X - status_width - 12
    status_y = y + 13

    draw_rounded_rect(
        pdf,
        status_x,
        status_y,
        status_width,
        status_height,
        fill_color=status_fill,
        stroke_color=status_line,
        radius=7,
    )
    draw_text(pdf, get_closure_status_label(closure.status), status_x + 11, status_y + 28, size=9, bold=True)
    draw_text(
        pdf,
        "Sorunsuz tamamlandı"
        if closure.status != "closed_with_issues"
        else "Kontrol gerekli",
        status_x + 11,
        status_y + 12,
        size=7.4,
        color=MUTED,
    )

    return y - 12


def draw_kpi_cards(pdf: canvas.Canvas, *, closure: DailyOperationClosure, y: float) -> float:
    issue_count = get_issue_count(closure)

    cards = [
        ("TOPLAM GÖREV", closure.total_task_count, PASTEL_BLUE, PASTEL_BLUE_LINE),
        ("TAMAMLANAN", closure.completed_task_count, PASTEL_GREEN, PASTEL_GREEN_LINE),
        ("ONAY BEKLEYEN", closure.approval_pending_task_count, PASTEL_PURPLE, PASTEL_PURPLE_LINE),
        ("REDDEDİLEN", closure.rejected_task_count, PASTEL_ROSE, PASTEL_ROSE_LINE),
        (
            "DİKKAT BAŞLIĞI",
            issue_count,
            PASTEL_AMBER if issue_count > 0 else PASTEL_TEAL,
            PASTEL_AMBER_LINE if issue_count > 0 else PASTEL_MINT_LINE,
        ),
    ]

    gap = 7
    card_width = ((PAGE_WIDTH - (2 * MARGIN_X)) - (gap * 4)) / 5
    card_height = 38
    x = MARGIN_X

    for label, value, fill, stroke in cards:
        draw_rounded_rect(
            pdf,
            x,
            y - card_height,
            card_width,
            card_height,
            fill_color=fill,
            stroke_color=stroke,
            radius=6,
        )
        draw_center_text(pdf, value, x + (card_width / 2), y - 15, size=16, bold=True)
        draw_center_text(pdf, label, x + (card_width / 2), y - 29, size=6.3, bold=True, color=MUTED)
        x += card_width + gap

    return y - card_height - 12


def draw_status_box(pdf: canvas.Canvas, *, closure: DailyOperationClosure, y: float) -> float:
    issue_count = get_issue_count(closure)

    if closure.status == "closed_with_issues":
        fill = PASTEL_AMBER
        stroke = PASTEL_AMBER_LINE
        description = f"Bu gün sorunlu kapatıldı. Toplam {issue_count} dikkat başlığı rapora ayrıştırıldı."
    else:
        fill = PASTEL_GREEN
        stroke = PASTEL_GREEN_LINE
        description = "Bu gün temiz kapatıldı. Açık iş, red, onay bekleyen görev veya eksik fotoğraf uyarısı görünmüyor."

    height = 52
    left_width = PAGE_WIDTH - (2 * MARGIN_X) - 118

    draw_rounded_rect(
        pdf,
        MARGIN_X,
        y - height,
        PAGE_WIDTH - (2 * MARGIN_X),
        height,
        fill_color=fill,
        stroke_color=stroke,
        radius=7,
    )

    draw_text(pdf, "KAPANIŞ KARARI", MARGIN_X + 12, y - 16, size=7, bold=True, color=MUTED)
    draw_text(pdf, get_closure_status_label(closure.status), MARGIN_X + 12, y - 31, size=12, bold=True)
    draw_wrapped_text(
        pdf,
        description,
        MARGIN_X + 12,
        y - 43,
        left_width - 18,
        size=7.6,
        color=INK,
        line_height=9,
        max_lines=2,
    )

    separator_x = MARGIN_X + left_width
    pdf.setStrokeColor(stroke)
    pdf.setLineWidth(0.8)
    pdf.line(separator_x, y - height, separator_x, y)

    draw_center_text(pdf, issue_count, separator_x + 59, y - 22, size=17, bold=True)
    draw_center_text(pdf, "Dikkat başlığı", separator_x + 59, y - 37, size=6.7, bold=True, color=MUTED)

    return y - height - 14


def draw_section_title(pdf: canvas.Canvas, title: str, y: float) -> float:
    draw_text(pdf, title, MARGIN_X, y, size=11.2, bold=True)
    return y - 12


def draw_empty_info_box(pdf: canvas.Canvas, text: str, y: float, *, fill, stroke) -> float:
    height = 32
    draw_rounded_rect(
        pdf,
        MARGIN_X,
        y - height,
        PAGE_WIDTH - (2 * MARGIN_X),
        height,
        fill_color=fill,
        stroke_color=stroke,
        radius=6,
    )
    draw_text(pdf, text, MARGIN_X + 12, y - 20, size=8, bold=True)
    return y - height - 14


def ensure_space(pdf: canvas.Canvas, y: float, needed_height: float, page_number: int) -> tuple[float, int]:
    if y - needed_height >= BOTTOM_Y + 20:
        return y, page_number

    draw_page_footer(pdf, page_number)
    pdf.showPage()
    page_number += 1
    return TOP_Y, page_number


def draw_table_header(
    pdf: canvas.Canvas,
    y: float,
    columns: list[tuple[str, float]],
    *,
    fill,
    stroke,
) -> float:
    row_height = 22
    x = MARGIN_X

    pdf.setFillColor(fill)
    pdf.setStrokeColor(stroke)
    pdf.setLineWidth(0.6)
    pdf.rect(MARGIN_X, y - row_height, sum(width for _, width in columns), row_height, fill=1, stroke=1)

    for title, width in columns:
        draw_center_text(pdf, title, x + (width / 2), y - 14, size=6.8, bold=True)
        pdf.setStrokeColor(stroke)
        pdf.line(x, y - row_height, x, y)
        x += width

    pdf.line(x, y - row_height, x, y)

    return y - row_height


def draw_table_row(
    pdf: canvas.Canvas,
    y: float,
    values: list[object],
    columns: list[tuple[str, float]],
    *,
    fill,
    stroke,
    row_height: float,
    bold_columns: set[int] | None = None,
    center_columns: set[int] | None = None,
) -> float:
    bold_columns = bold_columns or set()
    center_columns = center_columns or set()

    total_width = sum(width for _, width in columns)
    pdf.setFillColor(fill)
    pdf.setStrokeColor(stroke)
    pdf.setLineWidth(0.45)
    pdf.rect(MARGIN_X, y - row_height, total_width, row_height, fill=1, stroke=1)

    x = MARGIN_X

    for index, ((_, width), value) in enumerate(zip(columns, values)):
        pdf.setStrokeColor(stroke)
        pdf.line(x, y - row_height, x, y)

        if index in center_columns:
            draw_center_text(
                pdf,
                value,
                x + (width / 2),
                y - 15,
                size=6.8,
                bold=index in bold_columns,
            )
        else:
            draw_wrapped_text(
                pdf,
                value,
                x + 5,
                y - 10,
                width - 10,
                size=6.7,
                bold=index in bold_columns,
                line_height=8.2,
                max_lines=2,
            )

        x += width

    pdf.line(x, y - row_height, x, y)

    return y - row_height


def draw_problem_items(
    pdf: canvas.Canvas,
    *,
    problem_items: list[DailyOperationClosureItem],
    y: float,
    page_number: int,
) -> tuple[float, int]:
    y, page_number = ensure_space(pdf, y, 58, page_number)
    y = draw_section_title(pdf, "Dikkat Gerektiren İşler", y)

    if not problem_items:
        y = draw_empty_info_box(
            pdf,
            "Kontrol gerektiren iş yok. Bu kapanışta sorunlu görev görünmüyor.",
            y,
            fill=PASTEL_GREEN,
            stroke=PASTEL_GREEN_LINE,
        )
        return y, page_number

    columns = [
        ("Personel", 95),
        ("Görev", 210),
        ("Durum", 86),
        ("Sebep", 102),
    ]

    y, page_number = ensure_space(pdf, y, 44, page_number)
    y = draw_table_header(pdf, y, columns, fill=PASTEL_AMBER, stroke=PASTEL_AMBER_LINE)

    for item in problem_items:
        y, page_number = ensure_space(pdf, y, 30, page_number)
        y = draw_table_row(
            pdf,
            y,
            [
                get_staff_name(item),
                item.task_title,
                get_task_status_label(item.task_status, item.requires_manager_approval),
                get_problem_reason_text(item),
            ],
            columns,
            fill=colors.HexColor("#FFFBEB"),
            stroke=PASTEL_AMBER_LINE,
            row_height=30,
            bold_columns={1},
        )

    y -= 12

    return y, page_number


def draw_staff_summary(
    pdf: canvas.Canvas,
    *,
    items: list[DailyOperationClosureItem],
    y: float,
    page_number: int,
) -> tuple[float, int]:
    y, page_number = ensure_space(pdf, y, 80, page_number)
    y = draw_section_title(pdf, "Personel Performans Özeti", y)

    columns = [
        ("Personel", 167),
        ("Toplam", 60),
        ("Tamam", 60),
        ("Açık", 60),
        ("Onay", 60),
        ("Red", 60),
        ("Fotoğraf", 60),
    ]

    y = draw_table_header(pdf, y, columns, fill=PASTEL_TEAL, stroke=PASTEL_MINT_LINE)

    rows = build_staff_summary_rows(items)

    if not rows:
        y = draw_table_row(
            pdf,
            y,
            ["Personel özeti bulunamadı.", "", "", "", "", "", ""],
            columns,
            fill=WHITE,
            stroke=LINE,
            row_height=26,
            bold_columns={0},
        )
        return y - 12, page_number

    for row in rows:
        y, page_number = ensure_space(pdf, y, 25, page_number)
        y = draw_table_row(
            pdf,
            y,
            [
                row["name"],
                row["total"],
                row["done"],
                row["open"],
                row["approval"],
                row["rejected"],
                row["missing_photo"],
            ],
            columns,
            fill=WHITE,
            stroke=colors.HexColor("#CCFBF1"),
            row_height=25,
            bold_columns={0},
            center_columns={0, 1, 2, 3, 4, 5, 6},
        )

    return y - 14, page_number


def draw_task_list(
    pdf: canvas.Canvas,
    *,
    items: list[DailyOperationClosureItem],
    y: float,
    page_number: int,
) -> tuple[float, int]:
    y, page_number = ensure_space(pdf, y, 86, page_number)
    y = draw_section_title(pdf, "Kapanış Anındaki Görev Listesi", y)

    columns = [
        ("#", 24),
        ("Personel", 86),
        ("Görev", 168),
        ("Tip", 54),
        ("Durum", 74),
        ("Öncelik", 55),
        ("Şartlar", 66),
    ]

    y = draw_table_header(pdf, y, columns, fill=PASTEL_BLUE, stroke=PASTEL_BLUE_LINE)

    if not items:
        y = draw_table_row(
            pdf,
            y,
            ["", "Bu raporda görev satırı bulunamadı.", "", "", "", "", ""],
            columns,
            fill=WHITE,
            stroke=LINE,
            row_height=28,
            bold_columns={1},
        )
        return y - 12, page_number

    for index, item in enumerate(items, start=1):
        y, page_number = ensure_space(pdf, y, 31, page_number)

        if is_problem_item(item):
            fill = colors.HexColor("#FFFBEB")
        elif is_done_item(item):
            fill = colors.HexColor("#F0FDF4")
        else:
            fill = WHITE

        y = draw_table_row(
            pdf,
            y,
            [
                index,
                get_staff_name(item),
                item.task_title,
                get_task_type_label(item.task_type),
                get_task_status_label(item.task_status, item.requires_manager_approval),
                get_priority_label(item.task_priority),
                get_requirement_text(item),
            ],
            columns,
            fill=fill,
            stroke=colors.HexColor("#DBEAFE"),
            row_height=31,
            bold_columns={2},
            center_columns={0},
        )

    return y - 10, page_number


def draw_manager_note(
    pdf: canvas.Canvas,
    *,
    closure: DailyOperationClosure,
    y: float,
    page_number: int,
) -> tuple[float, int]:
    if not closure.manager_note:
        return y, page_number

    y, page_number = ensure_space(pdf, y, 54, page_number)

    box_height = 48
    draw_rounded_rect(
        pdf,
        MARGIN_X,
        y - box_height,
        PAGE_WIDTH - (2 * MARGIN_X),
        box_height,
        fill_color=colors.HexColor("#F0FDFA"),
        stroke_color=PASTEL_MINT_LINE,
        radius=7,
    )

    draw_text(pdf, "YÖNETİCİ KAPANIŞ NOTU", MARGIN_X + 12, y - 16, size=7, bold=True, color=MUTED)
    draw_wrapped_text(
        pdf,
        closure.manager_note,
        MARGIN_X + 12,
        y - 30,
        PAGE_WIDTH - (2 * MARGIN_X) - 24,
        size=7.8,
        line_height=9,
        max_lines=2,
    )

    return y - box_height - 12, page_number


def build_daily_operation_closure_pdf_bytes(
    *,
    closure: DailyOperationClosure,
    items: list[DailyOperationClosureItem],
    business: Business,
) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    page_number = 1

    pdf.setTitle(normalize_pdf_text(f"Missio Gün Sonu Raporu - {format_date(closure.closure_date)}"))

    y = draw_header(pdf, closure=closure, business=business)
    y = draw_kpi_cards(pdf, closure=closure, y=y)
    y = draw_status_box(pdf, closure=closure, y=y)
    y, page_number = draw_manager_note(pdf, closure=closure, y=y, page_number=page_number)

    problem_items = [item for item in items if is_problem_item(item)]

    y, page_number = draw_problem_items(
        pdf,
        problem_items=problem_items,
        y=y,
        page_number=page_number,
    )

    y, page_number = draw_staff_summary(
        pdf,
        items=items,
        y=y,
        page_number=page_number,
    )

    y, page_number = draw_task_list(
        pdf,
        items=items,
        y=y,
        page_number=page_number,
    )

    y, page_number = ensure_space(pdf, y, 28, page_number)

    draw_wrapped_text(
        pdf,
        "Bu PDF, gün kapatma anındaki snapshot verisinden anlık olarak üretilmiştir. PDF dosyası ayrıca arşivlenmez.",
        MARGIN_X,
        y,
        PAGE_WIDTH - (2 * MARGIN_X),
        size=7.2,
        color=MUTED,
        line_height=9,
        max_lines=2,
    )

    draw_page_footer(pdf, page_number)
    pdf.save()

    return buffer.getvalue()
