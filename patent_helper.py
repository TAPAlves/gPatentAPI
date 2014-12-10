#!/usr/bin/env python
""" PatentHelper - basic definition for GooglePatent, USPTOPatent, EPOPatent
PatentPub -
GooglePatent -
USPTOPatent -
EPOPatent -  """

import sys, urllib, urllib.request, urllib.error
from bs4 import BeautifulSoup
from collections import OrderedDict
from datetime import datetime
from httpfile import HttpFile
from zipfile import ZipFile
import re
from pprint import pprint

GOOGLE_BASE_URL = 'https://www.google.com/patents/'
USPTO_PATENT_BASE_URL = 'http://patft.uspto.gov/netacgi/nph-Parser?Sect2=PTO1&Sect2=HITOFF&p=1&u=/netahtml/PTO/search-bool.html&r=1&f=G&l=50&d=PALL&RefSrch=yes&Query='
USPTO_PUBLICATION_BASE_URL = 'http://appft1.uspto.gov/netacgi/nph-Parser?Sect1=PTO1&Sect2=HITOFF&d=PG01&p=1&u=/netahtml/PTO/srchnum.html&r=1&f=G&l=50&s1='
PAIR_SRC_URL_BASE = 'http://storage.googleapis.com/uspto-pair/applications/'

class Publication ( object ):
	""" Base class for information about patents/publications """
	def __init__( self, pub_num=None):
		self.application_number = None
		self.assignee = None
		self.country_code = None
		self.family = None
		self.filing_date = None
		self.kind_code = None
		self.inventors = None
		self.priority_date = None
		self.publication_date = None
		self.publication_number = pub_num
		self.title = None

	#def priority_date( self ):
	#	pass

class GooglePatent( Publication ):
	""" Returns a Publication object
			If the <pub_num> parameter is passed, the class will attempt to fetch information scraped from the Google Patents
			website corresponding to the passed parameter.
				<pub_num> should be of the form CC[XXXXXX]X[KC]
					- CC: country code
					- X: 0-9
					- KC: kind code
			If <pub_num> is omitted, a blank object will be created.
	"""
	def __init__(self, pub_num=None, base_url=GOOGLE_BASE_URL):

		######################################################################################################################################################
		#
		# STEP 1 - Set the initial state of each field in the object
		#
		######################################################################################################################################################

		#-----------------------------
		#| Public Fields
		#-----------------------------
		self.application_number = None			# The publication's application number
		self.assignee = None					  # The owner of the IP
		self.country_code = None				  # Country Code for the publication (e.g., US, EP, JP, CN, CA)

		self.family = None						# List of related publications (CONs, DIVs, etc)
		self.filing_date = None				   # The date the application was filed
		self.inventors = None					 # List of inventors' names
		self.kind_code = None					 # The kind code (e.g., A1, B1, A3, etc) - meaning is relevant to publishing patent office
		self.priority_date = None				 # Google's best guess as to the 'effective filing date' of the publicaiton - used for prior art determinations
		self.publication_number = pub_num		 # Publication Number - along with the country code and knid code, uniquely identifies the publication
		self.publication_date = None			  # The date the reference was published

		self.title = None						 # Title of the publication

		self.file_history = None				  # Link to the USPTO PAIR data - Default is 'None'

		self.dict = {}							# Python dict of the object's properties

		#-----------------------------
		#| Private Fields
		#-----------------------------
		self.__html = None						# This is the Google Patent page HTML.  It's stored in a 'private' field


		######################################################################################################################################################
		#
		# STEP 2 - Either return the empy object or use the <pub_num> parameter to try to fetch Publication data from Google Patents
		#
		######################################################################################################################################################

		# if <pub_num> is not passed into the function, then exit the init routine and return the default/blank settings
		# created above
		#if not pub_num:
		#	return

		# If we reach this code, then <pub_num> was passed.
		#
		# The first step here is to validate <pub_num>.
		# Call the validate_publication method, which will examine the pub_num entered by the
		# user, process it to try to put it in a form we can use, and return a validated pub_num or a Nonetype if invalid
		pub_num = validate_publication(pub_num)
		if not(pub_num):
			return								#Exit init and return an empty opject

		#print("I'm the modified pub_num! -->" + pub_num)

		# __get_html loads the Google Patents web page corresponding to <pub_num>
		# base_url is the url to the Google Patents webpage API
		self.__html = self.__get_html( base_url + str(pub_num))

		# if the __html field is populated, populate the remaining fields scraped from the HTML
		if self.__html:
			self.__biblio = self.__create_biblio_fields(self.__html)
			#print('\n\nBiblio: ' + str(self.__biblio))

			if self.__biblio:
				self.publication_number = self.__biblio['publication_number']
				self.kind_code = self.__biblio['kind_code']
				self.country_code = self.__biblio['country_code']
				self.title = self.__biblio['title']
				self.publication_date = self.__biblio['publication_date']
				self.priority_date = self.__biblio['priority_date']
				self.application_number = self.__biblio['application_number']
				self.filing_date = self.__biblio['filing_date']
				self.inventors = self.__biblio['inventors']
				self.family = self.__biblio['family']
				self.assignee = self.__biblio['assignee']
				self.classifications = {'US': self.__biblio['us_classifications'],
										'IN': self.__biblio['international_classifications'],
										'CC': self.__biblio['cooperative_classifications'],
										'EP': self.__biblio['european_classifications']}
				self.backward_citations = self.__biblio['backward_citations']


			# Determine if the file history is available
			temp_appNum = str(self.application_number).replace(',','')
			temp_appNum = temp_appNum.replace('/', '')
			#print('\n\nTemp appNum: ' + temp_appNum)

			url = PAIR_SRC_URL_BASE + temp_appNum + '.zip'
			#print('\n\nPAIR URL: ' + url + '\n\n')

			z = None
			try: z = ZipFile(HttpFile(url))
			except: pass
			if z : self.file_history = url
			print('\n\nfile history link: ' + str(self.file_history) + '\n\n')


			self.dict = {'application_number': self.application_number,
						 'assignee': self.assignee,
						 'country_code': self.country_code,
						 'family': self.family,
						 'filed': self.filing_date,
						 'file_history': self.file_history,
						 'inventors': self.inventors,
						 'kind_code': self.kind_code,
						 'priority': self.priority_date,
						 'publication_number': self.publication_number,
						 'published': self.publication_date,
						 'title': self.title
						}
			#print('\n\n\ndict --> ' + str(self.dict) + '\n\n\n')


	def html( self ):
		return self.__html

	def __str__(self):
		if self.publication_number and self.country_code and self.kind_code:
			return ('{0} {1} {2}').format(str(self.country_code), str(self.publication_number), str(self.kind_code))
		else:
			return str(type(self))

	def __create_biblio_fields( self, html ):
		biblio = {}	# initialize the dictionary that will hold the biblio information

		bSoup = BeautifulSoup(self.__html, 'lxml')	# create a BS4 object to parse the Google HTML

		if bSoup:  #make sure the BS4 object was created
			soupTable = bSoup.find("table", class_="patent-bibdata")
			biblio_list = soupTable.find_all("td", class_="patent-bibdata-heading")
			#print(biblio_list)


			biblio['application_number'] = None
			biblio['priority_date'] = None
			biblio['publication_date'] = None
			biblio['filing_date'] = None
			biblio['family'] = None
			biblio['inventors'] = None
			biblio['assignee'] = None

			for item in biblio_list:
				#print((item.getText()).lower())
				# Patent Number (set the patent object's CC, NUM and KC)
				# Iterate through the <TD> items using BS4, and find the one with text "Publication number"
				# The sibling "<TD>" should hold the Publication Number data, so use "next_sibling" and
				# get the text using "getText() method
				if (((item.getText()).lower() == 'publication number') and ('publication_number' not in biblio.keys())):
					full_num = item.next_sibling.getText()	# should be of form "CCXXXXXXXKC"
					#print(full_num)
					kind_code = full_num[-2:].strip()				# kind_code is last
					#print(kind_code)
					country = full_num[:2].strip()
					#print(country)
					num = (full_num[2:-2]).strip()
					#print('num = ' + num)
					biblio['publication_number'] = num
					biblio['kind_code'] = kind_code
					biblio['country_code'] = country

				# Application Number
				if ((item.getText()).lower() =='application number'):
					app_num = (item.next_sibling.getText()).strip()
					app_num = app_num[2:len(app_num)].strip()
					biblio['application_number'] = app_num

				# Priority Date
				try:
					if ((item.getText()).lower() == 'priority date'):
						pri_date = (item.next_sibling.getText()).strip()
						biblio['priority_date'] = datetime.strptime(pri_date, '%b %d, %Y').strftime('%Y-%m-%d')
						print('Priority Date: ' + str(biblio['priority_date']))
				except:
					pass

				# Publication Date
				try:
					if ((item.getText()).lower() == 'publication date'):
						pub_date = (item.next_sibling.getText()).strip()
						biblio['publication_date'] = datetime.strptime(pub_date, '%b %d, %Y').strftime('%Y-%m-%d')
				except:
					pass

				# Filing Date
				try:
					if ((item.getText()).lower() == 'filing date'):
						filing_date = (item.next_sibling.getText()).strip()
						biblio['filing_date'] = datetime.strptime(filing_date, '%b %d, %Y').strftime('%Y-%m-%d')
				except:
					pass


				# Family - Publications related to the requested publication
				if ((item.getText()).lower() =='also published as'):
					other_pubs = (item.next_sibling.getText()).strip()
					biblio['family'] = other_pubs.split(", ")

				# Inventors
				if ((item.getText()).lower() =='inventors'):
					inventors = (item.next_sibling.getText()).strip()
					biblio['inventors'] = inventors.split(', ')
					#print('\n\ninventors --> ' + str(biblio['inventors']))

				# Assignee
				if ((item.getText()).lower() =='original assignee'):
					original_assignee = (item.next_sibling.getText()).strip()
					biblio['assignee'] = original_assignee

			# Classifications
			#us_classes
			biblio['us_classifications'] = []
			us_classes = bSoup.findAll('td', text = re.compile('U.S. Classification'), attrs={'class', 'patent-data-table-td'})
			if us_classes:
				biblio['us_classifications'] = [x.strip() for x in (us_classes[0].next_sibling.get_text()).split(',')]

			#international_classes
			biblio['international_classifications'] = []
			int_classes = bSoup.findAll('td', text = re.compile('International Classification'), attrs={'class', 'patent-data-table-td'})
			if int_classes:
				biblio['international_classifications'] = [x.strip() for x in (int_classes[0].next_sibling.get_text()).split(',')]

			#coop_classes
			biblio['cooperative_classifications'] = []
			coop_classes = bSoup.findAll('td', text = re.compile('Cooperative Classification'), attrs={'class', 'patent-data-table-td'})
			if coop_classes:
				biblio['cooperative_classifications'] = [x.strip() for x in (coop_classes[0].next_sibling.get_text()).split(',')]

			#ep_classes
			biblio['european_classifications'] = []
			ep_classes = bSoup.findAll('td', text = re.compile('European Classification'), attrs={'class', 'patent-data-table-td'})
			if ep_classes:
				biblio['european_classifications'] = [x.strip() for x in (ep_classes[0].next_sibling.get_text()).split(',')]


			# Title
			biblio['title'] = None
			try:
				title_meta = bSoup.find('meta', attrs={'name':'DC.title'})	# this is a bs4 Tag element
				title_text = character_replace(title_meta['content'])
				biblio['title'] = title_text

			except:
				pass

			# Abstract
			biblio['abstract'] = None
			try: biblio['abstract'] = character_replace((bSoup.find('abstract').getText()).strip())
			except: pass

			# Citations
			biblio['backward_citations'] = []
			backward_citation_table = None
			try:
				backward_citation_table = bSoup.find('a', {'id': 'backward-citations'}).parent.findNext('table')
			except:
				pass
			if backward_citation_table:
				cite_numbers = backward_citation_table.findAll('td', class_="patent-data-table-td citation-patent")
				for item in cite_numbers:
					cite = (item.get_text())
					biblio['backward_citations'].append(cite)

			return biblio

	def __get_publication_status( self, application_number ):
		# Now we need the "Status" of the publication.  This is obtained from the USPTO Public PAIR data, which
		# is retrievable from a Zip file on Google.
		#
		try:
			temp_appNum = str(application_number).replace(',','')

			reg = re.compile(r'(^US (?P<series>\d{2})/(?P<num>\d{6}$))')
			match = reg.search(temp_appNum)

			url = PAIR_SRC_URL_BASE + match.group('series') + match.group('num') + '.zip'
			z = ZipFile(HttpFile(url))		#create a ZipFile object from the http resource using HttpFile

			for filename in z.namelist():

				if 'application_data' in filename:				# look for the 'application-data' file, which includes the publication status information
					with z.open(filename, 'r') as file_text:	# open the file with "file_text" as the file handler
						for line in file_text:
							line_text = str(line, encoding='ascii')

							if re.match(r'^Status', line_text):
								status = (line_text.split('\t')[1]).strip() # The Status will be the 2nd item in the array when splitting the line at the tab
								return status
								break
							else:
								continue

						break
		except Exception as e:
			return None

	def __get_html( self, url ):
		#print(url)
		req = urllib.request.Request(url,headers={'User-Agent' : 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0; EIE10;ENUSMCM'}) # create the Google patents HttpRequest object

		resp = urllib.request.urlopen(req) # create an HttpResponse object, open the url request and place the response into the HttpResonse object
		return str(resp.read())

# This function will take a string and replace entities that were badly decoded from unicode by BS4
# This is a stop-gap until I figure out a more elegant solution
# Add entities as they are discovered.
def character_replace(strng):
	strng = strng.replace("\\xe2\\x80\\x98", "'")
	strng = strng.replace("\\xe2\\x80\\x99", "'")
	strng = strng.replace("\\n","")

	return strng

def validate_publication(publication_number):

	# Strip leading/trailing whitespace and remove specific characters that may be passed in.
	# The goal is to have only form CC[XXXXXXXXXX]XKC
	publication_number = re.sub('[^0-9a-zA-Z]+', '', publication_number)
	#print('re.sub: "' + publication_number + '"')

	pattern = r"(?P<cc>[A-Za-z]{2})(?P<pub>[0-9]{1,12})(?P<kc>[A-Za-z]?[1-9]?)" # Regular Expression to match Google Patent's
	m = re.match(pattern, publication_number)

	if m:
		#print('Match! --> ' + m.group(0) + '\n\n')
		return publication_number

	return False


if __name__ == "__main__":

	#pat = GooglePatent("US8061014")
	#pat = GooglePatent("US8617194")
	#pat = GooglePatent(" US2010_0147230-A1!@#$%^&*()+_=[{|\}]:; ")
	pat = GooglePatent("US8123456")
	#print (pat)
	#print ('publication_number: ' + pat.publication_number)
	#print ('application_number: ' + pat.application_number)
	#print ('title: ' + pat.title)
	#print ('inventors: ' + str(pat.inventors))
	#print ('classifications: ' + str(pat.classifications))
	#print ('backwards_citations: ' + str(pat.backward_citations))
	#print ('priority_date: ' + str(pat.priority_date))
	#print ('family: ' + str(pat.family))
	print ('dict:' + str(pat.dict) + '\n\n')

	#validate_publication("US8123654C")
	#validate_publication("US20090060697");
