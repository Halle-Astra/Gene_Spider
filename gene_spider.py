'''This script is coded for gene spider. After testing, string 'Genomic details' can be used to discriminate htmls whether have objects or not.
'''
import requests as rq
import os
import pandas as pd
from lxml import etree

html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Title</title>
</head>
<body>
#Content_Replace
</body>
</html>'''

column_names = ['Locus',
 'Locus name ',
 'Symbol ',
 'Gene activity ',
 'Description ',
 'Chromosome ',
 'Arm'] ## Gotten by xpath('//div/table/tr/td[1]//text()') of ajax content.
column_names = [i.strip()  for i in column_names]

if __name__ == '__main__':
    if os.path.exists('result.csv'):
        input_csv = 'result.csv'
        df_input = pd.read_csv(input_csv)
    else:
        input_csv = 'all_genes.csv'
        df_input = pd.read_csv(input_csv)  # input column is `gene`
        nums_gene = len(df_input)
        for column_name in column_names:
            df_input[column_name] = ['None'] * nums_gene
        df_input['Available'] = ['#'] * nums_gene

    home_url = 'https://solgenomics.net'
    query_string_midfix = '/search/quick?term='
    ajax_url_template = 'https://solgenomics.net/jsforms/locus_ajax_form.pl?object_id=#ID#&action=view'  # Use it by replacing #ID#

    cnt = 0
    for gene_code in df_input['gene']:
        cnt+=1
        # gene_code = 'Solyc04g009860'
        if (df_input['Available'][df_input['gene']==gene_code] != '#').values[0]:
            continue

        query_url = home_url+query_string_midfix+gene_code
        r = rq.get(query_url)
        if 'Genomic details' in r.text:
            html = etree.HTML(r.text)
            url_sub = html.xpath('//*[@id="main_row"]/div[2]/div[5]/div/dl/dd[1]/ul/li/a/@href')
            url_sub = url_sub[0]
            locus_id = url_sub.split('=')[-1]
            gene_url = ajax_url_template.replace('#ID#', locus_id)
            r = rq.get(gene_url)
            ajax_content = eval(r.text.replace('null','None'))['html'].replace('<br/>','')
            html = etree.HTML(html_template.replace('Content_Replace', ajax_content))
            column_names_returned = html.xpath('//div/table/tr/td[1]//text()')
            column_names_returned = [i.strip() for i in column_names]
            table = html.xpath('//div/table/tr/td[2]//text()')
            table = [i.strip() for i in table]
            values_dict = dict(zip(column_names_returned, table))
            available = 1
        else:
            table = ['']*len(column_names)
            values_dict = dict(zip(column_names, table))
            available = 0
        for i, column_name in enumerate(column_names):
            if column_name not in values_dict:
                values_dict[column_name] = ''
            df_input[column_name][df_input['gene'] == gene_code] = values_dict[column_name]
            df_input['Available'][df_input['gene'] == gene_code] = available
        print(gene_code, '\t', values_dict)
        if cnt % 20==0:
            df_input.to_csv('result.csv',index = None)