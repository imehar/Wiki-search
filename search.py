

import re
import json
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
import copy
from functools import reduce
from collections import defaultdict
from flask import Flask
from flask import Flask, render_template, request


app = Flask(__name__)
app.debug = True
app.jinja_env.add_extension('jinja2.ext.loopcontrols')
porter=PorterStemmer()


class QueryIndex:
	"""docstring for QueryIndex"""
	def __init__(self):
		self.index = {}
		self.readFile = 'index.json'
		self.collectionFile = 'testCollection.json'
		self.sw = set(stopwords.words('english'))
		self.documents = {}

	def intersectList(self,lists):
		if len(lists)==0:
			return []
		lists.sort(key=len)
		return list(reduce(lambda x,y: set(x)&set(y),lists))

	def getTerms(self,line):
		""" @Input str of words
			@Output list of stemmed words (excluding stopwords)
		"""
		line = line.lower()
		line = re.sub(r'[^\w\d ]',' ',line)
		line = line.split()
		line = [porter.stem(x) for x in line if x not in self.sw]
		return line

	def getTermInfo(self,terms):
		"""
			@returns list of docid, positions of terms from index file
		"""
		return [self.index[term] for term in terms]

	def getDocID(self,termInfo):
		return [ [x[0] for x in p] for p in termInfo ]


	def readIndex(self,file):
		if len(self.index)==0:
			self.index = json.load(open(file,'r'))


	def readDoc(self,file):
		if len(self.documents)==0:
			self.documents = json.load(open(file,'r'))

	def queryType(self,q):
		"""
			@returns type of query
		"""
		if '"' in q:
			return "PQ"
		elif len(q.split())>1:
			return "FTQ"
		else:
			return "OWQ"

	def owq(self,q):
		"""
			@returns list of docid for given query
		"""
		prevQuery = q
		q = self.getTerms(q)
		print("terms ", q)
		if len(q)==0:
			print("no terms")
			return []
		elif len(q)>1:
			return self.ftq(prevQuery)
		q = q[0]
		if q not in self.index:
			print("No term found in index file")
			return []
		docid = self.index[q]
		docid = [ x[0] for x in docid]
		return docid

	def ftq(self,q):
		"""
			@returns list of docid for given query
		"""
		q = self.getTerms(q)
		if len(q)==0:
			print("no term")
			return []
		docid = set()
		for term in q:
			try:
				p = self.index[term]
				p = [ x[0] for x in p]
				docid = docid|set(p)
			except Exception as e:
				pass
				# raise e
		return list(docid)


	def pq(self,q):
		"""
			@returns list of docid for given query
		"""
		prevQuery = q
		q = self.getTerms(q)
		if len(q)==0:
			print("no term")
			return []
		elif len(q)==1:
			return self.owq(prevQuery)

		docid = self.pqDoc(q)
		return docid

	def pqDoc(self,q):
		"""
			@returns list of docid for given query
		"""
		pharseDoc = []
		length = len(q)
		for term in q:
			if not term in self.index:
				print("no doc")
				return []

		postings = self.getTermInfo(q)
		docs = self.getDocID(postings)
		docs = self.intersectList(docs)

		for i in range(len(postings)):
			postings[i] = [x for x in postings[i] if x[0] in docs]

		for i in range(len(postings)):
			for j in range(len(postings[i])):
				postings[i][j][1]=[x-i for x in postings[i][j][1]]
		result = []

		for i in range(len(postings[0])):
			li = self.intersectList( [ x[i][1] for x in postings ])
			if len(li)>0:
				result.append(postings[0][i][0])

		return result


	def startquery(self,q):
		readFile = self.readFile
		self.readIndex(readFile)
		print("Done reading file ...")
		qt = self.queryType(q)
		docid = []
		if qt=="OWQ":
			docid = self.owq(q)
		elif qt=="FTQ":
			docid = self.ftq(q)
		elif qt=="PQ":
			docid = self.pq(q)
		return docid


def clean_text(text):
	clean = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
	text = re.sub(clean,'',text)
	return text


q = QueryIndex()
@app.route("/")
def index():
	q.readIndex(q.readFile)
	print("Done reading file ...")
	return render_template('index.html')


@app.route("/search" ,methods=['GET','POST'])
def searchit():
	query = request.form.get('search','')
	# print('query ',query)
	# if query=='':
	# 	return render_template('index.html')
	result = q.startquery(query)
	result = list(map(str,result))
	q.readDoc(q.collectionFile)
	texts = { docid:clean_text(doc_dict['text']) for docid,doc_dict in q.documents.items()}
	return render_template('results.html',results=result,documents = q.documents,texts=texts)


@app.route("/showpage/<docid>")
def showpages(docid):
	return render_template('page.html',message=q.documents[str(docid)]['text'])


if __name__ == '__main__':
	app.run()