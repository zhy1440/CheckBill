import pandas as pd
import datetime
import logging
import numpy as np
from decimal import Decimal
# 交易日期	记账日期	交易摘要	人民币金额	交易地金额
# 2020/7/9

# 时间	收支类型	账目分类	金额	账户	账户类型	账本	成员	备注
# 2020/07/23
month = 4

start_date = datetime.datetime(2020, month - 1, 7)
end_date = datetime.datetime(2020, month, 7)


def config_logger():
    log_formatter = '[%(asctime)s] %(levelname)s : %(message)s'
    # create formatter
    formatter = logging.Formatter(log_formatter)
    log_level = logging.DEBUG

    # create logger
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(log_level)

    # add formatter to ch
    ch.setFormatter(formatter)

    fh = logging.FileHandler(
        filename='check_bill.log', encoding='utf-8')
    fh.setLevel(log_level)
    # tell the handler to use this format
    fh.setFormatter(formatter)

    # add the handler to the root logger
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger


SPLIT_MARK = '====================== {} ========================='
pd.set_option('display.float_format', lambda x: '%.2f' %
              x)  # 为了直观的显示数字，不采用科学计数法
logger = config_logger()


def print_split(title):
    logger.info(SPLIT_MARK.format(title))


def decimal_from_value(value):
    if value:
        return Decimal(str(value).replace(',', ''))


def remove_tab_from_value(value):
    return value.replace('\t', '')


def init_cmb():
    columns = ['transaction_date', 'bill_date', 'transaction_description', 'transaction_location', 'card_number',
               'str_rmb', 'transction_amount']
    df = pd.read_csv('data/userdata.csv', header=0, names=columns, parse_dates=['transaction_date', 'bill_date'],
                     # dtype={'transction_amount': np.float64}, thousands=',',
                     index_col=None, na_values=['NA'], converters={'transction_amount': decimal_from_value, 'transaction_description': remove_tab_from_value})
    df['type'] = 'cmb'
    df = df[['transaction_date', 'transction_amount',
             'transaction_description', 'type']]
    df = df.sort_values(by='transaction_date')

    # logger.debug(df)
    # quit()
    return df


def init_cmb_history():

    def conver_date(date):
        return pd.to_datetime('2020'+date.zfill(4))

    columns = ['transaction_date', 'bill_date', 'transaction_description', 'transaction_location', 'card_number',
               'str_rmb', 'transction_amount']
    df = pd.read_excel('data/cmb-{month}.xlsx'.format(month=month), 'Sheet1', converters={'transction_amount': decimal_from_value, 'transaction_date': conver_date},
                       index_col=None, names=columns, na_values=['NA'], parse_dates=['transaction_date'])
    df['type'] = 'cmb'
    df = df[['transaction_date', 'transction_amount',
             'transaction_description', 'type']]
    df = df.sort_values(by='transaction_date')
    df = df[df.transaction_date > start_date]

    logger.debug(df)
    # quit()
    return df


def init_pocket():
    columns = ['transaction_date', 'transaction_type', 'transaction_classify',
               'transction_amount', 'account', 'account_type', 'account_book', 'member', 'transaction_description']
    df = pd.read_excel('data/pocket.xls', '收支记录', converters={'transction_amount': decimal_from_value},
                       index_col=None, names=columns, na_values=['NA'], parse_dates=['transaction_date'])
    df['type'] = 'pocket'
    df = df[(df.account == '招商银行信用卡')]
    df = df[['transaction_date', 'transction_amount',
             'transaction_description', 'type']]
    df = df.sort_values(by='transaction_date')
    # df = df[df.transaction_date > datetime.datetime(2020, 7, 6)]
    df = df[(df.transaction_date > start_date)
            & (df.transaction_date < end_date)]

    # logger.debug(df)
    return df


def check_by_pair(df_cmb, df_pocket):
    print_split('check by pair')
    unrecorded_cmb = []
    pair_checked_count = 0
    # unrecorded_pocket = []
    for record in df_cmb.to_records():
        index, transaction_date, value, *(_) = record
        if transaction_date in df_pocket['transaction_date'].values:
            logger.debug(record)
            if value is not None:
                result = df_pocket[(df_pocket.transction_amount == -value) &
                                   (df_pocket.transaction_date == transaction_date)]
                if len(result) > 0:
                    if len(result) > 1:
                        logger.warning('[failed] !!! has same record')
                        logger.warning(result)
                        unrecorded_cmb.append(record)
                    else:
                        logger.info(
                            '[checked] {cmb} - {pocket}'.format(cmb=record, pocket=result.values))
                        df_pocket = df_pocket.drop(result.index)
                        pair_checked_count += 1
                else:
                    unrecorded_cmb.append(record)
                    # logger.debug('===> not found!!!', record)
        else:
            unrecorded_cmb.append(record)
            # logger.debug('===>', transaction_date, 'not found!!!', record)
        unrecorded_pocket = df_pocket.to_records()
    return pair_checked_count, unrecorded_cmb, unrecorded_pocket


def check_by_sum(unrecorded_cmb, unrecorded_pocket):
    print_split('check by sum')

    total_rest_records = unrecorded_cmb[:]
    for record in unrecorded_pocket:
        total_rest_records.append(record)

    columns = ['index', 'transaction_date', 'transction_amount',
               'transaction_description', 'type']
    df = pd.DataFrame.from_records(total_rest_records, columns=columns)
    # total_rest_count = len(total_rest_records)

    df = df[['transaction_date', 'type',
             'transction_amount', 'transaction_description']]
    df = df.sort_values(by=['transaction_date', 'type'])

    df = df.groupby('transaction_date').filter(
        lambda x: x.transction_amount.sum() != 0)

    cmb_rest_count = len(df[df['type'] == 'cmb'])
    pocket_rest_count = len(df[df['type'] == 'pocket'])

    print_split('Total Rest Records')
    for group in df.groupby('transaction_date'):
        logger.info(group)

    return cmb_rest_count, pocket_rest_count


def print_records(records, title):
    print_split(title)
    for record in records:
        logger.info('{} {} {}'.format(
            str(record[1])[:10], record[2], record[3]))


def main():
    print_split('started')

    df_cmb = init_cmb_history()

    # df_cmb = init_cmb()
    df_pocket = init_pocket()
    logger.debug(df_cmb)
    logger.debug(df_pocket)

    original_len_cmb = len(df_cmb)
    original_len_pocket = len(df_pocket)

    pair_checked_count, unrecorded_cmb, unrecorded_pocket = check_by_pair(
        df_cmb, df_pocket)

    print_records(unrecorded_pocket, 'POCKET')
    print_records(unrecorded_cmb, 'CMB')

    cmb_rest_count, pocket_rest_count = check_by_sum(
        unrecorded_cmb, unrecorded_pocket)

    pocket_checked_count = len(unrecorded_pocket) - pocket_rest_count
    cmb_checked_count = len(unrecorded_cmb) - cmb_rest_count

    if original_len_cmb == (cmb_rest_count + pair_checked_count + cmb_checked_count) \
            and (original_len_pocket == pocket_rest_count + pair_checked_count + pocket_checked_count):
        logger.info('[success] count check of cmb is ok. {} cmb records remain to be recorded'.format(
            cmb_rest_count))
    else:
        logger.warning('[failed] !!! count is inconsistant! cmb_checked_count {}: pocket_checked_count: {}'.format(
            cmb_checked_count, pocket_checked_count))

    logger.info(
        """Success checked count by pair: {}
        Total cmb count: {}     Rest cmb count:{}
        Total pocket count: {}  Rest pocket count: {}"""
        .format(pair_checked_count, original_len_cmb, cmb_rest_count, original_len_pocket, pocket_rest_count))

    print_split('finished')


if(__name__ == '__main__'):
    main()
