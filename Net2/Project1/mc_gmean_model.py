import logging

import re
import sys

import zipfile

import pandas as pd
import scipy
import sklearn
import statsmodels.api as sm

import nltk

# create logger
logger = logging.getLogger('main')



class text_file_tokenizer:

    def __init__(self, file_name, lang = 'English'):

        self.file_name = file_name
        self.lang      = lang

    def tokenize(self, start_marker = None, end_marker = None, mask_fn = None, transform_fn = None):

        """Separate the file into tokens

        :returns:          list of tokens

        """

        with zipfile.ZipFile(self.file_name) as zfile:
            text = zfile.read(zfile.namelist()[0]).decode('utf-8')

        logger.debug('Read the textual information of the length %d' % len(text))

        m = re.search(start_marker + '(.+?)' + end_marker, text, re.DOTALL)

        if m:
            text = m[1]

        logger.debug('The length after taking the part between the markers: %d' % len(text))

        tokens = nltk.tokenize.word_tokenize(text, language = self.lang)

	# we may wish to use a specialized tokenizer for Latin
	# http://cltk.org/blog/2015/08/02/tokenizing-latin-text.html

        # filter out
        if mask_fn != None:

            tokens = filter(mask_fn, tokens)

        # transform
        if transform_fn != None:

            tokens = list(map(lambda t: transform_fn(t), tokens))

        return(tokens)



class mc_gmean_model:

    def __init__(self):

        from collections import defaultdict

        # list of sequences with their counts
        self.seq_counts = defaultdict(int)

        # transition matrix as dictionary
        self.tm_dict = defaultdict(dict)

        # transition matrix as Data Frame
        self.tm   = pd.DataFrame()

        # states
        self.seqs = pd.DataFrame()

    def transition_matrix(self, sequences):

        """Build the transition matrix
        """

        for seq in sequences:

            self.seq_counts[seq] += 1

            for i in range(len(seq) - 1):

                try:
                    c = self.tm_dict[seq[i]][seq[i+1]]
                except KeyError:
                    self.tm_dict[seq[i]][seq[i+1]] = 0

                self.tm_dict[seq[i]][seq[i+1]] += 1

            # tm now contains the dictionary of transitions

        self.tm = pd.DataFrame(self.tm_dict).fillna(0).astype('int').transpose().sort_index()

        # adding missing columns
        for column_name in self.tm.index.difference(self.tm.columns):
            self.tm[column_name] = 0

        self.tm = self.tm.sort_index(axis=1)

        # converting to probabilities

        for r in self.tm.index:
            s = self.tm.loc[r].sum()
            self.tm.loc[r] = self.tm.loc[r].apply(lambda x: x/s)
            # checking the transition matrix is stationary
            s = round(self.tm.loc[r].sum())
            if s != 1:
                raise ValueError('The matrix is not stationary for %s (sum = %.2f)' % (r, s))

    # returns the vector of probabilities according to the transition matrix tm for s
    def tm_prob_vector(self, sequence, tm = None):

        if tm is None:
            tm = self.tm

        prob_vectory = []

        for i in range(len(sequence) - 1):
            try:
                prob_vectory.append(tm.loc[sequence[i]][sequence[i + 1]])
            except KeyError:
                raise ValueError('Some elements of the given sequence () does not belong to the set E' % (sequence[i], sequence[i+1]))
        return (prob_vectory)

    def compute_seqs(self, tm = None):

        if tm is None:
            tm = self.tm

        # creating from the dictionary
        self.seqs = pd.Series(self.seq_counts).to_frame().rename(columns={0: 'count'})
        #self.seqs = pd.Series({k: len(k) for k, v in self.seq_counts.items()}).to_frame().rename(columns = {0: 'length'})

        self.seqs['length'] = self.seqs.apply(lambda  seq: len(seq.name), axis = 1)

        self.seqs['prob_gmean'] = self.seqs.apply(lambda seq: scipy.stats.mstats.gmean(self.tm_prob_vector(seq.name, tm)), axis=1)

    def describe(self):
        """Basic info of the model
        """

        print('The number of sequences: %d'   % len(self.seqs))
        print('The minimal length:      %.2f' % self.seqs['length'].min())
        print('The maximum length:      %.2f' % self.seqs['length'].max())
        print('The average length:      %.2f' % self.seqs['length'].mean())
