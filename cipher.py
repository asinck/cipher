#!/usr/bin/python

#Adam Sinck
#I wrote this program for my CSC 240 class, as part of the honors project. I
#had a lot of fun with it, and have been working on it since then. It can
#solve almost all of the cryptograms that I give it.  A good source of
#cryptograms is http://www.cryptogramcorner.org/ . I use that site because it
#is easy to copy and paste puzzles into the file that the program reads. I
#programmed it to read a file because typing the puzzle in by hand would be
#tedious and error prone.

import re, string

#this is a class for the words that the program works on. It allows each of the
#words in the puzzle to store their own unsolved string, solved string, regex, and
#other helpful data.
class Word:
    #initialize the Word
    def __init__(self, unsolved):
        self.unsolved = unsolved
        self.solved = ''
        self.length = len(unsolved)
        self.possibilities = []
        self.instances = {}
        self.regex = ''
        self.usedLetters = ''
        self.generateInstances()

    #this generates the instances table for the Word. The table contains the
    #letters in the word, along with their frequency.
    def generateInstances(self):
        for i in self.unsolved:
            if i in self.instances:
                self.instances[i] += 1
            else:
                self.instances[i] = 1

    #output
    def __str__(self):
        s =  "unsolved:      " + self.unsolved + '\n'
        s += "solved:        " + self.solved + '\n'
        s += "length:        " + str(self.length) + '\n'
        s += "regex:         " + self.regex + '\n'
        s += "instances:     " + str(self.instances) + '\n'
        s += "possibilities: " + str(self.possibilities) + '\n'
        return s

#this is where the main program begins

#global variables
#this has all of the words in the dictionary
dictionary = ''
#this has the original cipherwords
cipherWords = []
#a set of variables for the input/output
cipherString = ''
solvedString = ''
#some punctuation that the program deals with
punctuation = [",", ".", "?", ";", ":", "!",
               "(", ")", "`", "[", "]", " "]
#this is a hash table of letters and what they could represent
keys = {"'":["'"]}
#this is a list of Word objects that have not been solved
unsolvedWords = []
#this is a list of Word objects that have been solved
solvedWords = []


#the main function that drives the program
def main():
    #some initial setup
    readDict()
    getCiphers()
    getSingleLetters()
    #now for the solve

    #entries before and after track the number of keys that have been entered
    #or deleted. If these are equal, it means that no progress was made.
    #these could have errors if # deleted == # number entered
    entriesBefore = 0
    entriesAfter = 1
    while len(unsolvedWords) > 0 and entriesAfter != entriesBefore:
        solveWords()
        entriesBefore = entriesAfter
        entriesAfter = 0
        for i in keys:
            entriesAfter += len(keys[i])
    solveWords()
#    cProfile.run('solveWords()')
    #this is so that it doesn't show up in the output table
    del keys["'"]
    punctuation.append("'")
    
    #output
    print "Solved Letters:"
    index = 1
    unsolvedKeys = ''
    for i in sorted(keys):
        if len(keys[i]) == 1:
            print '[' + i + ":" +  keys[i][0] + ']',
            if index % 6 == 0:
                print ''
            index += 1
        else:
            unsolvedKeys += '\n['+i+" : "+string.join(sorted(keys[i]),', ') + '] '
    print "\nUnsolved Letters:",
    print unsolvedKeys
    print ''
    #find out how many letters were solved
    numSolved = 0
    if len(solvedWords) > 0:
        for i in keys:
            if len(keys[i.lower()]) == 1:
                numSolved += 1
    print numSolved, "letters were solved"
    print ''
    
    global cipherString, solvedString
    print "Input:"
    print cipherString
    print "Output:"
    for i in cipherString:
        if i.lower() in keys and len(keys[i.lower()]) == 1:
            if i == i.lower():
                solvedString += keys[i][0]
            else:
                solvedString += keys[i.lower()][0].upper()
        elif i.lower() in keys and len(keys[i.lower()]) < 10:
            solvedString += '[' + string.join(keys[i.lower()], '') + ']'
        elif i in punctuation:
            solvedString += i
        else:
            solvedString += '_'

    print solvedString.lower()
            
#this will try to solve all of the unsolved words
def solveWords():
    #make a new array because this should not be editing the original array
    workArray = []
    for i in unsolvedWords:
        workArray.append(i)

    while len(workArray) > 0:
        #get the longest word
        currentWord = getLongest(workArray)
        #find the possible solutions for the current word
        solutions = solveWord(currentWord)
        #see if the word was solved or not, and adjust the unsolved and solved
        #arrays as necessary
        if type(solutions) == type([]):#multiple solutions were found
            unsolvedWords.append(currentWord)
            #reset the used letter attribute
            currentWord.usedLetters = ''
        else: #the word was solved
            currentWord.solved = solutions
            unsolvedWords.remove(currentWord)
            solvedWords.append(currentWord)
            setSolvedKeys(currentWord)
        #remove the current word from the work array
        workArray.remove(currentWord)
        #update the keys based on what the word could be
        for i in currentWord.unsolved:
            updateKeys(currentWord, i, string.find(currentWord.unsolved, i))

#this tries to solve individual words
def solveWord(word):
    #start by cleaning the keys so that solved letters are not in the options
    #for other letters
    cleanKeys()
    #this will be a new regex each time the function is called
    #this will allow a the program to recursively make the regex better
    word.regex = generateRegex(word)
    #begin with the most common letter, defining it if possible
    targetLetter = getCommonLetter(word)
    #get the possible matches for the word
    word.possibilities = getMatches(word)
    #if the word was solved, set the keys as necessary and return the solution
    if len(word.possibilities) == 1:
        index = 0
        return word.possibilities[0]
    
    #target letter is the most common letter; tgtIndex is the index of
    #that letter
    tgtIndex = -1
    if targetLetter != '':
        tgtIndex = string.find(word.unsolved, targetLetter)
    
    #if word ran out of letters for matching, then tgtIndex will still be -1
    #therefore, the possible matches should be returned to be processed.
    if tgtIndex == -1 or len(word.possibilities) < 1:
        return word.possibilities
    
    #this will use recursion to solve
    #if the code got this far, then possibleMatches > 1 element,
    #and word has not run out of letters to match
    #therefore, this will update the keys and work on the word some more.
    updateKeys(word, targetLetter, tgtIndex)
    return solveWord(word)
    
#this will return a base string for the regex
def generateRegex(word):
    s = ''
    usedLetters = ''
    for i in keys:
        if len(keys[i]) == 1:
            usedLetters += keys[i][0]
    for i in word.unsolved:
        #if the letter is in the keys hash file already, add that to the regex
        if i in keys:
            s += '[' + string.join(keys[i], '') + ']'
        elif len(usedLetters) > 0:
            s += '[^' + usedLetters + ']'
        #otherwise, add a wildcard
        else:
            s += '.'
    return s

#this will do the regular expression matching
def getMatches(word):
    matches = []
    s = '\\n(' + word.regex + ')\\n'
    global dictionary
    myDict = ''
    if len(word.possibilities) > 0:
        myDict = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n\n"
        myDict += string.join(word.possibilities, '\n\n')
        myDict += "\n\nzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"
    else:
        myDict = dictionary
        
    matchArray = re.findall(s, myDict)
    if len(matchArray) > 0:
        for i in matchArray:
            #if i is a tuple, set currentMatch to the first element
            if type(('', '')) == type(i):
                currentMatch = i[0]
            #otherwise, set it to i
            else:
                currentMatch = i
            notMatched = currentMatch not in matches
            letterPattern = sameLetterPattern(word.unsolved,currentMatch)
            if notMatched and letterPattern:
                matches.append(currentMatch)
    return matches

#this will go through all the keys and remove solved letters from the
#rest of the keys
def cleanKeys():
    #get the letters that are solved or empty entries
    usedLetters = "'\n"
    emptyKeys = ''
    for i in keys:
        if len(keys[i]) == 1:
            usedLetters += keys[i][0]
        elif len(keys[i]) == 0:
            emptyKeys += i
    #remove solved letters from the rest of the keys
    for i in keys:
        for j in usedLetters:
            if j in keys[i] and len(keys[i]) > 1:
                keys[i].remove(j)
    #remove empty keys from the table
    for i in emptyKeys:
        del keys[i]

#this will find out what letters a key entry can be.
#this makes the entry such that only letters that are common between the
#current (non null) entry and the new letter set are accepted.
def updateKeys(word, targetLetter, tgtIndex):
    possibleMatches = word.possibilities
    possibleKeys = []
    index = 0
    #if there's an entry in keys for the target letter, remove any letters
    #from keys[targetLetter] that could not be correct
    if targetLetter in keys and len(keys[targetLetter]) != 0:
        for i in keys[targetLetter]:
            for j in possibleMatches:
                if i == j[tgtIndex] and i not in possibleKeys:
                    possibleKeys.append(i)
        if len(possibleKeys) > 0:
            del keys[targetLetter]
            keys[targetLetter] = possibleKeys
    #otherwise, add all of the possible letters to keys
    elif len(possibleMatches) > 0:
        keys[targetLetter] = []
        for i in possibleMatches:
            if i[tgtIndex] not in keys[targetLetter]:
                keys[targetLetter].append(i[tgtIndex])

#this will go through a word and set keys from the solved word
def setSolvedKeys(word):
    index = 0
    for i in word.unsolved:
        keys[i] = list(word.solved[index])
        index += 1

#This will check to see if the letter pattern of the two given words is the
#same. This means that there will be unique letters in the same positions,
#and repeated letters in the same positions.
def sameLetterPattern(one, two):
    a = ''
    b = ''
    hold = ''
    #for each letter in one
    for i in one:
        #if the current letter has not been in the word before,
        #add a period to indicate a unique letter
        if i not in hold:
            a += '.'
        #otherwise, add a number to indicate the first position that the
        #letter showed up
        else:
            a += str(string.find(one, i))
        hold += i
    hold = ''
    #for each letter in two
    for i in two:
        #if the current letter has not been in the word before,
        #add a period to indicate a unique letter
        if i not in hold:
            b += '.'
        #otherwise, add a number to indicate the first position that the
        #letter showed up
        else:
            b += str(string.find(two, i))
        hold += i
    #finally, return the equality of the two strings
    return a == b

#this will find any single letter words in the cryptogram and set the keys for
#that letter to 'a' or 'i', because those are the only one letter words.
def getSingleLetters():
    for i in cipherWords:
        if i.length == 1:
            keys[i.unsolved] = ['a', 'i']

#this will return the longest word in a list
def getLongest(array):
    maxLen = 0
    a = array[0]
    for i in array:
        if i.length > maxLen:
            maxLen = i.length
            a = i
    return a

#this will return the most common letter in a word
def getCommonLetter(word):
    maximum = 0
    letter = ''
    for i in word.instances:
        #if the current letter is more common than the previous most common
        #letter and this letter has not been returned before in this attempt at
        #solving the word
        if word.instances[i] > maximum and i not in word.usedLetters:
            maximum = word.instances[i]
            letter = i
    word.usedLetters += letter
    return letter

#this will read the dictionary and make an array of words
#the array that it fills will be used for the regex matching
def readDict():
    text = open("/usr/share/dict/words")
    a = []
    for i in text:
        a.append(i.lower().strip())
    text.close()
    global dictionary
    dictionary = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n\n"
    dictionary += string.join(a, "\n\n")
    dictionary += "\n\nzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"

#this will retrieve the ciphers from a file, and put them in an array
def getCiphers():
    removeChars = [",", ".", "?", ";", ":", "!", "  ", "*",
                   "(", ")", "`", "[", "]", "\n", "\t"]
    #open the file
    try:
        text = open('cipher.txt')
        
        global cipherString
        readString = ''
        #read the entire file
        for i in text:
            readString += i.strip()
        text.close()
        #remove certain characters from the string
        for i in ["  ", "*", "\n", "\t"]:
            readString = readString.replace(i, '')
        #replace "  " with " " a couple of times to help with the formatting
        readString = readString.replace('  ', ' ')
        readString = readString.replace('  ', ' ')
        cipherString = readString
#original cipher grabber code
#This is good if you only want the first line of the file
#uncomment the next several lines of code, and comment out the code to here
#    #open the file
#    text = open('cipher.txt')
#    #and grab the first line
#    global cipherString
#    cipherString = text.readline().strip()
        #split the string at spaces for the arrays that the program is going to
        #work with
        s = cipherString.split(' ')
        #for each word in the array
        for i in s:
            if i != '':
                #do some formatting on the strings
                currentWord = i.lower().strip()
                #remove punctuation and spaces from the word
                for j in removeChars:
                    currentWord = currentWord.replace(j, "")
                cipherWords.append(Word(currentWord))
            
                #remove single quotes from either end, but not from the middle
                if currentWord[0] == "'":
                    currentWord = currentWord[1:]
                if currentWord[-1] == "'":
                    currentWord = currentWord[0:-1]
    
        #make an array of unsolved words that has no duplicated words
        for i in cipherWords:
            if i not in unsolvedWords:
                unsolvedWords.append(i)
    except:
        print
        print "Error: File 'cipher.txt' not found."
        print 
        print "This program reads this file so that you don't have to type the"
        print "cipher into the program.  Please create a file called"
        print "'cipher.txt' (without quotes) in the same directory, and copy"
        print "and paste a cryptogram in."
        print 
        exit()
        
if __name__ == '__main__':
    main()
