import pandas as pd
import sys
import numpy as np

C_TAKE_PR_PERC = 5
C_CAPITAL = 2000
C_FILENAME = 'output/BANKBEES-PerWeekCap-'+str(C_CAPITAL)+' and TakeProfit percentage- '+str(C_TAKE_PR_PERC)

df_csv = pd.read_csv("./input/BANKNIFTY-D.csv")

df_csv['Date'] = pd.to_datetime(df_csv['Date'], format='%d-%m-%y')
"""
df_csv = df_csv.sort_values(by='NewDate')
df_csv['Weekday'] = df_csv['NewDate'].dt.weekday
"""
data = {
    'BuyOn': [],
    'BuyPrice': [],
    'Qty': [],
    'SellOn': [],
    'SellPrice': [],
    'GainP': [],
    'Days': [],
    'GrossGain': [],
    'NetGain': [],
    'CSVIndex': []

}
columns = ['BuyOn', 'BuyPrice', 'Qty', 'SellOn', 'SellPrice', 'GainP', 'Days', 'GrossGain', 'NetGain', 'CSVIndex']

df = pd.DataFrame(data, columns = columns)

def getProfitForYear(dff, year):
    dff = dff[dff['BuyOn'].dt.year == year]
    return dff['NetGain'].sum()

def getSaleDate(DF, BuyDate, SellPrice, Index):
    dff = DF
    dff = dff.loc[(dff['Date'] > BuyDate)]
    for i, r in dff.iterrows():
        if SellPrice <= r['H']:
            return r['Date']
    return None

#Buying Logic
for index, row in df_csv.iterrows():
    if index > 0:

        if row['WeekDay'] < df_csv.iloc[index-1]['WeekDay']:
            df = df.append({
                'BuyOn': df_csv.iloc[index-1]['Date'],
                'BuyPrice': df_csv.iloc[index-1]['C'],
                'Qty':  round(C_CAPITAL / df_csv.iloc[index-1]['C']),
                'SellPrice': round( df_csv.iloc[index-1]['C'] + (df_csv.iloc[index-1]['C'] * C_TAKE_PR_PERC / 100 ) , 2),
                'CSVIndex': int(index)
            }, ignore_index=True)

#Selling Logic
#df.at[1, 'GainP'] = 11
for i, r in df.iterrows():
    sellDate = getSaleDate(df_csv, r['BuyOn'], r['SellPrice'], r['CSVIndex'])    
    if(sellDate is not None):
        GrossGain = round( (r['SellPrice'] * r['Qty']) - (r['BuyPrice'] * r['Qty']) , 2)
        df.at[i, 'SellOn'] = sellDate
        df.at[i, 'GrossGain'] = GrossGain
        df.at[i, 'NetGain'] = round( GrossGain - (GrossGain*1/100) , 2)
    
df['SellOn'] = pd.to_datetime(df['SellOn'], format='%d-%m-%y')

#Remove Days text
df['Days'] = (df['SellOn'] - df['BuyOn']).dt.days
##############################################################################
#Building Ledger
data = {
    'Date': [],
    'Action': [],
    'Amount': [],
    'Year': [],
    'Cummulation': []
}
columns = ['Date', 'Action', 'Amount', 'Year', 'Cummulation']

df_ledger = pd.DataFrame(data, columns = columns)
for x, l in df.iterrows():
    df_ledger = df_ledger.append({
        'Date': l['BuyOn'],
        'Action': 'Buy',
        'Amount': round( l['BuyPrice'] * l['Qty'], 2)
    }, ignore_index=True)
    if pd.isnull( l['SellOn'] ) == False:
        df_ledger = df_ledger.append({
            'Date': l['SellOn'],
            'Action': 'Sell',
            'Amount': round( l['BuyPrice'] * l['Qty'], 2)
        }, ignore_index=True)

df_ledger = df_ledger.sort_values(by='Date')
df_ledger['Year'] = pd.DatetimeIndex(df_ledger['Date']).year

###########################################################
#Preparing Cummulation
###########################################################
df_ledger = df_ledger.reset_index(drop=True)
currYear = 0
for e, g in df_ledger.iterrows():
#    if(e == 0):
    if(currYear != g['Year']):
        df_ledger.at[e, 'Cummulation'] = g['Amount']
        currYear = g['Year']
    else:
        if(g['Action'] == 'Buy'):
            df_ledger.at[e, 'Cummulation'] = round(df_ledger.iloc[e-1]['Cummulation'] + g['Amount'], 2)
        else:
            df_ledger.at[e, 'Cummulation'] = round(df_ledger.iloc[e-1]['Cummulation'] - g['Amount'], 2)


df_ledger.to_csv('./'+C_FILENAME+'--ledger.csv')
################################################################
#Building Summary

data = {
    'Year': [],
    'MaxCapital': [],
    'Profit': [],
    'Percent Gain': []
}
columns = ['Year', 'MaxCapital', 'Profit', 'Percent Gain']

df_summary = pd.DataFrame(data, columns = columns)

years = df_ledger.Year.unique()
df_ledger_tmp = df_ledger
for y in years:
    df_ledger_tmp = df_ledger
    df_ledger_tmp = df_ledger_tmp.loc[(df_ledger_tmp['Year'] == y)]
    df_ledger_tmp = df_ledger_tmp.sort_values(by='Cummulation', ascending=False)
    df_ledger_tmp = df_ledger_tmp.reset_index(drop=True)
    #df_ledger_tmp.iloc[0]['Amount']

    v_profitForYear = getProfitForYear(df, y)
    df_summary = df_summary.append({
        'Year': y,
        'MaxCapital': df_ledger_tmp.iloc[0]['Cummulation'],
        'Profit': v_profitForYear,
        'Percent Gain': round( v_profitForYear * 100 / df_ledger_tmp.iloc[0]['Cummulation'], 2 )
    }, ignore_index=True)
    

df.to_csv('./'+C_FILENAME+'--output.csv')
print(df_summary) #print(df)
df_summary.to_csv('./'+C_FILENAME+'--Summary.csv')
