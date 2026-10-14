from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import matplotlib
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak

from app.model import VARIABLES, PERTURBATIONS, equation_text
from app.utils.constants import Constants


def create_pdf(data, calculation_id):
    font_dir = Path(matplotlib.get_data_path()) / 'fonts/ttf'
    for name, filename in [('Company', 'DejaVuSans.ttf'), ('CompanyBold', 'DejaVuSans-Bold.ttf')]:
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
    pdfmetrics.registerFontFamily('Company', normal='Company', bold='CompanyBold', italic='Company', boldItalic='CompanyBold')
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = 'Company'
    styles['BodyText'].fontSize = 9
    styles['BodyText'].leading = 13
    content = []
    def text(value, style='BodyText'):
        return Paragraph(escape(str(value)), styles[style])
    def table(rows, widths=None):
        cells = [[text(c) for c in row] for row in rows]
        result = Table(cells, colWidths=widths, repeatRows=1)
        result.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eefb')),
                                   ('GRID',(0,0),(-1,-1),.3,colors.HexColor('#c7ced8')),
                                   ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5)]))
        return result
    def plot(path, width=475):
        image = Image(str(path))
        image.drawHeight *= width / image.drawWidth
        image.drawWidth = width
        if image.drawHeight > 590:
            image.drawWidth *= 590 / image.drawHeight
            image.drawHeight = 590
        return image
    content += [text('Моделирование продуктовой компании','Title'),
                text(f"Интервал t: {data['interval'][0]:g} — {data['interval'][1]:g}"),
                text('Расчёт основан на постановке до раздела с примером реализации. Значения приведены без обрезания. Нарушение минимального порога — проверка критерия, а не доказательство математической неустойчивости.'),Spacer(1,12)]
    rows = [['Показатель','Начало','L*','Порог','Конец','Первое нарушение']]
    for i,v in enumerate(VARIABLES):
        breach = data['result']['first_breach'][i]
        status = f't ≈ {breach:.6g}' if breach is not None else 'На сетке' if data['result']['ever_below_minimum'][i] else 'Не обнаружено'
        rows.append([v['symbol']+' '+v['name'], f"{data['initial_variable_values'][v['symbol']]:.5g}",data['scales'][i],data['minima'][i],f"{data['result']['solution'][i]:.6g}",status])
    content += [table(rows,[155,50,35,55,65,115]),PageBreak(),text('Динамика показателей','Heading1'),
                plot(Path(Constants.PATH_SOLUTION_GRAPHS_IMAGE)/(calculation_id+'.png')),text('Внешние факторы','Heading1'),
                plot(Path(Constants.PATH_SOLUTION_GRAPHS_IMAGE)/(calculation_id+'-q.png'))]
    content += [PageBreak(),text('Внешние факторы и параметры','Heading1')]
    for i,name in enumerate(PERTURBATIONS,1):
        content.append(text(f'q{i} — {name}'))
    for line in ['q1, q2 = a + b sin(c t + d)', 'q3 = 0 при t ≤ 0,6; 0,3 при 0,6 < t ≤ 0,8; 0,4 при t > 0,8.',
                 'q4 — пользовательская ступенчатая функция; новый уровень действует с указанного времени.', 'q5 = a √t + b.',
                 'Все параметры q1, q2, q4, q5 введены пользователем.']:
        content.append(text(line))
    content.append(table([['Параметр','Значение']]+[[k,f'{v:.8g}'] for k,v in data['perturbation_parameters'].items() if k != 'q4_steps'],[200,200]))
    content += [Spacer(1,12),text('Ступени q4','Heading2'),table([['Начало t','Уровень']]+[[s['time'],s['value']] for s in data['perturbation_parameters']['q4_steps']],[200,200])]
    content += [PageBreak(),text('Система дифференциальных уравнений','Heading1')]
    for i in range(15):
        content += [text(equation_text(i)),Spacer(1,10)]
    content += [PageBreak(),text('Коэффициенты полиномов','Heading1'),text('f(x) = a0 + a1 x + a2 x² + a3 x³')]
    content.append(table([['Функция','a0','a1','a2','a3']]+[[f]+[f"{c.get('A'+str(k),0):.6g}" for k in range(4)] for f,c in data['polynomial_coefficients'].items()],[80,95,95,95,95]))
    for i,t in enumerate(data['result']['snapshot_times'],1):
        content += [PageBreak(),text(f'Показатели компании при t = {t:g}','Heading1'),
                    plot(Path(Constants.PATH_PETAL_GRAPHS_IMAGE)/calculation_id/f'{i}.png')]
    stream = BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=A4, rightMargin=32,leftMargin=32,topMargin=32,bottomMargin=32,
                            title='Модель продуктовой компании',author='')
    doc.build(content)
    return stream.getvalue()
