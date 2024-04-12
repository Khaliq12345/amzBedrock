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
pd.options.display.max_columns = None
pd.options.display.max_rows = None

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

def get_table(cols: list, neg_keywords: list = []):
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
    items.append({
        'Product': "Sponsored Products",
        'Entity': 'Product Targeting'
    })
    for i in range(3):
        items.append({
            'Product': "Sponsored Products",
            'Entity': "Bidding Adjustment"
        })
    for k in neg_keywords:
        items.append({
            'Product': "Sponsored Products",
            'Entity': "Negative product targeting"
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
def download_categories(file_url, is_neg: bool = False):
    x_name = str(uuid.uuid1())
    output = f"{x_name}.csv"
    gdown.download(file_url, output, fuzzy=True, quiet=True)
    df = pd.read_csv(output, header=None)
    df.dropna(how='all', inplace=True)
    os.remove(output)
    if is_neg:
        return df[0].to_list()
    else:
        return df

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
            cat_df = download_categories(row['Categories File'])
            cat_names = cat_df[1].to_list()
            cat_ids = cat_df[0].to_list()
            for id_, name in zip(cat_ids, cat_names):
                if type(row['Negative Targeting']) != float:
                    neg_kewords = download_categories(row['Negative Targeting'], is_neg=True)
                    x_table = get_table(out_cols, neg_keywords=neg_kewords)
                else:
                    x_table = get_table(out_cols)
                #campaign name
                campaign_name = f"{row['SKU']}_{row['ASIN']}_SP_PT_CAT_{name}"
                #operation
                x_table['Operation'] = 'create'
                x_table['Campaign ID'] = campaign_name
                x_table.loc[x_table['Entity'] != 'Campaign', 'Ad Group ID'] = campaign_name
                x_table.loc[x_table['Entity'] == 'Campaign', 'Portfolio ID'] = row['Portfolio ID']
                x_table.loc[x_table['Entity'] == 'Campaign', 'Campaign Name'] = campaign_name
                x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Name'] = campaign_name
                x_table.loc[x_table['Entity'] == 'Campaign', 'Start Date'] = parse_date(str(row['Start Date']))
                x_table.loc[x_table['Entity'] == 'Campaign', 'Targeting Type'] = 'Manual'
                #state
                enable_pause = lambda x: 'enabled' if x == 'yes' else 'paused'
                x_table.loc[x_table['Entity'] == 'Product Ad', 'State'] = 'enabled'
                x_table.loc[x_table['Entity'].isin(['Campaign', 'Ad Group']), 'State'] = enable_pause(row['Activate Campaign and Ad Group'])
                x_table.loc[x_table['Entity'] == 'Product Targeting', 'State'] = 'enabled'
                
                x_table.loc[x_table['Entity'] == 'Campaign', 'Daily Budget'] = row['Daily Budget']
                console_sc_vc = lambda x, y, value: y if x == value else None
                x_table.loc[x_table['Entity'] == 'Product Ad', 'SKU'] = console_sc_vc(row['Console'], row['SKU'], 'SC')
                x_table.loc[x_table['Entity'] == 'Product Ad', 'ASIN'] = console_sc_vc(row['Console'], row['ASIN'], 'VC')
                x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Default Bid'] = row['Bid']
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
                x_table.loc[x_table['Entity'].isin(['Product Targeting']), 'Product Targeting Expression'] = f'category="{id_}"'
                #adding negative asin
                if type(row['Negative Targeting']) != float:
                    x_table.loc[x_table['Entity'] == 'Negative product targeting', 'Campaign ID'] = campaign_name
                    x_table.loc[x_table['Entity'] == 'Negative product targeting', 'State'] = 'enabled'
                    x_table.loc[x_table['Entity'] == 'Negative product targeting', 'Ad Group ID'] = campaign_name
                    neg_kewords_asins = [f'asin="{neg}"' for neg in neg_kewords]
                    x_table.loc[x_table['Entity'] == 'Negative product targeting', 'Product Targeting Expression'] = neg_kewords_asins
                x_table.replace('nan', value='', inplace=True)
                dfs.append(x_table)

    output_dataframe = pd.concat(dfs, ignore_index=True)
    return output_dataframe





