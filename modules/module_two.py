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

def get_table(cols: list, keyword_type: str, keywords: list, neg_keywords: list = []):
    items = []
    if keyword_type == 'Single':
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
        for i in range(3):
                items.append({
                    'Product': "Sponsored Products",
                    'Entity': "Bidding Adjustment"
                })
        items.append({
            'Product': "Sponsored Products",
            'Entity': 'Keyword', 
        })
    else:
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
        for i in range(3):
                items.append({
                    'Product': "Sponsored Products",
                    'Entity': "Bidding Adjustment"
                })
        for keyword in keywords:
            items.append({
                'Product': "Sponsored Products",
                'Entity': 'Keyword', 
            })
    
    for _ in neg_keywords:
        items.append({
            'Product': "Sponsored Products",
            'Entity': 'Negative Keyword', 
        })
    df = pd.DataFrame(items, columns=cols)
    df = df.loc[:, :].astype(str)
    return df

# a file
@retry(stop_max_attempt_number=10, wait_fixed=500)
def download_keywords(file_url, is_neg: bool = False):
    x_name = str(uuid.uuid1())
    output = f"{x_name}.csv"
    gdown.download(file_url, output, fuzzy=True, quiet=True)
    df = pd.read_csv(f'{x_name}.csv', header=None)
    df.dropna(how='all', inplace=True)
    os.remove(f'{x_name}.csv')
    if is_neg:
        return df[0].to_list(), df[1].to_list()
    else:
        return df[0].to_list()

def modify_table(row, x_table, kw_type, kws, neg_info: list = []):
    #Generating the campaign name
    no_nan = lambda x: '' if type(x) != str else x
    branded_or_name = lambda x: '_Branded_' if row['Branded Campaign?'] == 'y' else f'_{x}_'
    campaign_name_mod = no_nan(row['Campaign Name Modifier'])
    single_kw = f"{row['SKU']}_SP_KW_{row['Match Type']}_{row['ASIN']}{branded_or_name(campaign_name_mod)}{kws}"
    kw_not_single = f"{row['SKU']}_SP_KW_{row['Match Type']}_{row['ASIN']}{branded_or_name(campaign_name_mod)}"
    make_campaign_name = lambda x: single_kw if 'Single' in x else kw_not_single #make campaign name
    campaign_name = make_campaign_name(row['Single/Group KWs'])
    
    #operation
    x_table.loc[:, 'Operation'] = 'create'
    
    #campaign id
    x_table.loc[:, 'Campaign ID'] = campaign_name
    
    #ad group id
    x_table.loc[x_table['Entity'] != 'Campaign', 'Ad Group ID'] = campaign_name
    
    #portfolio id
    x_table.loc[x_table['Entity'] == 'Campaign', 'Portfolio ID'] = row['Portfolio ID']
    
    #campaign name
    x_table.loc[x_table['Entity'] == 'Campaign', 'Campaign Name'] = campaign_name
    
    #ad group name
    x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Name'] = campaign_name
    
    #date
    x_table.loc[x_table['Entity'] == 'Campaign', 'Start Date'] = parse_date(str(row['Start Date']))
    
    #targeting type
    x_table.loc[x_table['Entity'] == 'Campaign', 'Targeting Type'] = 'Manual'
    
    #state
    enable_pause = lambda x: 'enabled' if x == 'yes' else 'paused'
    x_table.loc[x_table['Entity'] == 'Product Ad', 'State'] = 'enabled'
    x_table.loc[~(x_table['Entity'].isin(['Campaign', 'Ad Group', 'Product Ad', 'Bidding Adjustment'])), 'State'] = 'enabled'
    x_table.loc[x_table['Entity'].isin(['Campaign', 'Ad Group']), 'State'] = enable_pause(row['Activate Campaign and Ad Group'])

    #daily budget
    x_table.loc[x_table['Entity'] == 'Campaign', 'Daily Budget'] = row['Daily Budget']
    
    #sku and asin
    console_sc_vc = lambda x, y, value: y if x == value else ''
    x_table.loc[x_table['Entity'] == 'Product Ad', 'SKU'] = console_sc_vc(row['Console'], row['SKU'], 'SC')
    x_table.loc[x_table['Entity'] == 'Product Ad', 'ASIN'] = console_sc_vc(row['Console'], row['ASIN'], 'VC')
    
    #bid
    x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Default Bid'] = row['Bid']
    
    #keyword text
    if 'Single' in kw_type:
        target_kw = kws
        if row['Branded Campaign?'] == 'y':
            target_kw = f"{row['brand name']} {kws}"
    else:
        target_kw = kws
        if row['Branded Campaign?'] == 'y':
            target_kw = [f"{row['brand name']} {x}" for x in  target_kw] 
    x_table.loc[x_table['Entity'] == 'Keyword', 'Keyword Text'] = target_kw
    
    #match type
    x_table.loc[x_table['Entity'] == 'Keyword', 'Match Type'] = row['Match Type']
    
    #bidding strategy
    x_table.loc[x_table['Entity'].isin(['Campaign', 'Bidding Adjustment']), 'Bidding Strategy'] = row['Bidding Strategy']
    
    #Placement
    placement_values = ['Placement Product Page', 
                        'Placement Rest Of Search', 
                        'Placement Top']
    x_table.loc[x_table['Entity'] == 'Bidding Adjustment', 'Placement'] = placement_values
    
    #Percentage
    perc = lambda x: str(x) if x > 0.0 else '0'
    perc_values = [
        perc(float(row['Placement Product Page'])),
        perc(float(row['Placement Rest Of Search'])),
        perc(float(row['Placement Top']))
    ]
    x_table.loc[x_table['Entity'] == 'Bidding Adjustment', 'Percentage'] = perc_values
    #adding negative keyword data
    if type(row['Negative Targeting']) != float:
        x_table.loc[x_table['Entity'] == 'Negative Keyword', 'Campaign ID'] = campaign_name
        x_table.loc[x_table['Entity'] == 'Negative Keyword', 'State'] = 'enabled'
        x_table.loc[x_table['Entity'] == 'Negative Keyword', 'Keyword text'] = neg_info[0]
        x_table.loc[x_table['Entity'] == 'Negative Keyword', 'Match type'] = neg_info[1]
    return x_table

def parse_date(date_str):
    adder = lambda x: f'0{x}' if len(x) < 2 else x
    parse_date = dateparser.parse(date_str)
    year = parse_date.year
    month = adder(str(parse_date.month))
    day = adder(str(parse_date.day))
    return f'{year}{month}{day}'

def proccess_df(input_df: pd.DataFrame):
    input_df = input_df.dropna(how='all')
    input_df = input_df.loc[2:]
    dfs = []
    input_df.loc[:, 'Placement Top'] = input_df['Placement Top'].astype(str).apply(lambda x: x.replace('%', '').strip() if type(x) == str else x)
    input_df.loc[:, 'Placement Product Page'] = input_df['Placement Product Page'].astype(str).apply(lambda x: x.replace('%', '').strip() if type(x) == str else x)
    input_df.loc[:, 'Placement Rest Of Search'] = input_df['Placement Rest Of Search'].astype(str).apply(lambda x: x.replace('%', '').strip() if type(x) == str else x)
    input_df.loc[:, 'Portfolio ID'] = input_df['Portfolio ID'].astype(str)
    for i, row in input_df.iterrows():
        if type(row['SKU']) != float:
            #get the row table
            if 'Single' in row['Single/Group KWs']:
                kws = download_keywords(row['Keyword Link'])
                for kw in kws:
                    if type(row['Negative Targeting']) != float:
                        neg_keywords, neg_types = download_keywords(row['Negative Targeting'], is_neg=True)
                        x_table = get_table(out_cols, row['Single/Group KWs'], kw, neg_keywords=neg_keywords)
                        x_table = modify_table(row, x_table, 'Single', kw, neg_info=[neg_keywords, neg_types])
                    else:
                        x_table = get_table(out_cols, row['Single/Group KWs'], kw)
                        x_table = modify_table(row, x_table, 'Single', kw)
                    x_table.replace('nan', value='', inplace=True)
                    dfs.append(x_table)
            else:
                kws = download_keywords(row['Keyword Link'])
                if type(row['Negative Targeting']) != float:
                    neg_keywords, neg_types = download_keywords(row['Negative Targeting'], is_neg=True)
                    x_table = get_table(out_cols, row['Single/Group KWs'], kws, neg_keywords=neg_keywords)
                    x_table = modify_table(row, x_table, 'Group', kws, neg_info=[neg_keywords, neg_types])
                else:
                    x_table = get_table(out_cols, row['Single/Group KWs'], kws)
                    x_table = modify_table(row, x_table, 'Group', kws)
                x_table.replace('nan', value='', inplace=True)        
                dfs.append(x_table)

    output_dataframe = pd.concat(dfs, ignore_index=True)
    return output_dataframe

