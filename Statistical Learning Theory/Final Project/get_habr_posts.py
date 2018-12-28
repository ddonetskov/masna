#!/usr/bin/env python3

import habr

import time

habr_web_f = habr.Habr('web', 'https://habr.com/post/')

for i in range(0,434500+1):

    print('Fetching the post %6d... ' % i, end='')

    post = habr_web_f.get_post(i)

    if post is not None:

        print('got with the status code %d of the size %8d.' % (post.fetch_code, len(post.html)))

        file_name_no_ext = '%s/%06d' % (habr.dir_raw, i)

        if post.fetch_code == 200:

            with open(file_name_no_ext + '.html', 'w', encoding='utf-8') as f:
                f.write(post.html)

        else:

            with open(file_name_no_ext + '.err.html', 'w', encoding='utf-8') as f:
                f.write(post.html)

            with open(file_name_no_ext + '.err.code', 'w', encoding='utf-8') as f:
                f.write(str(post.fetch_code))

    else:

        print('got None.')
    
    time.sleep(0.1)