


import re
import gc
import json
from collections import defaultdict
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

ps = PorterStemmer()

class Index():
	"""class for processing and the wikipedia document and storing the index file"""
	def __init__(self):
		self.index = defaultdict(list)
		self.collection = defaultdict(dict)
		self.sw = set(stopwords.words('english'))
		self.collectionFile = './data/wiki_01'
		self.indexFile = 'index.json'
		self.colFile = 'testCollection.json'

	def getTerms(self,line):
		""" @Input str of words
			@Output list of stemmed words (excluding stopwords)
		"""
		line = line.lower()
		line = re.sub(r'[^\w\d ]',' ',line)
		line = line.split(' ')
		line = [ps.stem(x) for x in line if x not in self.sw]
		return line

	def getPageInfo(self, file):
		"""
			@returns list of dict which contains 'id', 'title', 'text' of pages
		"""
		with open(file,'r') as inf:
			text = inf.read()
		decoder = json.JSONDecoder()
		doc = {}
		while True:
			obj, remain = decoder.raw_decode(text)
			doc[obj['id']] = obj
			text = text[remain:].strip()
			print(obj['id'],len(text),len(doc))
			if len(text)==0:
				break

		self.collection = doc
		self.writeColfile(self.colFile)
		return doc

	def writeColfile(self,file):
		with open(file,'w') as fout:
			json.dump(self.collection,fout)

	def writeIndexfile(self,file):
		with open(file, 'w') as fout:
		    json.dump(self.index, fout)

	def generateIndex(self):
		"""
			Generate the indexfile from collection data and saves the term, doc, position info in index file
		"""
		gc.disable()
		# collectionFile = 'testCollection.dat'
		# indexFile = 'index.json'
		collectionFile = self.collectionFile
		indexFile = self.indexFile
		allPages = self.getPageInfo(collectionFile)
		for pageid,pagedict in allPages.items():
			lines='\n'.join((pagedict['title'],pagedict['text']))
			pageid=int(pagedict['id'])
			terms=self.getTerms(lines)

			termdictPage={}
			for position, term in enumerate(terms):
				try:
					termdictPage[term][1].append(position)
				except:
					termdictPage[term]=[pageid, [position]]
			for termpage, postingpage in termdictPage.items():
				self.index[termpage].append(postingpage)

		gc.enable()
		self.writeIndexfile(indexFile)


if __name__ == '__main__':
	c = Index()
	c.generateIndex()

