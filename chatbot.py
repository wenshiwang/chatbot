import json
import re
import string
import nltk
import queue
from matplotlib import pyplot
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle

def load_corpus():
    """
    load the corpus from crawl.py dumped file
    ret/*.pydump
    """


    f = open('ret/new-corpus.pydump', 'rb')
    qaList = pickle.load(f)
    f.close()

    # qalist format is [[Q,A],...]
    # refold to old format

    question_list = [x[0] for x in qaList]
    answer_list = [x[1] for x in qaList]

    print('get qlist len', len(question_list))
    print('get alist len', len(answer_list))

    return question_list, answer_list


def corpus_statistic_gen(question_list):
    '''
    analysis word frequency and draw as a plot
    '''
    all_words = []
    word_map = {}
    for qline in question_list:
        mywords = qline[0:-1].strip().split(' ')
        all_words += mywords
        for word in mywords:
            if word in word_map:
                word_map[word] += 1
            else:
                word_map[word] = 1

    sorted_words = sorted(word_map.items(), key=lambda x: x[1], reverse=True)

    show_len = min(20, len(sorted_words))
    x = range(show_len)
    y = [c[1] for c in sorted_words[:show_len]]

    print('Word frequence:')
    for i in x:
        word, count = sorted_words[i]
        print(i, word, count)

    showGraph = False

    if showGraph:
        # draw the graph
        pyplot.figure()
        pyplot.plot(x, y)
        pyplot.show()


def fetch_my_words(text):
    pattern = re.compile('[{}]'.format(
        re.escape(string.punctuation)))
    text = pattern.sub("", text)
    words = text.lower().split()
    return words

def prepare_question(raw_question, stop_words, mystemmer):
    word_list = fetch_my_words(raw_question)
    word_list = filter(lambda w: w not in stop_words, word_list)
    word_list = ["#number" if word.isdigit() else word for word in word_list ]
    word_list = [mystemmer.stem(word) for word in word_list ]

    real_input = ' '.join(word_list)
    return real_input

def top5results(the_question, question_list_prepared, answer_list, stop_words, mystemmer):
    
    real_input = prepare_question(the_question, stop_words, mystemmer)
    print('prepared question', real_input)
    vectorizer = TfidfVectorizer(smooth_idf=False)
    X = vectorizer.fit_transform(question_list_prepared)
    vec_input = vectorizer.transform([real_input])
    ret = cosine_similarity(vec_input, X)[0]

    pqueue = queue.PriorityQueue()
    for i, v in enumerate(ret):
        pqueue.put((1.0 - v, i))

    top_answers = []
    top_indexs = []
    for i in range(5):
        top_indexs.append(pqueue.get()[1])

    return top_indexs

def getTopAnswer(question, qlist, alist, stop_words, mystemmer):
    topIndexs = top5results(question, qlist, alist, stop_words, mystemmer)
    print('top 5 index', topIndexs)

    return topIndexs[0], alist[topIndexs[0]]

def main():
    stop_words = set(nltk.corpus.stopwords.words('english'))
    mystemmer = nltk.stem.porter.PorterStemmer()
    question_list, answer_list = load_corpus()
    corpus_statistic_gen(question_list)

    question_list_prepared = [prepare_question(x, stop_words, mystemmer) for x in question_list]

    # evaluation
    print('Start evaluating...')
    countAll = 0
    countPass = 0
    fpwrite = open('ret/eva-result.txt', 'w')
    with open('dataset/eva.txt', 'r') as fp:
        evaQlines = fp.readlines()
        for qline in evaQlines:
            if len(qline) > 5 and ',' in qline:
                countAll += 1
                ww = qline.split(',')
                questionIndex = int(ww[0][1:])
                questionString = ww[1]
                print('for question:', questionIndex, questionString)
                fpwrite.write('Q:' + qline + '\n')
                ai, ans = getTopAnswer(questionString, question_list_prepared, answer_list, stop_words, mystemmer)
                # print('we get answer', ans)
                if ai == questionIndex:
                    print('the answer is corrent')
                    countPass += 1

                    fpwrite.write('A(OK):')
                else:
                    print('the answer is bad')
                    fpwrite.write('A(NG):')
                fpwrite.write(ans + '\n\n-----------------------\n\n')


    passRate = countPass * 1.0 / countAll
    retText = 'For {} question, {} passed, pass rate={}'.format(countAll, countPass, passRate)
    print(retText)
    fpwrite.write(retText + '\n')
    fpwrite.close()

    # interaction QA
    print('Start test QA...')
    while True:
        print()
        print()
        question = input('>>>>>>>>>>>>>>>>>>>>>>What is your question?')
        print('Question:', question)
        if 'exit' in question or len(question) < 3:
            print('quit')
            break
        print('ANSWER:', getTopAnswer(question, question_list_prepared, answer_list, stop_words, mystemmer)[1])

if __name__ == '__main__':
    main()
