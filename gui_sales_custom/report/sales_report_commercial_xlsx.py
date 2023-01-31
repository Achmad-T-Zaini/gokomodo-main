# Copyright 2019 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import (
    FORMATS,
    XLS_HEADERS,
)


class ReportSDTReportXlsx(models.AbstractModel):
    _inherit = "report.sdt_report_sales.report_sdt_report_xlsx"

    def _get_ws_params(self, wb, data):
        filter_template = {
            "1_date_from": {
                "header": {"value": "Date from"},
                "data": {
                    "value": self._render("date_from"),
                    "format": FORMATS["format_tcell_date_center"],
                },
            },
            "2_date_to": {
                "header": {"value": "Date to"},
                "data": {
                    "value": self._render("date_to"),
                    "format": FORMATS["format_tcell_date_center"],
                },
            },
            # "3_analytic_type": {
            #     "header": {"value": "Analytic Type"},
            #     "data": {
            #         "value": self._render("analytic_type"),
            #         "format": FORMATS["format_tcell_center"],
            #     },
            # },
        }
        stock_card_template = {
            "1_sale_id": {
                "header": {"value": "Order"},
                "data": {
                    "value": self._render("sale_id"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 15,
            },
            "2_customer": {
                "header": {"value": "Customer"},
                "data": {
                    "value": self._render("customer"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 50,
            },
            "3_provinsi": {
                "header": {"value": "Provinsi"},
                "data": {
                    "value": self._render("provinsi"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 15,
            },
            "4_sales": {
                "header": {"value": "Sales"},
                "data": {
                    "value": self._render("sales"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 20,
            },
            "5_order_type": {
                "header": {"value": "Order Type"},
                "data": {
                    "value": self._render("order_type"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 15,
            },
            "6_route": {
                "header": {"value": "Route"},
                "data": {
                    "value": self._render("route"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 15,
            },
            "6_status": {
                "header": {"value": "Status"},
                "data": {
                    "value": self._render("status"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 15,
            },
            "7_product_id": {
                "header": {"value": "Product"},
                "data": {
                    "value": self._render("product_id"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 50,
            },
            "8_qty_order": {
                "header": {"value": "Qty Order"},
                "data": {"value": self._render("qty_order")},
                "width": 15,
            },
            "9_product_uom_id": {
                "header": {"value": "UoM"},
                "data": {
                    "value": self._render("product_uom_id"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 10,
            },
            "10_price_unit": {
                "header": {"value": "Price"},
                "data": {"value": self._render("price_unit")},
                "width": 15,
            },
            "10_total_sales": {
                "header": {"value": "Total Sales"},
                "data": {"value": self._render("total_sales")},
                "width": 15,
            },
            "11_sale_margin": {
                "header": {"value": "Margin"},
                "data": {"value": self._render("sale_margin")},
                "width": 15,
            },
            "12_sale_margin2cost": {
                "header": {"value": "Margin to Cost(%)"},
                "data": {"value": self._render("sale_margin2cost")},
                "width": 15,
            },
            "13_sale_margin2sale": {
                "header": {"value": "Margin to Sale(%)"},
                "data": {"value": self._render("sale_margin2sale")},
                "width": 15,
            },
            "14_delivered": {
                "header": {"value": "Delivery"},
                "data": {
                    "value": self._render("delivered"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 25,
            },
            "15_qty_delivered": {
                "header": {"value": "Qty Delivery"},
                "data": {"value": self._render("qty_delivered")},
                "width": 15,
            },
            "16_invoice": {
                "header": {"value": "Invoice"},
                "data": {
                    "value": self._render("invoice"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 25,
            },
            "17_qty_invoice": {
                "header": {"value": "Qty Invoice"},
                "data": {"value": self._render("qty_invoice")},
                "width": 15,
            },
            "18_credit_note": {
                "header": {"value": "Credit Note"},
                "data": {
                    "value": self._render("credit_note"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 25,
            },
            "19_qty_credit_note": {
                "header": {"value": "Qty CN"},
                "data": {"value": self._render("qty_credit_note")},
                "width": 15,
            },
            "20_request": {
                "header": {"value": "Request"},
                "data": {
                    "value": self._render("request"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 25,
            },
            "21_qty_request": {
                "header": {"value": "Qty Request"},
                "data": {"value": self._render("qty_request")},
                "width": 15,
            },
            "22_purchase": {
                "header": {"value": "Purchase"},
                "data": {
                    "value": self._render("purchase"),
                    "format": FORMATS["format_tcell_date_left"],
                    },
                "width": 25,
            },
            "23_qty_purchase": {
                "header": {"value": "Qty Purchase"},
                "data": {"value": self._render("qty_purchase")},
                "width": 15,
            },
            "24_received": {
                "header": {"value": "Received"},
                "data": {
                    "value": self._render("received"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 25,
            },
            "25_sale_cost": {
                "header": {"value": "Cost"},
                "data": {"value": self._render("sale_cost")},
                "width": 15,
            },
            "26_qty_received": {
                "header": {"value": "Qty Received"},
                "data": {"value": self._render("qty_received")},
                "width": 15,
            },
            "27_bill": {
                "header": {"value": "Bill"},
                "data": {
                    "value": self._render("bill"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 25,
            },
            "28_qty_bill": {
                "header": {"value": "Qty Bill"},
                "data": {"value": self._render("qty_bill")},
                "width": 15,
            },
            "29_refund": {
                "header": {"value": "Refund"},
                "data": {
                    "value": self._render("refund"),
                    "format": FORMATS["format_tcell_date_left"],
                },
                "width": 25,
            },
            "30_qty_refund": {
                "header": {"value": "Qty Refund"},
                "data": {"value": self._render("qty_refund")},
                "width": 15,
            },
        }

        ws_params = {
            "ws_name": "Report Sales",
            "generate_ws_method": "_sdt_report",
            # "title": "SDT Report Summary - {}".format(analytic.name),
            "title": "Report Sales Gokomodo",
            "wanted_list_filter": [k for k in sorted(filter_template.keys())],
            "col_specs_filter": filter_template,
            "wanted_list": [k for k in stock_card_template.keys()],
            "col_specs": stock_card_template,
        }
        return [ws_params]

    def _sdt_report(self, wb, ws, ws_params, data, objects):
        ws.set_portrait()
        ws.fit_to_pages(1, 0)
        ws.set_header(XLS_HEADERS["xls_headers"]["standard"])
        ws.set_footer(XLS_HEADERS["xls_footers"]["standard"])
        self._set_column_width(ws, ws_params)
        # Title
        row_pos = 0
        row_pos = self._write_ws_title(ws, row_pos, ws_params, True)
        # Filter Table
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=FORMATS["format_theader_blue_center"],
            col_specs="col_specs_filter",
            wanted_list="wanted_list_filter",
        )
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="data",
            render_space={
                "date_from": objects.date_from or "",
                "date_to": objects.date_to or "",
            },
            col_specs="col_specs_filter",
            wanted_list="wanted_list_filter",
        )
        row_pos += 1
        # Stock Card Table
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="header",
            default_format=FORMATS["format_theader_blue_center"],
        )
        ws.freeze_panes(row_pos, 0)

        total_sales = 0.00
        total_qty_order = 0.00
        total_qty_delivered = 0.00
        total_qty_invoice = 0.00
        total_qty_credit_note = 0.00
        total_qty_request = 0.00
        total_qty_purchase = 0.00
        total_qty_received = 0.00
        total_qty_bill = 0.00
        total_qty_refund = 0.00

        for line in objects.results:
            total_sales = total_sales + (line.qty_order * line.price_unit)
            total_qty_order = total_qty_order + line.qty_order
            total_qty_delivered = total_qty_delivered + line.qty_delivered
            total_qty_invoice = total_qty_invoice + line.qty_invoice
            total_qty_credit_note = total_qty_credit_note + line.qty_credit_note
            total_qty_request = total_qty_request + line.qty_request
            total_qty_purchase = total_qty_purchase + line.qty_purchase
            total_qty_received = total_qty_received + line.qty_received
            total_qty_bill = total_qty_bill + line.qty_bill
            total_qty_refund = total_qty_refund + line.qty_refund

            row_pos = self._write_line(
                ws,
                row_pos,
                ws_params,
                col_specs_section="data",
                render_space={
                    'sale_id': line.sale_id.name,
                    'customer': line.customer,
                    'provinsi': line.provinsi,
                    'sales': line.sales,
                    'order_type': line.order_type,
                    'route': line.route,
                    'status': line.status,
                    'product_id': line.product_id.name,
                    'qty_order': line.qty_order,
                    'product_uom_id': line.product_uom_id.name,
                    'price_unit': line.price_unit,
                    'total_sales': line.qty_order * line.price_unit,
                    'sale_margin': line.sale_margin,
                    'sale_margin2cost': line.sale_margin2cost,
                    'sale_margin2sale': line.sale_margin2sale,
                    'delivered': line.delivered,
                    'qty_delivered': line.qty_delivered,
                    'invoice': line.invoice,
                    'qty_invoice': line.qty_invoice,
                    'credit_note': line.credit_note,
                    'qty_credit_note': line.qty_credit_note,
                    'request': line.request,
                    'qty_request': line.qty_request,
                    'purchase': line.purchase,
                    'qty_purchase': line.qty_purchase,
                    'received': line.received,
                    'sale_cost': line.sale_cost,
                    'qty_received': line.qty_received,
                    'bill': line.bill,
                    'qty_bill': line.qty_bill,
                    'refund': line.refund,
                    'qty_refund': line.qty_refund,
                },
                default_format=FORMATS["format_tcell_amount_right"],
            )
        
        row_pos = self._write_line(
            ws,
            row_pos,
            ws_params,
            col_specs_section="data",
            render_space={
                'sale_id': 'TOTAL',
                'customer': '',
                'provinsi': '',
                'sales': '',
                'order_type': '',
                'route': '',
                'status': '',
                'product_id': '',
                'qty_order': total_qty_order,
                'product_uom_id': '',
                'price_unit': '',
                'total_sales': total_sales,
                'sale_margin': '',
                'sale_margin2cost': '',
                'sale_margin2sale': '',
                'delivered': '',
                'qty_delivered': total_qty_delivered,
                'invoice': '',
                'qty_invoice': total_qty_invoice,
                'credit_note': '',
                'qty_credit_note': total_qty_credit_note,
                'request': '',
                'qty_request': total_qty_request,
                'purchase': '',
                'qty_purchase': total_qty_purchase,
                'received': '',
                'sale_cost': '',
                'qty_received': total_qty_received,
                'bill': '',
                'qty_bill': total_qty_bill,
                'refund': '',
                'qty_refund': total_qty_refund,
            },
            default_format=FORMATS["format_theader_blue_right"],
        )
