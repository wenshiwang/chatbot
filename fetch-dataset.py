# Crawl and organize corpus from the immigration rules website

import requests
from bs4 import BeautifulSoup, NavigableString
import os
import pickle


# Make sure these dir exist
if not os.path.exists('tmp'):
    os.mkdir('tmp')

if not os.path.exists('ret'):
    os.mkdir('ret')

'''
It is found that there are two types of landing pages.
H model has sub-columns that can be clicked on by the mouse.
P-type, does not have, but a direct document.
Generally, they are H type, and part 10 is P type.

Therefore, there are two types of crawling processes.
'''

def downloadForLinkTypeH(link):
    '''
   H-type download process, first download the HTML text of the web page, and then use BeautifulSoup to parse the HTML content,
     Extract what you need from it.
     For type H, its List is in the element whose class is gem-c-govspeak. For it, the title <h2><h3> is
     As its Question, and the plain text under it as Answer.
    '''
    r = requests.get(link)
    with open('tmp/h.html', 'w') as fp:
        fp.write(r.text)
    sp = BeautifulSoup(r.text)
    elem = sp.find(attrs={'class':'gem-c-govspeak'})
    print(elem)
    qaList = []
    lastQ = []
    lastA = []
    for child in elem.children:
        if isinstance(child, NavigableString) or child.name == None:
            continue

        if child.name == 'h3' or child.name == 'h2':
            if len(lastQ) + len(lastA) > 0:
                qaList.append([lastQ, lastA])
                lastQ = []
                lastA = []
            lastQ.append(child.text)
        else:
            lastA.append(child.text)

    if len(lastQ) + len(lastA) > 0:
        qaList.append([lastQ, lastA])

    for qa in qaList:
        qa[0] = ','.join(qa[0])
        qa[1] = ','.join(qa[1])
    
    return qaList

def downloadForLinkTypeP(link):
    '''
    Similar to H model, the specific extraction location is different。
    '''
    r = requests.get(link)
    with open('tmp/p.html', 'w') as fp:
        fp.write(r.text)
    sp = BeautifulSoup(r.text)

    qaList = []
    lastQ = []
    lastA = []
    for elem in sp.find_all(attrs={'class':'legislative-list'}):
        print(elem)
        for child in elem.children:
            if child.name == 'li':
                for i, cc in enumerate(child.children):
                    if cc.name == None:
                        text = cc
                    else:
                        text = cc.text
                    if i == 0:
                        lastQ.append(text)
                    else:
                        lastA.append(text)
                qaList.append([lastQ, lastA])
                lastQ = []
                lastA = []

    for qa in qaList:
        #clean up empty segments
        qa[0] = list(filter(lambda x: len(x.strip())>0, qa[0]))
        qa[1] = list(filter(lambda x: len(x.strip())>0, qa[1]))

        qa[0] = ','.join(qa[0])
        qa[1] = ','.join(qa[1])
    
    return qaList

# This is the web page link that needs fetch, and the second parameter is its type
entryLinks = [['https://www.gov.uk/guidance/immigration-rules/immigration-rules-part-3-students', 'h'],
['https://www.gov.uk/guidance/immigration-rules/immigration-rules-part-1-leave-to-enter-or-stay-in-the-uk', 'h'],
['https://www.gov.uk/guidance/immigration-rules/immigration-rules-part-5-working-in-the-uk', 'h'],
['https://www.gov.uk/guidance/immigration-rules/immigration-rules-part-10-registering-with-the-police','p']]

def main():
    qaList = []

    # Download the web pages one by one and extract QA
    for link in entryLinks:
        print('gather from', link[0])
        if link[1] == 'h':
            qaList.extend(downloadForLinkTypeH(link[0]))
        elif link[1] == 'p':
            qaList.extend(downloadForLinkTypeP(link[0]))

    # The following is to clean up some spam
    # filter out empty
    qaList = list(filter(lambda qa:len(qa[0]) > 0 and len(qa[1]) > 0, qaList))

    # filter out deleted
    qaList = list(filter(lambda qa:'DELETED' not in qa[1] and len(qa[1]) > 0, qaList))

    print('we got qa tuples, len=', len(qaList))
    for qa in qaList:
        print('Q:', qa[0])
        print('A:', qa[1])
        print()

    # write down, serialize them
    # Directly serialize and store here, so that it can be read directly in use without parsing;
    fn = 'ret/new-corpus.pydump'
    f = open(fn, 'wb')
    pickle.dump(qaList, f)
    f.close()
    print('Corpus saved to ', fn)
    print('DONE')

    # In order to be able to view the contents of corpus intuitively, a txt file is also output
    with open('ret/corpus-show.txt', 'w') as fp:
        for i, qa in enumerate(qaList):
            fp.write('#{} Q:'.format(i) + qa[0] + '\n')
            fp.write('A:' + qa[1] + '\n')
            fp.write('\n')
            fp.write('----------------------------------------\n')
            fp.write('\n')


main()
