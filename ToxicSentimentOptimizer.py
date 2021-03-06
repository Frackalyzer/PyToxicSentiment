"""
ToxicSentimentOptimizer.py
"""

import csv
import re
import pickle
import sys

from nltk.corpus import stopwords
from textblob import classifiers

max_rows_used = 1000  # 0 means unlimited
max_rows_test = 10  # 0 means unlimited

file_encoding = 'utf-8'
file_eol_char = '\n'
rows_per_batch = 100

classifier_type = 'NaiveBayes'

src_folder = 'F:/Kaggle/ToxicCommentClassificationChallenge'
tgt_folder = 'F:/Kaggle/ToxicCommentClassificationChallenge'

training_files = {
    'toxic': f'{src_folder}/train_toxic.csv',
    'severe_toxic': f'{src_folder}/train_severe_toxic.csv',
    'obscene': f'{src_folder}/train_obscene.csv',
    'threat': f'{src_folder}/train_threat.csv',
    'insult': f'{src_folder}/train_insult.csv',
    'identity_hate': f'{src_folder}/train_identity_hate.csv',
    'bad_words': f'{src_folder}/bad_words_sorted.txt',
    'positive_words': f'{src_folder}/positive_words_sorted.txt'
}

use_train_files_list = ['bad_words', 'toxic']
use_test_files_list = ['toxic']

trainer_field_names = [
    "comment_text",
    "sentiment"
]

testing_field_names = [
    "id",
    "sentiment",
    "comment_text"
]

accuracy_field_names = [
    "comment_text",
    "sentiment"
]

pos_neg_dict = {
    '0': 'pos',
    '1': 'neg'
}

regexs = {
    'http': re.compile(r"http.?://[^\s]+[\s]?", re.IGNORECASE),
    'https': re.compile(r"https.?://[^\s]+[\s]?", re.IGNORECASE),
    'numbers': re.compile(r"\s?[0-9]+\.?[0-9]*", re.IGNORECASE)
}

test_rows = [
    ("it's a bitch", "neg"),
    ("fuck y'all", "neg"),
    ("Jane saw a dog", "pos"),
    ("Billy is a cat", "pos"),
    ("Steve is an asshole", "neg"),
    ("Thebes is a city", "pos"),
    ("Santorini is an asshat island", "neg"),
    ("Phoenix is a fucking hot city", "neg"),
    ("Flagstaff is a very cool city", "pos"),
    ("Sedona is an elite city", "pos")
]

csv.register_dialect('this_projects_dialect',
                     delimiter=',',
                     quotechar='"',
                     quoting=csv.QUOTE_MINIMAL,
                     lineterminator=file_eol_char)

cached_stopwords = stopwords.words("english")
extend_stopwords = [
    "a"
]
cached_stopwords.extend(extend_stopwords)


# replace pattern characters with replacement characters
# until the source string has no pattern characters remaining
def replace_chars(src_str, pat_chars='  ', rpl_chars=' '):
    while src_str.find(pat_chars) > -1:
        src_str = src_str.replace(pat_chars, rpl_chars)
    return src_str


# cleanse source string of
# any non-alphanumeric characters,
# allowing single spaces as the exception
def cleanse_text(src_str):
    src_str = src_str.lower()
    for regex_compiled in regexs.values():
        src_str = re.sub(regex_compiled, '', src_str, re.MULTILINE)
    tmp_str_1 = src_str \
        .replace(file_eol_char, ' ') \
        .replace('-', ' ') \
        .replace('_', ' ') \
        .replace('.', ' ') \
        .replace(',', ' ') \
        .replace(';', ' ') \
        .replace("'", '') \
        .replace(':', ' ')
    tmp_str_1 = replace_chars(tmp_str_1, '  ', ' ')
    tmp_str_2 = ''
    for c in tmp_str_1:
        if c.isalnum() or c in [" ", "'"]:
            tmp_str_2 += c
    tmp_str_2 = replace_chars(tmp_str_2, '  ', ' ')
    # remove stop words from text
    tmp_str_2 = ' '.join([word for word in tmp_str_2.split() if word not in cached_stopwords])
    tmp_str_2 = tmp_str_2.strip()
    return tmp_str_2


for key in use_train_files_list:

    training_file_path = training_files[key]

    classifier = None
    rows_read = 0
    rows_used = 0
    with open(training_file_path,
              'r',
              newline='',
              encoding=file_encoding) as training_file:

        csv_dict_reader = csv.DictReader(training_file,
                                         fieldnames=trainer_field_names,
                                         dialect='this_projects_dialect')

        first_batch = True
        rows = []
        for row in csv_dict_reader:
            rows_read += 1
            if key == 'bad_words':
                sentiments = ['neg']
            else:
                sentiments = ['pos']
            if row['sentiment'] in sentiments:
                rows_used += 1
                row_text = row['comment_text'].replace(file_eol_char, ' ')
                row_text = cleanse_text(row_text)
                # create a text, sentiment tuple
                # and append it to the rows to
                # be used to update the classifier
                rows.append((row_text, row['sentiment']))
                if rows_used % rows_per_batch == 0:
                    if first_batch:
                        if classifier_type == 'NaiveBayes':
                            classifier = classifiers.NaiveBayesClassifier(rows)
                        elif classifier_type == 'DecisionTree':
                            classifier = classifiers.DecisionTreeClassifier(rows)
                        else:
                            print(f'Invalid classifier type specified: {classifier_type}')
                            sys.exit(1)
                        first_batch = False
                    else:
                        classifier.update(rows)
                        print(f'classifier.accuracy: {classifier.accuracy(rows)}')
                    rows.clear()
                    msg = f'{key} {classifier_type} classifier updated, rows read, used: {rows_read:,}, {rows_used:,}'
                    print(msg)

            if rows_used >= max_rows_used > 0:
                break

        if first_batch:
            if classifier_type == 'NaiveBayes':
                classifier = classifiers.NaiveBayesClassifier(rows)
            elif classifier_type == 'DecisionTree':
                classifier = classifiers.DecisionTreeClassifier(rows)
            else:
                print(f'Invalid classifier type specified: {classifier_type}')
                sys.exit(1)
            print(f'classifier.accuracy: {classifier.accuracy(rows)}')
            first_batch = False
        else:
            classifier.update(rows)
            print(f'classifier.accuracy: {classifier.accuracy(rows)}')
        rows.clear()
        msg = f'{key} {classifier_type} classifier updated, rows read, used: {rows_read:,}, {rows_used:,}'
        print(msg)

    print(f'Pickling of {key} {classifier_type} classifier started')
    pickle_file_path = f'{tgt_folder}/Classifier_{classifier_type}_{key}.pickle'
    with open(pickle_file_path, 'wb') as pickle_file:
        pickle.dump(classifier, pickle_file, protocol=pickle.HIGHEST_PROTOCOL, fix_imports=False)
    print(f'Pickling of {key} {classifier_type} classifier finished')
    print('========================================================')

    print(classifier.accuracy(test_rows))

    rows = []
    for row in test_rows:
        rows.append((cleanse_text(row[0]), row[1]))
    classifier.update(rows)
    for row in rows:
        sentiment = classifier.classify(row[0])
        if sentiment != row[1]:
            print(f'row: {row}, sentiment: {sentiment}')

with open(training_files['toxic'],
          'r',
          newline='',
          encoding=file_encoding) as testing_file:
    csv_dict_reader = csv.DictReader(testing_file,
                                     fieldnames=testing_field_names,
                                     dialect='this_projects_dialect')
    rows_read = 0
    for row in csv_dict_reader:
        rows_read += 1
        comment_text = cleanse_text(row['comment_text'])
        sentiment = classifier.classify(comment_text)
        if sentiment != row['sentiment']:
            print(f'row: {comment_text}, sentiment: {sentiment}')
        if rows_read >= max_rows_test > 0:
            break

classifier.show_informative_features(100)

