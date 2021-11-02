'''This script is coded for gene spider. After testing, string 'Genomic details' can be used to discriminate htmls whether have objects or not.
'''
import requests as rq
import os
import pandas as pd
from lxml import etree
import time
from multiprocessing import Pool

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
                'Arm']  ## Gotten by xpath('//div/table/tr/td[1]//text()') of ajax content.
column_names = [i.strip() for i in column_names]

home_url = 'https://solgenomics.net'
query_string_midfix = '/search/quick?term='
ajax_url_template = 'https://solgenomics.net/jsforms/locus_ajax_form.pl?object_id=#ID#&action=view'  # Use it by replacing #ID#

num_proc = 48

def spider_process(gene_code):
    query_url = home_url + query_string_midfix + gene_code
    r = rq.get(query_url)
    if 'Genomic details' in r.text:
        html = etree.HTML(r.text)
        url_sub = html.xpath('//*[@id="main_row"]/div[2]/div[5]/div/dl/dd[1]/ul/li/a/@href')
        url_sub = url_sub[0]
        if url_sub[-8:] == '/details':
            gene_details_url = home_url + url_sub
            r = rq.get(gene_details_url)
            html = etree.HTML(r.text)
            elements = html.xpath('//div[@class="infosectioncontent"]/table[2]')
            values_dict = dict()
            for i in range(len(elements)):
                key = html.xpath('//div[@class="infosectioncontent"]/table[2]//tr[{}]/td/span//text()'.format(i + 1))
                key = [i.strip() for i in key]
                key = [i for i in key if i]
                key = ' '.join(key)
                value = html.xpath('//div[@class="infosectioncontent"]/table[2]//tr[{}]/td/div//text()'.format(i + 1))
                value = [i.strip() for i in value]
                value = [i for i in value if i]
                value = ' '.join(value)
                values_dict[key] = value
            available = 2
        else:
            locus_id = url_sub.split('=')[-1]
            gene_url = ajax_url_template.replace('#ID#', locus_id)
            r = rq.get(gene_url)
            ajax_content = eval(r.text.replace('null', 'None'))['html'].replace(' <br/>', '')
            html = etree.HTML(html_template.replace('Content_Replace', ajax_content))
            column_names_returned = html.xpath('//div/table/tr/td[1]//text()')
            column_names_returned = [i.strip() for i in column_names]
            # table = html.xpath('//div/table/tr/td[2]//text()')
            # table = [i.strip() for i in table]
            # values_dict = dict(zip(column_names_returned, table))
            elements = html.xpath('//div/table/tr')
            values_dict = dict()
            for i in range(len(elements)):
                key = html.xpath('//div/table/tr[{}]/td[1]//text()'.format(i + 1))
                key = [i.strip() for i in key]
                key = [i for i in key if i]
                key = ' '.join(key)
                value = html.xpath('//div/table/tr[{}]/td[2]//text()'.format(i + 1))
                value = [i.strip() for i in value]
                value = [i for i in value if i]
                value = ' '.join(value)
                values_dict[key] = value
            available = 1
    else:
        table = [''] * len(column_names)
        values_dict = dict(zip(column_names, table))
        available = 0
    return values_dict, available


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

    time_begin = time.time()

    pool = Pool(num_proc)
    res_ls = []
    genes = []
    for cnt, gene_code in enumerate(df_input['gene']):
        # gene_code = 'Solyc04g009860'
        # gene_code = 'Solyc01g005290'
        # gene_code = 'Solyc00g012540'
        if (df_input['Available'][df_input['gene'] == gene_code] != '#').values[0]:
            continue
        genes.append(gene_code)
        res = pool.apply_async(spider_process, args=(gene_code,))
        res_ls.append(res)
        if (cnt + 1) % num_proc == 0:
            pool.close()
            pool.join()
            for j, res in enumerate(res_ls):
                values_dict, available = res.get()
                gene_code = genes[j]
                for i, column_name in enumerate(column_names):
                    if column_name not in values_dict:
                        values_dict[column_name] = ''
                    df_input[column_name][df_input['gene'] == gene_code] = values_dict[column_name]
                    df_input['Available'][df_input['gene'] == gene_code] = available
            pool = Pool(num_proc)
            res_ls = []
            genes = []

            time_now = time.time()
            print(cnt, '{}s'.format(time_now - time_begin), gene_code, '\t', values_dict)
            df_input.to_csv('result.csv', index=None)
