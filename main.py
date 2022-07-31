import requests
import time
import string
import pprint
import re
from lxml import html

pp = pprint.PrettyPrinter(indent=2)
alphanumeric = re.compile(r'[^\w\s_]+')

START_TAG = "START"
END_TAG = "END"
graph = {END_TAG: {}}
occuranceDict = {}


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


def getPoem(t):
    repeat = True

    while repeat:
        t = time.time()
        poemUrl = "https://www.poetryinvoice.com/poems/senior/random?t="+str(t)
        xpath = '//*[@id="block-system-main"]/div/div/div/div[2]/div'
        r = requests.get(poemUrl)
        if r.status_code != 200:
            raise Exception("bad status code", r.status_code)
        tree = html.fromstring(r.text)
        poem = tree.xpath(xpath)
        result = ' '.join(''.join([x.text_content() for x in poem[0] if x.tag == 'p']).strip().split()).replace('"', '').replace('”', '').replace('“', '')
        print("=================")
        #print(result)
        if "CDATA" in result:
            result = ""
        smartQuoteMap = {0x201c: u'"',
                   0x201d: u'"',
                   0x2018: u"'",
                   0x2019: u"'"}

        result = result.translate(smartQuoteMap)  # remove smart quotes
        result = result.translate(str.maketrans('', '', string.punctuation))  # remove all punctuation
        result = alphanumeric.sub('', result)
        result = result.lower()  # make it all lower case

        repeat = not is_ascii(result)
        if repeat:
            print("repeating...")
    print(result)
    return result


def learnPoem(inputPoem):
    prevWord = START_TAG
    wordlist = [prevWord] + inputPoem.split(' ') + [END_TAG]
    for word in wordlist:
        if prevWord in graph:
            if word in graph[prevWord]:
                graph[prevWord][word] += 1
            else:
                graph[prevWord][word] = 1
        else:
            graph[prevWord] = {}
            graph[prevWord][word] = 1
        prevWord = word
    return graph


def trimGraph(g):
    keycount = [x for xs in [list(g[x].keys()) for x in g] for x in xs]
    incommingOccuranceDict = {x: keycount.count(x) for x in g}
    # pp.pprint(incommingOccuranceDict)
    for key in incommingOccuranceDict:
        if incommingOccuranceDict[key] < 4   and key != END_TAG and key != START_TAG:
            g.pop(key, None)
            for each in g:
                g[each].pop(key, None)
    return g


def graphString(g):
    tmp = ""
    varlist = []
    # arrayList = [[0]*len(g) for _ in range(len(g))]
    keyList = list(g.keys())
    i = 0
    for key_i in range(len(keyList)):
        tmp += f'const char s_{i}[] PROGMEM = "{keyList[key_i]}";\n'
        varlist.append(f's_{i}')

        i += 1
    tmp += f"const char *const word_array[] PROGMEM = {{{','.join(varlist)}}};\n"
    # const Node a PROGMEM = {1, 2};
    # node index, count
    for src in keyList:
        nodeList = []
        for dest in graph[src]:
            nodeName = 'n_' + src + '_' + dest
            tmp += f"const Node {nodeName} PROGMEM = {{ {keyList.index(dest)}, {graph[src][dest]} }};\n"
            nodeList.append(nodeName)
        tmp += f"const Node {'na_' + src}[] PROGMEM = {{ {','.join(['& '+x for x in nodeList])} }};\n"
        tmp += f"const OutgoingEdges {'e_'+src} PROGMEM = {{ {'na_' + src}, {len(nodeList)} }};\n"

    tmp += f"const OutgoingEdges *const edgeList[] PROGMEM = {{ {','.join(['&e_'+x for x in keyList])} }};\n"

    return tmp


if __name__ == "__main__":
    for i in range(50):
        learnPoem(getPoem(time.time()))
        time.sleep(0.25)
    with open("output.txt", "w") as f:
        f.write(graphString(trimGraph(graph)))
    wordLen = {word: len(word) for word in graph.keys()}
    pp.pprint(sorted(wordLen, key=lambda x: wordLen[x], reverse=True))
    print("=============================================================")
    print(max([graph[x][y] for x in graph for y in graph[x]]))
    print(len(graph))
