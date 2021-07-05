import hashlib

def getFingerprint(hdict):
    # returns a String of 160 bits fingerprint
    fingerprintList = []
    for i in range(160):
        ithValue = 0
        for key in hdict:
            ithBit = int(key[i])
            if ithBit == 0:
                ithValue -= hdict[key]
            else:
                ithValue += hdict[key]
        if ithValue <= 0:
            fingerprintList.append(0)
        else:
            fingerprintList.append(1)
    return (''.join([str(x) for x in fingerprintList]))
        
def getWordHash(word):
    # returns a string of 160 bits of the word
    shaValue = hashlib.sha1(word.encode())
    hexValue = shaValue.hexdigest()
    binValue = bin(int(hexValue, 16))[2:].zfill(160) # 8 bit
    return str(binValue)

def getNumSimilarFloat(binA, binB):
    # returns a float of the ratio of similar bits between them
    same = 0
    for i in range(160):
        if binA[i] == binB[i]:
            same += 1
    return same / 160

def scraper():    
    global uniqueHashSet


    ### CODE BETWEEN HERE

    hashDict = dict()
    for word in tokensWithoutStop:
        '''
        if word not in commonWords:
            commonWords[word] = 1
        else:
            commonWords[word] += 1
        '''
        
        # creating the dict for this url
        wordHash = getWordHash(word)
        if wordHash not in hashDict:
            hashDict[wordHash] = 1
        else:
            hashDict[wordHash] += 1

    fingerprint = getFingerprint(hashDict)

    for fp in uniqueHashSet:
        if getNumSimilarFloat(fingerprint, fp) >= 0.95:
            return list(extract_next_links(url, resp))
    uniqueHashSet.add(fingerprint)

    