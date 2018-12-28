import concurrent.futures

import habr

import re
import os

def run_batch(working_dir, start_id, batch_size):
        
    from subprocess import run

    script_path = os.path.join(working_dir, 'run_one_batch.py')
    run(['python.exe', script_path, str(start_id), str(batch_size)])

def main():

    _, _, filenames = next(os.walk(habr.dir_parsed), (None, None, []))

    batch_size = 1000
    start_id_list   = list(range(0, 436000, batch_size))

    for fn in filenames:
        m = re.search('habr_posts_([0-9]+)-[0-9]+\.parquet', fn)
        if m:
            start_id = int(m[1])
        else:
            continue
        print('Found the file %s with the start_id %d, skipping it' % (fn, start_id))
        # remove these start_id's from the lists as they are already processed
        start_id_list.remove(start_id)

    batch_size_list = [batch_size] * len(start_id_list)

    print('The list of start_id''s to process: %s' % start_id_list)

    working_dir = [os.getcwd().replace('\\', '/')] * len(start_id_list)
    # print('The working dir is %s' % working_dir)

    with concurrent.futures.ProcessPoolExecutor(max_workers=5) as executor:
        print('Within the executors loop...')
        res = executor.map(run_batch, working_dir, start_id_list, batch_size_list)

if __name__ == '__main__':
    main()