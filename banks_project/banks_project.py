# Code for ETL operations on Country-GDP data

# Importing the required libraries

from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
from pathlib import Path

PROJECT_PATCH = Path(__file__).parent


def log_progress(message):
    ''' This function logs the mentioned message at a given stage of the 
    code execution to a log file. Function returns nothing.'''

    timestamp_format = '%Y-%h-%d-%H:%M:%S'  # Year-Monthname-Day-Hour-Minute-Second
    now = datetime.now()  # get current timestamp
    timestamp = now.strftime(timestamp_format)
    with open(PROJECT_PATCH / "code_log.txt", "a") as f:
        f.write(timestamp + ' : ' + message + '\n')


def extract(url, table_attribs):
    ''' The purpose of this function is to extract the required
    information from the website and save it to a dataframe. The
    function returns the dataframe for further processing. '''

    page = requests.get(url).text
    data = BeautifulSoup(page, 'html.parser')
    df = pd.DataFrame(columns=table_attribs)
    tables = data.find_all('tbody')
    rows = tables[0].find_all('tr')
    for row in rows:
        col = row.find_all('td')
        if len(col) != 0:
            market_cap = col[2].contents[0].strip()
            # market_cap = float(col[2].contents[0][:-1])
            bank_name = col[1].find_all('a')[1]['title']
            data_dict = {"Name": bank_name,
                         "MC_USD_Billion": market_cap
                         }
            df1 = pd.DataFrame(data_dict, index=[0])
            df = pd.concat([df, df1], ignore_index=True)
    return df


def transform(df, csv_path):
    ''' This function accesses the CSV file for exchange rate
    information, and adds three columns to the data frame, each
    containing the transformed version of Market Cap column to
    respective currencies'''

    df_exchange = pd.read_csv(csv_path)

    exchange_rate = df_exchange.set_index('Currency').to_dict()['Rate']

    df["MC_USD_Billion"] = [float(x)
                            for x in df['MC_USD_Billion']]

    df['MC_GBP_Billion'] = [np.round(x*exchange_rate['GBP'], 2)
                            for x in df['MC_USD_Billion']]

    df['MC_EUR_Billion'] = [np.round(x*exchange_rate['EUR'], 2)
                            for x in df['MC_USD_Billion']]

    df['MC_INR_Billion'] = [np.round(x*exchange_rate['INR'], 2)
                            for x in df['MC_USD_Billion']]

    return df


def load_to_csv(df, output_path):
    ''' This function saves the final data frame as a CSV file in
    the provided path. Function returns nothing.'''

    df.to_csv(output_path)


def load_to_db(df, sql_connection, table_name):
    ''' This function saves the final data frame to a database
    table with the provided name. Function returns nothing.'''

    df.to_sql(table_name, sql_connection, if_exists='replace', index=False)


def run_queries(query_statement, sql_connection):
    ''' This function runs the query on the database table and
    prints the output on the terminal. Function returns nothing. '''

    print(query_statement)
    query_output = pd.read_sql(query_statement, sql_connection)
    print(query_output)


''' Here, you define the required entities and call the relevant
functions in the correct order to complete the project. Note that this
portion is not inside any function.'''

url = 'https://web.archive.org/web/20230908091635/https://en.wikipedia.org/wiki/List_of_largest_banks'
table_attribs = ["Name", "MC_USD_Billion"]
csv_path = PROJECT_PATCH / 'exchange_rate.csv'
output_path = PROJECT_PATCH / 'Largest_banks_data.csv'
db_name = 'Banks.db'
db_path = PROJECT_PATCH / 'Banks.db'
table_name = 'Largest_banks'

log_progress('Preliminaries complete. Initiating ETL process')

df = extract(url, table_attribs)

# print(df)
# print(df.dtypes)

log_progress('Data extraction complete. Initiating Transformation process')

transform(df, csv_path)

# print(df)
# print(df.dtypes)


log_progress('Data transformation complete. Initiating loading process')

load_to_csv(df, output_path)

log_progress('Data saved to CSV file')

sql_connection = sqlite3.connect(db_path)

log_progress('SQL Connection initiated.')

load_to_db(df, sql_connection, table_name)

log_progress('Data loaded to Database as table. Running the query')

query_statement = f"SELECT * from {table_name}"
run_queries(query_statement, sql_connection)

print()

query_statement = f"SELECT AVG(MC_GBP_Billion) from {table_name}"
run_queries(query_statement, sql_connection)


log_progress('Process Complete.')

sql_connection.close()
