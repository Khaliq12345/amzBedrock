import pandas as pd
import dateparser
import pandas
from datetime import datetime
import gdown
from warnings import filterwarnings

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

def get_table(cols: list, keyword_type: str, keywords: list):
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
    df = pd.DataFrame(items, columns=cols)
    return df

# a file
def download_keywords(file_url):
    output = "kw.txt"
    gdown.download(file_url, output, fuzzy=True, quiet=True)
    with open('kw.txt', 'r') as f:
        kws = f.readlines()
        kws = [k.replace('\n', '') for k in kws]
    return kws

def modify_table(row, x_table, kw_type, kws):
    #Generating the campaign name
    no_nan = lambda x: '' if type(x) != str else x
    single_kw = f"{row['SKU']}_SP_KW_{row['Match Type']}_{row['ASIN']}_{no_nan(row['Campaign Name Modifier'])}_{kws}"
    kw_not_single = f"{row['SKU']}_SP_KW_{row['Match Type']}_{row['ASIN']}_{no_nan(row['Campaign Name Modifier'])}"
    make_campaign_name = lambda x: single_kw if 'Single' in x else kw_not_single #make campaign name
    campaign_name = make_campaign_name(row['Single/Group KWs'])
    
    #operation
    x_table['Operation'] = 'create'
    
    #campaign id
    x_table['Campaign ID'] = campaign_name
    
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
    x_table.loc[x_table['Entity'].isin(['Campaign', 'Bidding Adjustment']), 'Bidding Strategy'] = 'Dynamic bids - down only'
    
    #Placement
    placement_values = ['Placement Product Page', 
                        'Placement Rest Of Search', 
                        'Placement Top']
    x_table.loc[x_table['Entity'] == 'Bidding Adjustment', 'Placement'] = placement_values
    
    #Percentage
    perc = lambda x: x*100 if x > 0.0 else 0
    perc_values = [
        perc(row['Placement Product Page']),
        perc(row['Placement Rest Of Search']),
        perc(row['Placement Top'])
    ]
    x_table.loc[x_table['Entity'] == 'Bidding Adjustment', 'Percentage'] = perc_values
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
    dfs = []
    input_df['Placement Top'] = input_df['Placement Top'].apply(lambda x: float(x.replace('%', ''))/100 if type(x) == str else x)
    input_df['Placement Product Page'] = input_df['Placement Product Page'].apply(lambda x: float(x.replace('%', ''))/100 if type(x) == str else x)
    input_df['Placement Rest Of Search'] = input_df['Placement Rest Of Search'].apply(lambda x: float(x.replace('%', ''))/100 if type(x) == str else x)
    input_df['Portfolio ID'] = input_df['Portfolio ID'].astype(str)
    for i, row in input_df.iterrows():
        if type(row['SKU']) != float:
            #get the row table
            if 'Single' in row['Single/Group KWs']:
                kws = download_keywords(row['Keyword Link'])
                for kw in kws:
                    x_table = get_table(out_cols, row['Single/Group KWs'], kw)
                    x_table = modify_table(row, x_table, 'Single', kw)
                    dfs.append(x_table)
            else:
                kws = download_keywords(row['Keyword Link'])
                x_table = get_table(out_cols, row['Single/Group KWs'], kws)
                x_table = modify_table(row, x_table, 'Group', kws)        
                dfs.append(x_table)

    output_dataframe = pd.concat(dfs)
    return output_dataframe

