import datetime as dt
import re
import os

import paramiko
import requests

from bs4 import BeautifulSoup
import json

import pandas as pd

# some global variables
dir_raw       = 'D:/Temp/01_habr_raw/'
dir_parsed    = 'D:/Temp/02_habr_parsed/'
dir_processed = 'D:/Temp/03_habr_processed/'

fn_raw_pattern = '%d.html'
fn_parsed_parquet_pattern = re.compile('habr_posts_[0-9]{6}-[0-9]{6}.parquet')

class Habr():
    """
    The class to manage the content of habr.com
    
    Parameters
    ----------    
    source_type: str ('web', 'sqlite', 'ssh', 'file')
        the source type:
        - 'web': the website,
        - 'sqlite': the sqlite database
        - 'ssh': a server accessible by ssh
        - 'dir': a directory with the files
    path: str
        a pointer to the source, the format depends on the source type
    """
    
    def __init__(self, source_type, path):
        
        if source_type == 'dir':
            
            self.source_type = source_type
            self.dir = path
        
        elif source_type == 'ssh':
            
            self.source_type = source_type
            self.path = path

            self.ssh_client = paramiko.SSHClient()
            hostname = re.search('@(.+?):', path).group(1)
            username = re.search('(.+?)@', path).group(1)
            self.dir = re.search(':(.+)', path).group(1)
            # self.ssh_client.load_system_host_keys()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())            
            self.ssh_client.connect(hostname=hostname, username=username, compress=False)
            self.sftp_client = self.ssh_client.open_sftp()            
        
        elif source_type == 'web':
            
            self.source_type = source_type
            if path is None:
                self.path = 'https://habr.com/post/'
            else:
                self.path = path
                    
        else:
            raise ValueError('The source type ''%s'' is not implemented' % source_type)
            
            
    def get_post(self, n, copy_to_dir = None):
        
        """

        """
        
        hp = None

        file_name = fn_raw_pattern % n
        
        if self.source_type == 'dir':
            
            try:
                path = self.dir + file_name
                with open(path, encoding='utf8') as f:
                    post = f.read()
                stat = os.stat(path)
                hp = HabrPost(html=post, fetch_time=dt.datetime.fromtimestamp(stat.st_mtime))
            except FileNotFoundError:
                return(None)
        
        elif self.source_type == 'ssh':
            
            try:
                with self.sftp_client.file(self.dir + '/' + file_name) as sftp_file:
                    post = sftp_file.read().decode('utf8')
                    stat = sftp_file.stat()
                hp = HabrPost(html=post, fetch_time=dt.datetime.fromtimestamp(stat.st_mtime))
            except FileNotFoundError:
                return(None)
            
        elif self.source_type == 'web':
            
            post_url = self.path + str(n)
            r  = requests.get(post_url)
            if r.status_code == 200:
                hp = HabrPost(html=r.text, fetch_time=dt.datetime.now(), fetch_code=r.status_code)
            else:
                hp = HabrPost(html=r.text, fetch_time=dt.datetime.now(), fetch_code=r.status_code)

                
        if copy_to_dir is not None:
            with open(copy_to_dir + '/' + file_name, 'w', encoding='utf8') as f:
                f.write(hp.html)

        return(hp)
    
class HabrPost():
    
    """
    Handles the content of an individual post
    """
    
    def __init__(self, html=None, fetch_time=None, fetch_code=None):
        
        self.html = html
        self.fetch_time = fetch_time
        self.fetch_code = fetch_code
        
    def get_post_info(self):

        """
        Parses and returns an information about a post as the dictionary
        """

        page = BeautifulSoup(self.html, 'lxml')

        post_info = {}

        # meta
        property_list = {
                 'type': {'property':'og:type'},
                 'title': {'property':'og:title'},
                 'description': {'property':'og:description'},
                 'locale': {'property':'og:locale'},
                 'url': {'property':'og:url'},
                 'keywords': {'name':'keywords'}}

        for property_name, property_attrs in property_list.items():
            res = page.find('meta', attrs=property_attrs)
            if res is None:
                post_info[property_name] = ''
            else:
                post_info[property_name] = res['content'].strip()

        # span
        property_list = {
                 'user': {'class':'user-info__nickname user-info__nickname_small'},
                 'post_time': {'class': 'post__time'},
                 'bookmarks': {'class':'bookmark__counter js-favs_count'},
                 'views': {'class': 'post-stats__views-count'},
                 'comments_no': {'class': 'post-stats__comments-count'},
                 'type_label': {'class':'post__type-label'}}

        for property_name, property_attrs in property_list.items():
            res = page.find('span', attrs=property_attrs)
            if res is None:
                post_info[property_name] = ''
            else:
                post_info[property_name] = res.string

        post_info['title_html'] = page.title.string

        post_info['voting'] = page.find('span', attrs={'class':'voting-wjt__counter'})['title']

        # if the html page contains the json structure for the mobile platforms
        res = page.find('script', attrs={'type':'application/ld+json'})
        
        if res is not None:
            
            j = json.loads(res.string)

            post_info['app_type']           = j['@type']
            post_info['app_datePublished']  = j['datePublished']
            post_info['app_dateModified']   = j['dateModified']

            post_info['app_author_type']    = j['author']['@type']
            post_info['app_author_name']    = j['author']['name']

            post_info['app_publisher_type'] = j['publisher']['@type']
            post_info['app_publisher_name'] = j['publisher']['name']

        # hubs
        hubs = []
        for hub in page.select('ul.post__hubs li.inline-list__item_hub'):
            hubs.append(hub.a.string)
        post_info['hubs'] = ';'.join(hubs)
        # print('Hubs: %s' % hubs)

        # tags
        tags = []
        for tag in page.select('li.inline-list__item_tag'):
            tags.append(tag.a.string)
        post_info['tags'] = ';'.join(tags)
        # print('Tags: %s' % tags)

        # user stats
        post_info['user_specialization'] = page.find('div', attrs={'class':'user-info__specialization'}).string
        user_info = page.find('div', attrs={'class':'media-obj__body media-obj__body_user-info'})
        if user_info is not None:
            t = user_info.find('div', attrs={'class':'user-info__stats-item stacked-counter'})
            if t is not None:
                post_info['user_votes'] = t['title']
            t = user_info.find('div', attrs={'class':'stacked-counter__value stacked-counter__value_green '})
            if t is not None:
                post_info['user_karma'] = t.string
            t = user_info.find('div', attrs={'class':'stacked-counter__value stacked-counter__value_magenta'})
            if t is not None:    
                post_info['user_rating'] = t.string
            t = user_info.find('div', attrs={'class':'stacked-counter__value stacked-counter__value_blue'})
            if t is not None:
                post_info['user_followers'] = t.string
                
        # for translated posts
        post_translatation = page.find('a', attrs={'class':'post__translatation-link'})
        if post_translatation is not None:
            post_info['translation_title'] = post_translatation['title']
            post_info['translation_link']  = post_translatation.string        
        
        # extracting the post's text
        post_text = page.find('div', attrs={'class':'post__text post__text-html js-mediator-article'})
        if post_text is not None:
            post_info['text'] = post_text.get_text(' ', strip=True)

        return(post_info)


def process_habr_batch(habr, start_id, batch_size, batches, copy_to_dir=None, output_dir=None):

    df_list = []

    for batch_no in range(batches):

        batch_start_id = start_id + batch_no*batch_size
        batch_end_id   = start_id + (batch_no+1)*batch_size - 1

        post_infos = {}
        exceptions = {}

        for post_id in range(batch_start_id, batch_end_id+1):

            try:
                hp = habr.get_post(post_id, copy_to_dir=copy_to_dir)
                if hp is None:
                    # print('The post %d is absent' % i)
                    continue
                post_info = hp.get_post_info()
                post_info['post_fetch_time'] = hp.fetch_time
                post_info['post_fetch_code'] = hp.fetch_code
                post_infos[post_id] = post_info
            except Exception as e:
                exceptions[post_id] = str(e)

        dfp = pd.DataFrame.from_dict(post_infos, orient='index')
        dfe = pd.DataFrame.from_dict(exceptions, orient='index').rename(columns={0:'msg'})

        # processing data if there is any
        if len(dfp) > 1:

            # dropping the nanosecond precision
            dfp['post_fetch_time'] = dfp['post_fetch_time'].astype('datetime64[ms]')
        
            if output_dir is not None:
                
                try:

                    data_type = 'posts'
                    dfp.to_parquet('%s/habr_posts_%06d-%06d.parquet' % (output_dir, batch_start_id, batch_end_id))

                    data_type = 'exceptions'
                    if len(dfe) > 0:
                        dfe.to_parquet('%s/habr_posts_%06d-%06d_exceptions.parquet' % (output_dir, batch_start_id, batch_end_id))

                except Exception as e:

                    print('An exception when writing %s: %s' % (data_type, str(e)))
            
            df_list.append(dfp)

        print('%s: the batch %d is completed' % (pd.datetime.now(), batch_no))

    if len(df_list) == 1:
        df = df_list[0]
    elif len(df_list) > 1:
        df = pd.concat(df_list)
    else:
        df = pd.DataFrame()
    
    return(df)