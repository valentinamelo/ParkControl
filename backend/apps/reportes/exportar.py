"""Exporta el reporte de ingresos a PDF (ReportLab) y Excel (openpyxl), RF-22."""
from io import BytesIO

from django.utils import timezone
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

NEGRO = "111111"
AMARILLO = "F5C400"
FORMATO_PESOS = '"$"#,##0'


def pesos(valor):
    return "$" + f"{valor:,.0f}".replace(",", ".")


def titulo(parqueadero, reporte):
    return f"Reporte de ingresos · {parqueadero.nombre}", (
        f"Del {reporte['desde']:%d/%m/%Y} al {reporte['hasta']:%d/%m/%Y} · "
        f"generado el {timezone.localtime():%d/%m/%Y %I:%M %p}"
    )


# --- PDF ---

def _tabla_pdf(encabezado, filas, anchos, alinear_derecha=()):
    tabla = Table([encabezado, *filas], colWidths=anchos, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(f"#{NEGRO}")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(f"#{AMARILLO}")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E6E6E6")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for col in alinear_derecha:
        estilo.append(("ALIGN", (col, 0), (col, -1), "RIGHT"))
    tabla.setStyle(TableStyle(estilo))
    return tabla


def _grupo_pdf(nombre, grupos):
    filas = [[g["nombre"], str(g["cantidad"]), pesos(g["total"])] for g in grupos] or [["Sin ingresos", "", ""]]
    return _tabla_pdf([nombre, "Pagos", "Total"], filas, [7 * cm, 2.5 * cm, 3.5 * cm], alinear_derecha=(1, 2))


def reporte_pdf(reporte, parqueadero, filtros_texto):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm,
        title="Reporte de ingresos", author=parqueadero.nombre,
    )
    estilos = getSampleStyleSheet()
    nombre, subtitulo = titulo(parqueadero, reporte)
    h2 = estilos["Heading3"]
    historia = [
        Paragraph(nombre, estilos["Title"]),
        Paragraph(subtitulo, estilos["Normal"]),
    ]
    if filtros_texto:
        historia.append(Paragraph(f"Filtros: {filtros_texto}", estilos["Normal"]))
    historia += [
        Spacer(1, 0.4 * cm),
        _tabla_pdf(
            ["Total recaudado", "Pagos"],
            [[pesos(reporte["total"]), str(reporte["cantidad"])]],
            [8 * cm, 5 * cm],
        ),
    ]
    for titulo_grupo, clave, columna in [
        ("Por método de pago", "por_metodo", "Método"),
        ("Por tipo de vehículo", "por_tipo", "Tipo"),
        ("Por concepto", "por_concepto", "Concepto"),
        ("Por trabajador", "por_usuario", "Trabajador"),
    ]:
        historia += [Paragraph(titulo_grupo, h2), _grupo_pdf(columna, reporte[clave])]

    historia += [
        Paragraph("Por día", h2),
        _tabla_pdf(
            ["Fecha", "Pagos", "Total"],
            [[f"{d['fecha']:%d/%m/%Y}", str(d["cantidad"]), pesos(d["total"])] for d in reporte["por_dia"]],
            [7 * cm, 2.5 * cm, 3.5 * cm],
            alinear_derecha=(1, 2),
        ),
        Paragraph("Detalle de pagos", h2),
        _tabla_pdf(
            ["Fecha", "Concepto", "Ref.", "Placa", "Tipo", "Método", "Registró", "Valor"],
            [
                [f"{f['fecha']:%d/%m %I:%M %p}", f["concepto"], f["referencia"], f["placa"], f["tipo_vehiculo"],
                 f["metodo"], f["usuario"], pesos(f["valor"])]
                for f in reporte["detalle"]
            ] or [["Sin pagos en el rango", "", "", "", "", "", "", ""]],
            [2.6 * cm, 2 * cm, 2.2 * cm, 1.6 * cm, 1.4 * cm, 2 * cm, 3 * cm, 2 * cm],
            alinear_derecha=(7,),
        ),
    ]
    doc.build(historia)
    return buffer.getvalue()


# --- Excel ---

def _encabezado_xlsx(hoja, columnas, fila=1):
    for i, texto in enumerate(columnas, start=1):
        celda = hoja.cell(row=fila, column=i, value=texto)
        celda.font = Font(bold=True, color=AMARILLO)
        celda.fill = PatternFill("solid", fgColor=NEGRO)
        celda.alignment = Alignment(horizontal="center")


def _anchos(hoja, anchos):
    for i, ancho in enumerate(anchos, start=1):
        hoja.column_dimensions[get_column_letter(i)].width = ancho


def reporte_xlsx(reporte, parqueadero, filtros_texto):
    libro = Workbook()
    nombre, subtitulo = titulo(parqueadero, reporte)

    resumen = libro.active
    resumen.title = "Resumen"
    resumen["A1"] = nombre
    resumen["A1"].font = Font(bold=True, size=14)
    resumen["A2"] = subtitulo
    resumen["A3"] = f"Filtros: {filtros_texto}" if filtros_texto else ""
    resumen["A5"], resumen["B5"] = "Total recaudado", reporte["total"]
    resumen["A6"], resumen["B6"] = "Pagos", reporte["cantidad"]
    resumen["A5"].font = resumen["A6"].font = Font(bold=True)
    resumen["B5"].number_format = FORMATO_PESOS
    fila = 8
    for titulo_grupo, clave in [
        ("Método de pago", "por_metodo"), ("Tipo de vehículo", "por_tipo"),
        ("Concepto", "por_concepto"), ("Trabajador", "por_usuario"),
    ]:
        _encabezado_xlsx(resumen, [titulo_grupo, "Pagos", "Total"], fila)
        for g in reporte[clave]:
            fila += 1
            resumen.cell(row=fila, column=1, value=g["nombre"])
            resumen.cell(row=fila, column=2, value=g["cantidad"])
            resumen.cell(row=fila, column=3, value=g["total"]).number_format = FORMATO_PESOS
        fila += 2
    _anchos(resumen, [28, 12, 16])

    por_dia = libro.create_sheet("Por día")
    _encabezado_xlsx(por_dia, ["Fecha", "Pagos", "Total"])
    for i, d in enumerate(reporte["por_dia"], start=2):
        por_dia.cell(row=i, column=1, value=d["fecha"]).number_format = "DD/MM/YYYY"
        por_dia.cell(row=i, column=2, value=d["cantidad"])
        por_dia.cell(row=i, column=3, value=d["total"]).number_format = FORMATO_PESOS
    _anchos(por_dia, [14, 10, 16])

    detalle = libro.create_sheet("Detalle")
    _encabezado_xlsx(detalle, ["Fecha", "Concepto", "Referencia", "Placa", "Tipo", "Método", "Registró", "Valor"])
    for i, f in enumerate(reporte["detalle"], start=2):
        valores = [f["fecha"].replace(tzinfo=None), f["concepto"], f["referencia"], f["placa"], f["tipo_vehiculo"],
                   f["metodo"], f["usuario"], f["valor"]]
        for j, valor in enumerate(valores, start=1):
            detalle.cell(row=i, column=j, value=valor)
        detalle.cell(row=i, column=1).number_format = "DD/MM/YYYY HH:MM"
        detalle.cell(row=i, column=8).number_format = FORMATO_PESOS
    if reporte["detalle"]:
        total = len(reporte["detalle"]) + 2
        detalle.cell(row=total, column=7, value="Total").font = Font(bold=True)
        celda = detalle.cell(row=total, column=8, value=f"=SUM(H2:H{total - 1})")
        celda.font = Font(bold=True)
        celda.number_format = FORMATO_PESOS
    detalle.freeze_panes = "A2"
    _anchos(detalle, [18, 14, 18, 10, 10, 15, 24, 14])

    buffer = BytesIO()
    libro.save(buffer)
    return buffer.getvalue()
