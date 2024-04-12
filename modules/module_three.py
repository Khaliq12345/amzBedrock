import pandas as pd
import dateparser
import pandas
from datetime import datetime
import gdown
from warnings import filterwarnings
import uuid
import os
from retrying import retry

filterwarnings('ignore')

out_cols = ['Product',
 'Entity',
 'Operation',
 'Campaign ID',
 'Ad Group ID',
 'Portfolio ID',
 'Ad ID',
 'Keyword ID',
 'Product Targeting ID',
 'Campaign Name',
 'Ad Group Name',
 'Start Date',
 'End Date',
 'Targeting Type',
 'State',
 'Daily Budget',
 'SKU',
 'ASIN',
 'Ad Group Default Bid',
 'Bid',
 'Keyword Text',
 'Match Type',
 'Bidding Strategy',
 'Placement',
 'Percentage',
 'Product Targeting Expression']

def get_table(cols: list, asins:list):
    items = []
    items.append({
        'Product': "Sponsored Products",
        'Entity': 'Campaign'
    })
    items.append({
        'Product': "Sponsored Products",
        'Entity': 'Ad Group'
    })
    items.append({
        'Product': "Sponsored Products",
        'Entity': 'Product Ad'
    })
    for asin in asins:
        items.append({
            'Product': "Sponsored Products",
            'Entity': 'Product Targeting'
        })
    for i in range(3):
        items.append({
            'Product': "Sponsored Products",
            'Entity': "Bidding Adjustment"
        })
    
    df = pd.DataFrame(items, columns=cols)
    df = df.loc[:, :].astype(str)
    return df

def parse_date(date_str):
    adder = lambda x: f'0{x}' if len(x) < 2 else x
    parse_date = dateparser.parse(date_str)
    year = parse_date.year
    month = adder(str(parse_date.month))
    day = adder(str(parse_date.day))
    return f'{year}{month}{day}'

@retry(stop_max_attempt_number=10, wait_fixed=500)
def download_asins(file_url):
    x_name = str(uuid.uuid1())
    output = f"{x_name}.csv"
    gdown.download(file_url, output, fuzzy=True, quiet=True)
    df = pd.read_csv(output, header=None)
    df.dropna(how='all', inplace=True)
    os.remove(output)
    return df[0].to_list()

def proccess_df(input_df: pd.DataFrame):
    input_df.dropna(how='all')
    input_df = input_df.loc[2:]
    dfs = []
    input_df.loc[:, 'Placement Top'] = input_df['Placement Top'].astype(str).apply(lambda x: x.replace('%', '').strip() if type(x) == str else x)
    input_df.loc[:, 'Placement Product Page'] = input_df['Placement Product Page'].astype(str).apply(lambda x: x.replace('%', '').strip() if type(x) == str else x)
    input_df.loc[:, 'Placement Rest Of Search'] = input_df['Placement Rest Of Search'].astype(str).apply(lambda x: x.replace('%', '').strip() if type(x) == str else x)
    input_df.loc[:, 'Portfolio ID'] = input_df['Portfolio ID'].astype(str)
    for i, row in input_df.iterrows():
        if type(row['SKU']) != float:
            #Entity and Sponsored Product
            if row['Targeting'] == 'SELF':
                x_table = get_table(out_cols, [row['ASIN']])
            else:
                asins = download_asins(row['Targeting File'])
                x_table = get_table(out_cols, asins)
            #create
            x_table.loc[:, 'Operation'] = 'create'
            #campaign name
            campaign_name = lambda x: f"{row['SKU']}_SP_PT_{row['ASIN']}_{row['Targeting']}_Expanded" if 'y' in x else f"{row['SKU']}_SP_PT_{row['ASIN']}_{row['Targeting']}"
            #campaign id
            x_table.loc[:, 'Campaign ID'] = campaign_name(row['Expanded?'])
            #ad group id
            x_table.loc[x_table['Entity'] != 'Campaign', 'Ad Group ID'] = campaign_name(row['Expanded?'])
            #portfolio id
            x_table.loc[x_table['Entity'] == 'Campaign', 'Portfolio ID'] = row['Portfolio ID']
            #campaign name
            x_table.loc[x_table['Entity'] == 'Campaign', 'Campaign Name'] = campaign_name(row['Expanded?'])
            #ad group name
            x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Name'] = campaign_name(row['Expanded?'])
            #start date
            x_table.loc[x_table['Entity'] == 'Campaign', 'Start Date'] = parse_date(str(row['Start Date']))
            #targeting type
            x_table.loc[x_table['Entity'] == 'Campaign', 'Targeting Type'] = 'Manual'
            #state
            enable_pause = lambda x: 'enabled' if x == 'yes' else 'paused'
            x_table.loc[x_table['Entity'] == 'Product Ad', 'State'] = 'enabled'
            x_table.loc[x_table['Entity'].isin(['Campaign', 'Ad Group']), 'State'] = enable_pause(row['Activate Campaign and Ad Group'])
            x_table.loc[x_table['Entity'] == 'Product Targeting', 'State'] = 'enabled'
            #daily budget
            x_table.loc[x_table['Entity'] == 'Campaign', 'Daily Budget'] = row['Daily Budget']
            #sku and asin
            console_sc_vc = lambda x, y, value: y if x == value else None
            x_table.loc[x_table['Entity'] == 'Product Ad', 'SKU'] = console_sc_vc(row['Console'], row['SKU'], 'SC')
            x_table.loc[x_table['Entity'] == 'Product Ad', 'ASIN'] = console_sc_vc(row['Console'], row['ASIN'], 'VC')
            #Ad group default bid
            x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Default Bid'] = row['Bid']
            #Bidding adj
            x_table.loc[x_table['Entity'].isin(['Campaign', 'Bidding Adjustment']), 'Bidding Strategy'] = row['Bidding Strategy']
            #Placement
            placement_values = ['Placement Product Page', 
                                'Placement Rest Of Search', 
                                'Placement Top']
            x_table.loc[x_table['Entity'] == 'Bidding Adjustment', 'Placement'] = placement_values
            #Percentage
            perc = lambda x: str(x) if x > 0.0 else '0'
            perc_values = [
                perc(int(row['Placement Product Page'])),
                perc(int(row['Placement Rest Of Search'])),
                perc(int(row['Placement Top']))
            ]
            x_table.loc[x_table['Entity'] == 'Bidding Adjustment', 'Percentage'] = perc_values
            #Product Targeting
            if row['Targeting'] == 'SELF':
                if row['Expanded?'] == 'y':
                    targets = f'asin-expanded="{row["ASIN"]}"'
                else:
                    targets = f'asin="{row["ASIN"]}"'
            else:
                if row['Expanded?'] == 'y':
                    targets = [f'asin-expanded="{t}"' for t in asins]
                else:
                    targets = [f'asin="{t}"' for t in asins]
            x_table.loc[x_table['Entity'].isin(['Product Targeting']), 'Product Targeting Expression'] = targets
            x_table.replace('nan', value='', inplace=True)
            dfs.append(x_table)
    
    output_dataframe = pd.concat(dfs, ignore_index=True)
    return output_dataframe



