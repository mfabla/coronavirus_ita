# script 1 to export coronavirus data
# mike abla
# 22 mar 2020

# import packages
import requests
import json
import pandas as pd
import numpy as np
from plotnine import *
import matplotlib.pyplot as plt
import xlsxwriter

### part 1:  api connection to get coronavirus data
# get italy data

url = "https://coronavirus-monitor.p.rapidapi.com/coronavirus/cases_by_particular_country.php"
api_key = 'xxxxx'

querystring = {"country":"Italy"}

headers = {
    'x-rapidapi-host': "coronavirus-monitor.p.rapidapi.com",
    'x-rapidapi-key': api_key
    }

response = requests.request("GET", url, headers=headers, params=querystring)

print(response.text)

data = response.json()
print(data.keys())

### part 2: convert to dataframe and clean
df_italy = pd.DataFrame(data['stat_by_country'])

# vars to change to numeric
vars_numeric = ['total_cases', 'new_cases', 'active_cases', 'total_deaths', 'new_deaths', 'total_recovered',
                'serious_critical', 'total_cases_per1m']


df_italy[vars_numeric] = df_italy[vars_numeric].apply(lambda x: x.str.replace(',', '').\
                             apply(pd.to_numeric))

# fix datetime & create date field
df_italy['record_date'] = pd.to_datetime(df_italy['record_date'])
df_italy['date'] = df_italy['record_date'].dt.date


### part 3: group by date
vars_to_keep =  vars_numeric + ['record_date']
df_ITA = df_italy[vars_to_keep].\
    dropna().\
    set_index('record_date').\
    drop_duplicates()

df_ITA_summary = df_ITA.resample('D').max().reset_index()
df_ITA_summary['new_cases % change'] = (df_ITA_summary['new_cases'] - df_ITA_summary['new_cases'].shift(1))/df_ITA_summary['new_cases'].shift(1)
df_ITA_summary['new_cases WoW % change'] = (df_ITA_summary['new_cases'] - df_ITA_summary['new_cases'].shift(7))/df_ITA_summary['new_cases'].shift(7)
df_ITA_summary['new_cases_3dayMA'] = df_ITA_summary['new_cases'].rolling(window=3).mean()
df_ITA_summary_melt = pd.melt(df_ITA_summary, id_vars='record_date')

### part 4: plot trending

print(df_ITA_summary_melt.variable.unique())
vars_to_plot = ['active_cases', 'new_cases']
df_plot = df_ITA_summary_melt[df_ITA_summary_melt.variable.isin(vars_to_plot)]

# daily %s change wit new cases - bar chart
# df_ITA_summary.plot.bar(x='record_date', y='new_cases % change', )
# plt.show()
# plt.clear()

# daily %s change wit new cases - lollipop
# plt.stem(df_ITA_summary['new_cases % change'])
# plt.xticks(ticks=range(1, len(df_ITA_summary['record_date'])), labels=df_ITA_summary['record_date'].dt.date, rotation=45)
# plt.show()
# plt.clear()

#(ggplot(df_plot, aes(x='record_date', y='value', color='variable')) +geom_line())

# active & new case counts
# gca stands for 'get current axis'
ax = plt.gca()
df_ITA_summary.plot(x='record_date', y='active_cases', color='orange', ax=ax)
df_ITA_summary.plot(x='record_date', y='new_cases', color='maroon', ax=ax)
#df_ITA_summary.plot(x='record_date', y='total_recovered', color='blue', ax=ax)
plt.xlabel('Date')
plt.ylabel('Total Cases')
plt.title('Mar 17 - Current: Active & New Italy Covid-19 Cases')
plt.show()
plt.clf()


# 3 day ma of new cases
ax = plt.gca()
df_ITA_summary.plot(x='record_date', y='new_cases_3dayMA', color='orange', ax=ax)
plt.xlabel('Date')
plt.ylabel('Total Cases')
plt.title('Mar 17 - Current: 3 Day MA of New Cases')
plt.show()
plt.clf()

### part 5: write excel file
writer = pd.ExcelWriter('ITA_CoronaVirus_NewActiveCases.xlsx', engine='xlsxwriter')
df_ITA_summary.to_excel(writer, sheet_name='ITA Totals', index=False)

# add table formating
workbook = writer.book
worksheet = writer.sheets['ITA Totals']
#worksheet.add_table()
writer.save()
