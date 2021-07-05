import re
from hashForScraper import *
from PartA import textProcess
from urllib.parse import urlparse, urldefrag
from bs4 import BeautifulSoup

uniqueUrls = set()      # a set that keeps track of all the unique urls we scrapped
longestPage = None      # a tuple ("url",wordcount) keep track of the url with maximum word count
commonWords = dict()    # a dictionary <"word":frequency> that keeps track of most common words
subdomainICS = dict()   # a dictionary <"subdomain":frequency>
stopWords = set()       # a set of stop words
uniqueHashSet = set()   # a set of unique hash IDs for similarity detection

with open("stopWords.txt") as f:
    for line in f:
        stopWords.add(line.strip('\n'))

blackList = set()
with open("blackList.txt") as f:
    for line in f:
        blackList.add(line.strip('\n'))


def scraper(url, resp):
    global longestPage
    global commonWords
    global stopWords
    global subdomainICS
    links = set()
    if resp.status >= 200 and resp.status <= 399:
        if resp.raw_response:
            html = resp.raw_response.content
            soup = BeautifulSoup(html, 'html.parser')
            # extract only the text from the page
            text = soup.get_text(" ", strip=True)

            # tokenize the text while checking for unuseful webpage
            t = textProcess()
            tokens = t.tokenize(text)
            tokensWithoutStop = []
            stopWordsCount = 0
            for word in tokens:
                if word not in stopWords:
                    tokensWithoutStop.append(word)
                else:
                    stopWordsCount += 1

            # skip scraping for info if the file is too big or not useful
            if stopWordsCount > 0.5 * len(tokens):
                return list(extract_next_links(url, resp))
            if len(tokens) > 10000:
                return list(extract_next_links(url, resp))

            # update the url with the most words
            if not longestPage:
                longestPage = (url, len(tokensWithoutStop))
            else:
                if len(tokensWithoutStop) > longestPage[1]:
                    longestPage = (url, len(tokensWithoutStop))

            # store the word counts in a dictionary for most common words
            hashDict = dict()
            for word in tokensWithoutStop:
                if word not in commonWords:
                    commonWords[word] = 1
                else:
                    commonWords[word] += 1

                # creating the hash dict for this url
                wordHash = getWordHash(word)
                if wordHash not in hashDict:
                    hashDict[wordHash] = 1
                else:
                    hashDict[wordHash] += 1

            # generate fingerprint for current url
            fingerprint = getFingerprint(hashDict)

            # if the fingerprint of the current url is similar to a hash id in our set
            # return an empty list without scraping new urls from the current url
            for fp in uniqueHashSet:
                if getNumSimilarFloat(fingerprint, fp) >= 0.95:
                    print("DETECTED SIMILAR PAGE:", url)
                    return []
            uniqueHashSet.add(fingerprint)

            # count number of subdomains in ics.uci.edu
            parsed = urlparse(url)
            if ".ics.uci.edu" in url:
                subdomain = parsed[0] + "://" + parsed[1]
                if subdomain not in subdomainICS:
                    subdomainICS[subdomain] = 1
                else:
                    subdomainICS[subdomain] += 1

            # store all the information to a text file
            generate_report()

            # scrap all the urls form the page
            links = extract_next_links(url, resp)
    return [link for link in links]

def generate_report():
    file1 = open("report.txt", "w+")
    file1.write("Unique Pages: {}\n\n".format(len(uniqueUrls)))
    file1.write("Longest Page: {}\n\n".format(longestPage))
    file1.write("50 Most Common Words: \n")
    wordList = [(k,v) for k, v in commonWords.items()]
    sortedWords = sorted(wordList, key=lambda x: x[1], reverse=True)
    for i in range(50):
        file1.write("{} -> {}\n".format(sortedWords[i][0], sortedWords[i][1]))
    file1.write("\nSubdomain List: \n")
    for i in subdomainICS:
        file1.write("{}, {}\n".format(i, subdomainICS[i]))
    file1.close()

# returns a set of valid, unique, de-fragmented urls
def extract_next_links(url, resp):
    global uniqueUrls
    urls = set()    # a set that keeps track of only the urls scrapped from this url
    html = resp.raw_response.content
    soup = BeautifulSoup(html, 'html.parser')
    # extract all the urls from the url
    for link in soup.find_all('a'):
        newUrl = link.get('href')         # get a new url from the given url

        # if url is in blacklist, don't add it to the set and continue
        parsed = urlparse(newUrl)
        if parsed[0] and parsed[1] and parsed[2]:
            urlWithPath = "{}://{}/{}".format(parsed[0], parsed[1], parsed[2].split('/')[1])
            if urlWithPath in blackList:
                print("BLOCKED: {}".format(newUrl))
                continue

        newUrl = urldefrag(newUrl)[0]     # de-fragment the new url
        if newUrl not in uniqueUrls and is_valid(newUrl):
            print(newUrl)
            urls.add(newUrl)           # add url to local urls set
            uniqueUrls.add(newUrl)     # add url to global urls set to keep track of # of unique pages
    return urls

def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        if not re.search(
                r"(\.ics\.uci\.edu|"
                + r"\.cs\.uci\.edu|"
                + r"\.informatics\.uci\.edu|"
                + r"\.stat\.uci\.edu"
                + r"|today\.uci\.edu\/department\/information_computer_sciences)$", parsed.netloc):
            return False

        checkList = [parsed.path.lower(), parsed.query.lower(), parsed.params.lower()]

        for i in checkList:
            if re.match(
                    r".*\.(css|js|bmp|gif|jpe?g|ico"
                    + r"|png|tiff?|mid|mp2|mp3|mp4"
                    + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                    + r"|ps|eps|tex|ppt|pptx|ppsx|doc|docx|xls|xlsx|names"
                    + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                    + r"|epub|dll|cnf|tgz|sha1|war|apk|mat"
                    + r"|thmx|mso|arff|rtf|jar|csv"
                    + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", i):
                return False

        return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise