from io import BytesIO

import xlsxwriter

from app.services.gap_report_service import GapReportService


class GapReportExportService:
    def __init__(self, db):
        self.report_service = GapReportService(db)

    def export(self, start_date, end_date):
        report = self.report_service.report(start_date, end_date)
        output = BytesIO()
        with xlsxwriter.Workbook(output, {
            "in_memory": True, "strings_to_formulas": False, "strings_to_urls": False,
        }) as workbook:
            sheet = workbook.add_worksheet("Relatório de GAP")
            header = workbook.add_format({"bold": True, "bg_color": "#253449", "font_color": "white"})
            dates = workbook.add_format({"num_format": "dd/mm/yyyy"})
            note_format = workbook.add_format({"text_wrap": True, "valign": "top"})
            sheet.write_row(0, 0, [
                "ECO", "Owner", "Effective Date", "Approval Date", "GAP 14D",
                "Comentário / Justificativa",
            ], header)
            sheet.set_column(0, 1, 24)
            sheet.set_column(2, 3, 18)
            sheet.set_column(4, 4, 12)
            sheet.set_column(5, 5, 65, note_format)
            sheet.freeze_panes(1, 0)
            for index, item in enumerate(report.items, start=1):
                sheet.write(index, 0, item.eco)
                sheet.write(index, 1, item.owner)
                if item.effective_date is not None:
                    sheet.write_datetime(index, 2, item.effective_date, dates)
                sheet.write_datetime(index, 3, item.approval_date, dates)
                if item.gap_14d is not None:
                    sheet.write_number(index, 4, item.gap_14d)
                sheet.write(index, 5, item.gap_14d_note, note_format)
            sheet.autofilter(0, 0, len(report.items), 5)
        return output.getvalue()
