import pandas as pd
import dateparser
import pandas
from datetime import datetime
import gdown
from warnings import filterwarnings
import uuid
import os

filterwarnings('ignore')

out_cols = ['Product',
 'Entity',
 'Operation',
 'Campaign ID',
 'Portfolio ID',
 'Ad Group ID',
 'Ad ID',
 'Targeting ID',
 'Campaign Name',
 'Ad Group Name',
 'Start Date',
 'End Date',
 'State',
 'Tactic',
 'Budget Type',
 'Budget',
 'SKU',
 'ASIN',
 'Ad Group Default Bid',
 'Bid',
 'Bid Optimization',
 'Cost Type',
 'Targeting Expression',
]

def get_table(cols: list, target_type:str, targets:list, asin=False):
    if asin:
        items = []
        items.append({
            'Product': "Sponsored Display",
            'Entity': 'Campaign'
        })
        items.append({
            'Product': "Sponsored Display",
            'Entity': 'Ad Group'
        })
        items.append({
            'Product': "Sponsored Display",
            'Entity': 'Product Ad'
        })
        for target in targets:
            items.append({
                'Product': "Sponsored Display",
                'Entity': target_type
            })        
    else:
        items = []
        items.append({
            'Product': "Sponsored Display",
            'Entity': 'Campaign'
        })
        items.append({
            'Product': "Sponsored Display",
            'Entity': 'Ad Group'
        })
        items.append({
            'Product': "Sponsored Display",
            'Entity': 'Product Ad'
        })
        items.append({
            'Product': "Sponsored Display",
            'Entity': target_type
        })   
    df = pd.DataFrame(items, columns=cols)
    return df

def get_targets(file_url, type_):
    x_name = str(uuid.uuid1())
    output = f"{x_name}.csv"
    if type_ == 'list':
        gdown.download(file_url, output, fuzzy=True, quiet=True)
        df = pd.read_csv(output, header=None)
        os.remove(output)
        return df[0].to_list()
    elif type_ == 'df':
        gdown.download(file_url, output, fuzzy=True, quiet=True)
        df = pd.read_csv(output, header=None)
        os.remove(output)
        return df[0].to_list(), df[1].to_list()
    else:
        print('Please check your type: The only supported types are list and df')

def processing_targets(row):
    asins = targetings = categories = None
    if (row['Targeting'] == 'Contextual Targeting') and (row['Contextual Targeting'] == 'asin'):
        asins = get_targets(row['Contextual Targeting Targeting File'], 'list')
        return asins
    elif (row['Targeting'] == 'Contextual Targeting') and (row['Contextual Targeting'] == 'category'):
        targetings, categories = get_targets(row['Contextual Targeting Targeting File'], 'df')
        return targetings, categories
    elif (row['Targeting'] == 'Audience Targeting') and ('Category' in row['Audience Targeting']):
        targetings, categories = get_targets(row['Audience Targeting Targeting File'], 'df')
        return targetings, categories

def parse_date(date_str):
    adder = lambda x: f'0{x}' if len(x) < 2 else x
    parse_date = dateparser.parse(date_str)
    year = parse_date.year
    month = adder(str(parse_date.month))
    day = adder(str(parse_date.day))
    return f'{year}{month}{day}'

def common_df_processor(x_table, campaign_name, row):
    x_table['Campaign Name'] = campaign_name  
    x_table['Campaign ID'] = campaign_name
    x_table['Portfolio ID'] = row['Portfolio ID']
    x_table.loc[x_table['Entity'] != 'Campaign', 'Ad Group ID'] = campaign_name
    x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Name'] = campaign_name
    #date
    x_table.loc[x_table['Entity'] == 'Campaign', 'Start Date'] = parse_date(str(row['Start Date']))
    #state
    enable_pause = lambda x: 'enabled' if x == 'yes' else 'paused'
    x_table.loc[x_table['Entity'].isin(['Campaign', 'Ad Group']), 'State'] = enable_pause(row['Activate Campaign and Ad Group'])
    x_table.loc[~(x_table['Entity'].isin(['Campaign', 'Ad Group'])), 'State'] = 'enabled'
    #Budget
    x_table.loc[x_table['Entity'] == 'Campaign', 'Budget Type'] = 'daily'
    x_table.loc[x_table['Entity'] == 'Campaign', 'Budget'] = row['Daily Budget']
    #sku and asin
    console_sc_vc = lambda x, y, value: y if x == value else None
    x_table.loc[x_table['Entity'] == 'Product Ad', 'SKU'] = console_sc_vc(row['Console'], row['SKU'], 'SC')
    x_table.loc[x_table['Entity'] == 'Product Ad', 'ASIN'] = console_sc_vc(row['Console'], row['ASIN'], 'VC')
    #Bid
    x_table.loc[x_table['Entity'] == 'Ad Group', 'Ad Group Default Bid'] = row['Bid']
    #Bid optimization
    x_table.loc[x_table['Entity'] == 'Ad Group', 'Bid Optimization'] = row['Bid Optimization']
    return x_table

def proccess_df(input_df: pd.DataFrame):
    input_df.dropna(how='all')
    input_df = input_df.loc[2:]
    dfs = []
    input_df['Portfolio ID'] = input_df['Portfolio ID'].astype(str)
    for i, row in input_df.iterrows():
        #option 1
        if (row['Targeting'] == 'Contextual Targeting') and (row['Contextual Targeting'] == 'asin'):
            targets = processing_targets(row)
            x_table = get_table(out_cols, 'Contextual Targeting', targets, asin=True)
            x_table['Operation'] = 'create'
            #cost type
            cost_type_selector = lambda x: f"cpc_{x.split(' ')[-1]}" if (x == 'Optimize for page visits') or (x == 'Optimize for conversions') else f"vcpm_{x.split(' ')[-1]}"
            x_table.loc[x_table['Entity'] == 'Campaign', 'Cost Type'] = cost_type_selector(row['Bid Optimization'])
            #targeting expression
            targeting_exp_values = [f'asin="{t}"' for t in targets]
            x_table.loc[x_table['Entity'] == 'Contextual Targeting', 'Targeting Expression'] = targeting_exp_values
            #campaign name
            cost_type = cost_type_selector(row['Bid Optimization'])
            if row['Defense'] == 'yes':
                campaign_name = f"SD_{row['SKU']}_{row['ASIN']}_{cost_type}_ASIN Targeting_Defense"
            else:
                campaign_name = f"SD_{row['SKU']}_{row['ASIN']}_{cost_type}_ASIN Targeting"
            x_table.loc[x_table['Entity'] == 'Campaign', 'Tactic'] = 'T00020'
            x_table = common_df_processor(x_table, campaign_name, row)
            dfs.append(x_table)

        #option 2
        elif (row['Targeting'] == 'Contextual Targeting') and (row['Contextual Targeting'] == 'category'):
            targets = processing_targets(row)
            for cat, cat_name in zip(targets[0], targets[1]):
                x_table = get_table(out_cols, 'Contextual Targeting', [], asin=False)
                x_table['Operation'] = 'create'
                #cost type
                cost_type_selector = lambda x: f"cpc_{x.split(' ')[-1]}" if (x == 'Optimize for page visits') or (x == 'Optimize for conversions') else f"vcpm_{x.split(' ')[-1]}"
                x_table.loc[x_table['Entity'] == 'Campaign', 'Cost Type'] = cost_type_selector(row['Bid Optimization'])
                #targeting expression
                targeting_exp_value = f'category="{cat}"'
                x_table.loc[x_table['Entity'] == 'Contextual Targeting', 'Targeting Expression'] = targeting_exp_value
                #campaign name
                cost_type = cost_type_selector(row['Bid Optimization'])
                if row['Defense'] == 'yes':
                    campaign_name = f"SD_{row['SKU']}_{row['ASIN']}_{cost_type}_{cat_name}_Defense"
                else:
                    campaign_name = f"SD_{row['SKU']}_{row['ASIN']}_{cost_type}_{cat_name}"
                x_table.loc[x_table['Entity'] == 'Campaign', 'Tactic'] = 'T00020'
                x_table = common_df_processor(x_table, campaign_name, row)
                dfs.append(x_table)

        # option 3
        elif (row['Targeting'] == 'Audience Targeting') and (('Category' in row['Audience Targeting'])):
            targets = processing_targets(row)
            for cat, cat_name in zip(targets[0], targets[1]):
                x_table = get_table(out_cols, 'Audience Targeting', [], asin=False)
                x_table['Operation'] = 'create'
                #cost type
                cost_type_selector = lambda x: f"cpc_{x.split(' ')[-1]}" if (x == 'Optimize for page visits') or (x == 'Optimize for conversions') else f"vcpm_{x.split(' ')[-1]}"
                x_table.loc[x_table['Entity'] == 'Campaign', 'Cost Type'] = cost_type_selector(row['Bid Optimization'])
                #targeting expression
                if 'views-Category' in row['Audience Targeting']:
                    targeting_exp_value = f'views=(category="{cat}" lookback={row["Lookback"].replace("days", "")})'
                    tev = f"views-category-{cat_name}-lookback-{row['Lookback']}"
                elif 'purchases-Category' in row['Audience Targeting']:
                    targeting_exp_value = f'purchases=(category="{cat}" lookback={row["Lookback"].replace("days", "")})'
                    tev = f"purchases-category-{cat_name}-lookback-{row['Lookback']}"
                else:
                    targeting_exp_value = None
                x_table.loc[x_table['Entity'] == 'Audience Targeting', 'Targeting Expression'] = targeting_exp_value
                #campaign name
                cost_type = cost_type_selector(row['Bid Optimization'])
                campaign_name = f"SD_{row['SKU']}_{row['ASIN']}_{cost_type}_{tev}_Retargeting"
                x_table.loc[x_table['Entity'] == 'Campaign', 'Tactic'] = 'T00030'
                x_table = common_df_processor(x_table, campaign_name, row)
                dfs.append(x_table)
        
        #option 4
        elif (row['Targeting'] == 'Audience Targeting') and (('Category' not in row['Audience Targeting'])):
            x_table = get_table(out_cols, 'Audience Targeting', [], asin=False)
            x_table['Operation'] = 'create'
            #cost type
            cost_type_selector = lambda x: f"cpc_{x.split(' ')[-1]}" if (x == 'Optimize for page visits') or (x == 'Optimize for conversions') else f"vcpm_{x.split(' ')[-1]}"
            x_table.loc[x_table['Entity'] == 'Campaign', 'Cost Type'] = cost_type_selector(row['Bid Optimization'])
            #targeting expression
            if 'views-Advertised products' in row['Audience Targeting']:
                targeting_exp_value = f"views=(exact-product lookback={row['Lookback'].replace('days', '')})"
                tev = f"views-exact-product lookback-{row['Lookback']})"
            elif 'views-Related to advertised products' in row['Audience Targeting']:
                targeting_exp_value = f"views=(similar-product lookback={row['Lookback'].replace('days', '')})"
                tev = f"views-similar-product lookback-{row['Lookback']})"
            elif 'purchases-Advertised products' in row['Audience Targeting']:
                targeting_exp_value = f"purchases=(exact-product lookback={row['Lookback'].replace('days', '')})"
                tev = f"purchases-exact-product lookback-{row['Lookback']})"
            elif 'purchases-Related to advertised products' in row['Audience Targeting']:
                targeting_exp_value = f"purchases=(related-product lookback={row['Lookback'].replace('days', '')})"
                tev = f"purchases-related-product lookback-{row['Lookback']})"
            x_table.loc[x_table['Entity'] == 'Audience Targeting', 'Targeting Expression'] = targeting_exp_value
            #campaign name
            cost_type = cost_type_selector(row['Bid Optimization'])
            campaign_name = f"SD_{row['SKU']}_{row['ASIN']}_{cost_type}_{tev}_Retargeting"
            x_table.loc[x_table['Entity'] == 'Campaign', 'Tactic'] = 'T00030'
            x_table = common_df_processor(x_table, campaign_name, row)
            dfs.append(x_table)

    output_dataframe = pd.concat(dfs, ignore_index=True)
    return output_dataframe
