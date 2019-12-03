


import re
import gc
import os
import json
import math
from collections import defaultdict
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

ps = PorterStemmer()

class Index():
	
	def __init__(self):
		self.index = defaultdict(list)
		self.collection = defaultdict(dict)
		with open('stopWords.dat','r') as inf:
			self.sw = set([ x.strip() for x in inf.readlines()])
		self.sw = self.sw | set(stopwords.words('english'))
		self.collectionFile = './data/testCollection.dat'
		self.indexFile = 'index.dat'
		self.colFile = 'testCollection.json'
		self.numDocuments = 0
		self.tf = defaultdict(list)
		self.df = defaultdict(int)

	def getTerms(self,line):
		""" @Input str of words
			@Output list of stemmed words (excluding stopwords)
		"""
		line = line.lower()
		line = re.sub(r'[^a-z0-9 ]',' ',line)
		line = line.split()
		line = [ps.stem(x) for x in line if x not in self.sw]
		return line

	def getPageInfo(self, file):
		"""
			@returns list of dict which contains 'id', 'title', 'text' of pages
		"""
		with open(file,'r') as inf:
			text = inf.readlines()
		doc=[]
		doc_details = {}
		cur_start = 0
		while True:
			for line in range(cur_start, len(text)):
				if text[line]=='</page>\n':
					cur_start = line+1
					break
				doc.append(text[line])

			curPage=''.join(doc)
			pageid=re.search('<id>(.*?)</id>', curPage, re.DOTALL)
			pagetitle=re.search('<title>(.*?)</title>', curPage, re.DOTALL)
			pagetext=re.search('<text>(.*?)</text>', curPage, re.DOTALL)

			if pageid==None or pagetitle==None or pagetext==None:
				break
				# return {}

			d={}
			d['id']=pageid.group(1)
			d['title']=pagetitle.group(1)
			d['text']=pagetext.group(1)
			doc_details[d['id']] = d
			print(d['id'],len(doc_details))
			doc = []
		self.collection = doc_details
		self.writeColfile(self.colFile)
		return doc_details


	def writeColfile(self,file):
		with open(file,'w') as fout:
			json.dump(self.collection,fout)


	def writeIndexfile(self,file):
		if os.path.isfile(file):
			os.remove(file)
		with open(file, 'a') as fout:
			print(self.numDocuments,file=fout)
			self.numDocuments=float(self.numDocuments)
			for term in self.index.keys():
				postinglist=[]
				for p in self.index[term]:
					docID=p[0]
					positions=p[1]
					postinglist.append(':'.join([str(docID) ,','.join(map(str,positions))]))

				postingData=';'.join(postinglist)
				tfData=','.join(map(str,self.tf[term]))
				idfData='%.7f' % (self.numDocuments/self.df[term])
				print('|'.join((term, postingData, tfData, idfData)),file=fout)


	def generateIndex(self):
		"""
			Generate the indexfile from collection data and saves the term, doc, position info in index file
		"""
		gc.disable()
		collectionFile = self.collectionFile
		indexFile = self.indexFile
		allPages = self.getPageInfo(collectionFile)
		for pageid,pagedict in allPages.items():
			lines='\n'.join((pagedict['title'],pagedict['text']))
			pageid=int(pagedict['id'])
			terms=self.getTerms(lines)
			self.numDocuments+=1

			termdictPage={}
			norm = 0
			for position, term in enumerate(terms):
				try:
					termdictPage[term][1].append(position)
					norm += len(termdictPage[term][1])**2
				except:
					termdictPage[term]=[pageid, [position]]
					norm += len(termdictPage[term][1])**2

			norm=math.sqrt(norm)

			for term,posting in termdictPage.items():
				self.tf[term].append('%.7f'% (float(len(posting[1]))/norm))
				self.df[term]+=1


			for termpage, postingpage in termdictPage.items():
				try:
					self.index[termpage].append(postingpage)
				except:
					self.index[termpage] = postingpage

		
		gc.enable()
		self.writeIndexfile(indexFile)


if __name__ == '__main__':
	c = Index()
	c.generateIndex()

