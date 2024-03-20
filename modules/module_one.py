import pandas as pd
import dateparser
from datetime import datetime

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

def get_table(cols: list):
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
    for i in range(4):
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
    return df

def parse_date(date_str):
    adder = lambda x: f'0{x}' if len(x) < 2 else x
    parse_date = dateparser.parse(date_str)
    year = parse_date.year
    month = adder(str(parse_date.month))
    day = adder(str(parse_date.day))
    return f'{year}{month}{day}'

def proccess_df(input_df: pd.DataFrame):
    input_df.dropna(how='all')
    dfs = []
    input_df['Placement Top'] = input_df['Placement Top'].apply(lambda x: float(x.replace('%', ''))/100 if type(x) == str else x)
    input_df['Placement Product Page'] = input_df['Placement Product Page'].apply(lambda x: float(x.replace('%', ''))/100 if type(x) == str else x)
    input_df['Placement Rest Of Search'] = input_df['Placement Rest Of Search'].apply(lambda x: float(x.replace('%', ''))/100 if type(x) == str else x)
    input_df['Portfolio ID'] = input_df['Portfolio ID'].astype(str)
    for i, row in input_df.iterrows():
        if type(row['SKU']) != float:
            x_table = get_table(out_cols)
            campaign_name = f"{row['SKU']}_SP_Auto_{row['ASIN']}"
            x_table['Operation'] = 'create'
            x_table['Campaign ID'] = campaign_name
            x_table.loc[x_table['Entity'] != 'Campaign', 'Ad Group ID'] = campaign_name
            x_table.loc[x_table['Entity'] == 'Campaign', 'Portfolio ID'] = row['Portfolio ID']
            x_table.loc[x_table['Entity'] == 'Campaign', 'Campaign Name'] = campaign_name
            x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Name'] = campaign_name
            x_table.loc[x_table['Entity'] == 'Campaign', 'Start Date'] = parse_date(str(row['Start Date']))
            x_table.loc[x_table['Entity'] == 'Campaign', 'Targeting Type'] = 'Auto'
            enable_pause = lambda x: 'enabled' if x == 'yes' else 'paused'
            x_table.loc[x_table['Entity'] == 'Product Ad', 'State'] = 'enabled'
            x_table.loc[x_table['Entity'].isin(['Campaign', 'Ad Group']), 'State'] = enable_pause(row['Activate Campaign and Ad Group'])
            targets = ['loose-match', 'close-match', 'complements', 'substitutes']
            x_table.loc[x_table['Entity'] == 'Product Targeting', 'State'] = [enable_pause(row[t]) for t in targets]
            x_table.loc[x_table['Entity'] == 'Campaign', 'Daily Budget'] = row['Daily Budget']
            console_sc_vc = lambda x, y, value: y if x == value else None
            x_table.loc[x_table['Entity'] == 'Product Ad', 'SKU'] = console_sc_vc(row['Console'], row['SKU'], 'SC')
            x_table.loc[x_table['Entity'] == 'Product Ad', 'ASIN'] = console_sc_vc(row['Console'], row['ASIN'], 'VC')
            x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Default Bid'] = row['Bid']
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
            x_table.loc[x_table['Entity'].isin(['Product Targeting']), 'Product Targeting Expression'] = targets
            dfs.append(x_table)

    output_dataframe = pd.concat(dfs, ignore_index=True)
    return output_dataframe











