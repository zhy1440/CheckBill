import pandas as pd
import numpy as np
from pdfreader import PDFDocument, SimplePDFViewer
# from common import config_logger
from common import decimal_from_value

# logger = config_logger('analyze_pdf.log')
FILE_PATH = "data/CreditCardReckoning2020{}.pdf"


def init_cmb_from_pdf(month):
    filename = FILE_PATH.format(str(month).zfill(2))
    # logger.info(filename)
    fd = open(filename, "rb")

    doc = PDFDocument(fd)
    all_pages = [p for p in doc.pages()]
    # logger.info(len(all_pages))

    viewer = SimplePDFViewer(fd)
    records = []
    for i in range(len(all_pages)):
        viewer.navigate(i+1)
        viewer.render()
        records = np.append(records, viewer.canvas.strings[4:])

    head = np.where(records == '记账日')[0][0]
    tail = np.where(records == '本期还款总额')[0][-1]
    records = records[head:tail]

    # title_cn = records[:5]
    # title_en = records[5:11]
    records = records[11:]

    column_cn = ['交易日' '交易摘要' '人民币金额' '卡号末四位' '记账日' '交易地金额']
    column_en = ['transaction_date', 'transaction_description', 'transction_amount',
                 'card_number', 'bill_date', 'str_rmb']
    # Data: ['' '掌上生活还款' '-3,011.49' '9978' '07/24' '-3,011.49']

    df = pd.DataFrame(records.reshape(
        [int(len(records)/6), 6]), columns=column_en)

    df['type'] = 'cmb'

    df['transaction_date'] = df['transaction_date'].apply(
        lambda _: '2020/' + _)
    df['transaction_date'] = pd.to_datetime(
        df['transaction_date'], format="%Y/%m/%d", errors='coerce')

    df['transction_amount'] = df['transction_amount'].apply(
        lambda _: decimal_from_value(_))

    df = df[['transaction_date', 'transction_amount',
             'transaction_description', 'type']]

    return df


def init_cmb_from_pdf_multiple(months):
    df = pd.DataFrame()

    for month in months:
        df = df.append(init_cmb_from_pdf(month), ignore_index=True)

    df = df.sort_values(by='transaction_date')
    return df
