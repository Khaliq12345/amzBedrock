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

def get_table(cols: list, keyword_type: str, keywords: list):
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
    for i in range(3):
            items.append({
                'Product': "Sponsored Products",
                'Entity': "Bidding Adjustment"
            })
    if 'Single' in keyword_type:
        items.append({
            'Product': "Sponsored Products",
            'Entity': 'Keyword', 
        })
    else:
        for keyword in keywords:
            items.append({
                'Product': "Sponsored Products",
                'Entity': 'Keyword', 
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

def proccess_df(input_df: pd.DataFrame, kws: list):
    dfs = []
    input_df['Placement Top'] = input_df['Placement Top'].apply(lambda x: float(x.replace('%', ''))/100 if type(x) == str else x)
    input_df['Placement Product Page'] = input_df['Placement Product Page'].apply(lambda x: float(x.replace('%', ''))/100 if type(x) == str else x)
    input_df['Placement Rest Of Search'] = input_df['Placement Rest Of Search'].apply(lambda x: float(x.replace('%', ''))/100 if type(x) == str else x)
    input_df['Portfolio ID'] = input_df['Portfolio ID'].astype(str)
    for i, row in input_df.iterrows():
        if type(row['SKU']) != float:
            #get the row table
            x_table = get_table(out_cols, row['Single/Group KWs'], kws)
            
            #Generating the campaign name
            single_kw = f"{row['SKU']}_SP_KW_{row['Match Type']}_{row['ASIN']}_{row['Campaign Name Modifier']}_{kws[0]}"
            kw_not_single = f"{row['SKU']}_SP_KW_{row['Match Type']}_{row['ASIN']}_{row['Campaign Name Modifier']}"
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
            if 'Single' in row['Single/Group KWs']:
                target_kw = kws[0]
            else:
                target_kw = kws
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
            
            dfs.append(x_table)

    output_dataframe = pd.concat(dfs)
    return output_dataframe

