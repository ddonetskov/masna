import argparse

import habr

parser = argparse.ArgumentParser(description='Process the command-line arguments.')
parser.add_argument('start_id',   type=int, help='the start id')
parser.add_argument('batch_size', type=int, help='the number of items to process')

args = parser.parse_args()
   
start_id   = args.start_id
batch_size = args.batch_size
batches    = 1

habr_ssh  = habr.Habr('ssh', 'dmdp@192.168.1.2:/mnt/data_1/Temp/01_habr_raw')

print('Processing the batch: %d, %d, %d' % (start_id, batch_size, batches))

df = habr.process_habr_batch(habr=habr_ssh, 
                             start_id=start_id, 
                             batch_size=batch_size, 
                             batches=batches, 
                             output_dir=habr.dir_parsed)
    
print('Has successfully built the dataframe of the shape %s for %d, %d, %d' % (str(df.shape), start_id, batch_size, batches))