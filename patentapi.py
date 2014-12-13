#!/usr/bin/env python
import re
import urllib.request, urllib.error
import htmlmin

from bs4 import BeautifulSoup,SoupStrainer, NavigableString, Tag
from collections import OrderedDict
from datetime import datetime
from httpfile import HttpFile
from zipfile import ZipFile

""" PatentHelper - basic definition for GooglePatent, USPTOPatent, EPOPatent
PatentPub -
GooglePatent -
USPTOPatent -
EPOPatent -  """

""" Base class for information about patents/publications """
class PatentPublication ( object ):

    ''' __init__ : Set up the '''

    def __init__( self ):

        # Bibliographic information
        self.abstract = None
        self.application_number = None
        self.assignee = None
        self.classifications = {'us_classifications': [],
                                'international_classifications': [],
                                'cooperative_classifications': [],
                                'ep_classifications': []}
        self.country_code = None
        self.family_members = []
        self.filing_date = None
        self.id = None
        self.kind_code = None
        self.inventors = []
        self.priority_date = None
        self.publication_date = None
        self.publication_number = None
        self.title = None

        # Full Text
        self.full_text = None
        self.claims = []

        # Citations
        self.backward_citations = []

        # Legal Events
        self.legal_events = []

class GooglePatentPublication( PatentPublication ):
    """ Returns a PatentPublication object
            If the <pub_num> parameter is passed, the class will attempt to fetch information scraped from the Google Patents
            website corresponding to the passed parameter.
                <pub_num> should be of the form CC[XXXXXX]X[KC]
                    - CC: country code
                    - X: 0-9
                    - KC: kind code
            If <pub_num> is omitted, a blank object will be created.
    """

    # Initialization
    def __init__( self, pub_num=None ):
        ######################################################################################################################################################
        #
        # STEP 1 - Set the initial state of each field in the object
        #
        ######################################################################################################################################################

        # Initialize the Base Class so the fields are available in the GooglePatentPublications class instance
        PatentPublication.__init__(self)

        # Constants
        self.PATENTPUBLICATION_BASE_URL = 'https://www.google.com/patents/'
        self.FILEHISTORY_BASE_URL = 'http://storage.googleapis.com/uspto-pair/applications/'

        # Fields in addition to the Base Class (PatentPublication)
        self.file_history = None
        self.terminal_disclaimer = None
        self.pta = None
        self.google_priority_date = None

        ######################################################################################################################################################
        #
        # STEP 2 - Validate the <pub_num> parameter.  If valid, set the publication_number property and  go to step 3.
        #          If not valid, throw a ValueError exception.
        #
        ######################################################################################################################################################
        # Call the validate_publication method
        pub_num = validate_publication(pub_num)
        if not pub_num:
            raise ValueError("Missing or invalid publication number, '" + str(pub_num) + "'.")

        #print('\n\nValidated Publication Number: ' + pub_num)

        # If we get here, the publication number is vlaid, so set the object's 'self.publication_number
        # disabled to set the ID to the full CC_[XXXX]_KC format
        #self.id = pub_num

        ######################################################################################################################################################
        #
        # STEP 3 - Call __get_html with the validated publication number to retrieve the Google Patent html page associated with the publication.
        #          When the call results in an error, raise the HTTPError for handling by the calling function.
        #
        ######################################################################################################################################################
        try: self.__html = self.__get_html(str(pub_num))
        except urllib.error.HTTPError as e:
            raise e
        #print(self.__html)

        ######################################################################################################################################################
        #
        # STEP 4 - Presumably, we have a Google Patent HTML Page for the requested Publication Number.  So, now we call a helper function
        #          to populate the GooglePatentPublication fields.
        #
        ######################################################################################################################################################
        if self.__html:

            # Populate the Bibliographic fields
            self.__populate_biblio()



        # Create a dictionary of the object's properties
        self.dict = {'abstract': self.abstract,
                     'application_number': self.application_number,
                     'assignee': self.assignee,
                     'backward_citations': self.backward_citations,
                     'claims': self.claims,
                     'classifications': self.classifications,
                     'country_code': self.country_code,
                     'family_members': self.family_members,
                     'filing_date': self.filing_date,
                     'file_history': self.file_history,
                     'full_text': self.full_text,
                     'google_priority_date': self.google_priority_date,
                     'id': self.id,
                     'inventors': self.inventors,
                     'kind_code': self.kind_code,
                     'legal_events': self.legal_events,
                     'priority_date': self.priority_date,
                     'publication_number': self.publication_number,
                     'publication_date': self.publication_date,
                     'title': self.title
                    }

    def __get_html ( self, pub_num ):
        url = self.PATENTPUBLICATION_BASE_URL + pub_num

        #print('\n\nget_html url parameter: ' + url)
        req = urllib.request.Request(url,headers={'User-Agent' : 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0; EIE10;ENUSMCM'}) # create the Google patents HttpRequest object

        resp = urllib.request.urlopen(req) # create an HttpResponse object, open the url request and place the response into the HttpResponse object
        #html = str(resp.read())
        html = resp.read().decode('utf-8')
        #print(htmlmin.minify(html).encode('utf-8'))
        return htmlmin.minify(html)

    def __populate_biblio( self ):
        #print(self.publication_number)

        # create a BS4 object to parse the Google HTML
        strainer = SoupStrainer('html')
        bSoup = BeautifulSoup(self.__html, 'lxml', parse_only=strainer)

        # In the Google HTML, there is a <table> element with class="patent-bibdata". This table has most of the bibliographic
        # data in table cells adjacent to cells with the data heading with class "patent-bibdata-heading".  We'll use BS4's
        # 'next_sibling' method to get the data after finding the data heading
        soupTable = bSoup.find("table", class_="patent-bibdata")
        biblio_list = soupTable.find_all("td", class_="patent-bibdata-heading")

        # Kind Code
        for item in biblio_list:
            # Patent Number (set the patent object's CC, NUM and KC)
            # Iterate through the <TD> items using BS4, and find the one with text "Publication number"
            # The sibling "<TD>" should hold the Publication Number data, so use "next_sibling" and
            # get the text using "getText() method

            if (((item.getText()).lower() == 'publication number') and not(self.kind_code)):
                full_num = item.next_sibling.getText()    # should be of form "CCXXXXXXXKC"
                #print(full_num)
                kind_code = full_num[-2:].strip()                # kind_code is last
                #print(kind_code)
                country = full_num[:2].strip()
                #print(country)
                publ_num = (full_num[2:-2]).strip()
                #print('num = ' + publ_num)

                self.id = country + publ_num + kind_code
                self.publication_number = publ_num
                self.kind_code = kind_code
                self.country_code = country

            # Application Number
            if ((item.getText()).lower() =='application number'):
                app_num = (item.next_sibling.getText()).strip()
                app_num = app_num[2:len(app_num)].strip()
                self.application_number = app_num

            # Google's calculated Priority Date
            try:
                if ((item.getText()).lower() == 'priority date'):
                    google_priority_date = (item.next_sibling.getText()).strip()
                    self.google_priority_date = datetime.strptime(google_priority_date,  '%b %d, %Y').strftime('%Y-%m-%d')
                    #print('Google Priority Date: ' + str(self.google_priority_date))
            except:
                pass

            # Publication Date
            try:
                if ((item.getText()).lower() =='publication date'):
                    pub_date = (item.next_sibling.getText()).strip()
                    self.publication_date = datetime.strptime(pub_date,  '%b %d, %Y').strftime('%Y-%m-%d')
                    #print('Publication Date: ' + str(self.publication_date))
            except:
                pass

            # Filing Date
            try:
                if ((item.getText()).lower() =='filing date'):
                    filing_date = (item.next_sibling.getText()).strip()
                    self.filing_date = datetime.strptime(filing_date,  '%b %d, %Y').strftime('%Y-%m-%d')
                    #print('Filing Date: ' + str(self.filing_date))
            except:
                pass

            # Family - Publications related to the requested publication
            if ((item.getText()).lower() =='also published as'):
                other_pubs = (item.next_sibling.getText()).strip()
                self.family_members = other_pubs.split(", ")
                #print('Family Members: ' + str(self.family_members))


            # Inventors
            if ((item.getText()).lower() =='inventors'):
                inventors = (item.next_sibling.getText()).strip()
                self.inventors = inventors.split(', ')
                #print('Inventors: ' + str(self.inventors))

            # Assignee
            if ((item.getText()).lower() =='original assignee'):
                original_assignee = (item.next_sibling.getText()).strip()
                self.assignee = original_assignee
                #print('Assignee: ' + self.assignee)

        #
        # Add biblio items not in the biblio table
        #
        # Title
        try:
            title_meta = bSoup.find('meta', attrs={'name':'DC.title'})    # this is a bs4 Tag element
            title_text = character_replace(title_meta['content'])
            self.title = title_text
            #print('Title: ' + self.title)
        except: pass

        # Abstract
        try:
            self.abstract = character_replace((bSoup.find('abstract').getText()).strip())
        except: pass
        #print('ABSTRACT: ' + self.abstract)

        # Backward Citations
        backward_citation_table = None
        try:
            backward_citation_table = bSoup.find('a', {'id': 'backward-citations'}).parent.findNext('table')
        except:pass
        if backward_citation_table:
            cite_numbers = backward_citation_table.findAll('td', class_="patent-data-table-td citation-patent")
            for item in cite_numbers:
                cite = process_citation(item.get_text())
                if (cite['publication_number'] != ''):
                    self.backward_citations.append(cite)
        #print('Backward Citations: ' + str(self.backward_citations))


        #-----------------------------------------------------------------------
        # Classifications
        #-----------------------------------------------------------------------

        #us_classes
        us_classifications = []
        us_classes = bSoup.findAll('td', text = re.compile('U.S. Classification'), attrs={'class', 'patent-data-table-td'})
        if us_classes:
            us_classifications = [x.strip() for x in (us_classes[0].next_sibling.get_text()).split(',')]

        #international_classes
        international_classifications = []
        int_classes = bSoup.findAll('td', text = re.compile('International Classification'), attrs={'class', 'patent-data-table-td'})
        if int_classes:
            international_classifications = [x.strip() for x in (int_classes[0].next_sibling.get_text()).split(',')]

        #coop_classes
        cooperative_classifications = []
        coop_classes = bSoup.findAll('td', text = re.compile('Cooperative Classification'), attrs={'class', 'patent-data-table-td'})
        if coop_classes:
            cooperative_classifications = [x.strip() for x in (coop_classes[0].next_sibling.get_text()).split(',')]

        #ep_classes
        ep_classifications = []
        ep_classes = bSoup.findAll('td', text = re.compile('European Classification'), attrs={'class', 'patent-data-table-td'})
        if ep_classes:
            ep_classifications = [x.strip() for x in (ep_classes[0].next_sibling.get_text()).split(',')]

        self.classifications = {'us_classifications': us_classifications,
                                'international_classifications': international_classifications,
                                'cooperative_classifications': cooperative_classifications,
                                'ep_classifications': ep_classifications}

        #---------------------------------------------------
        # Determine if the file history is available
        #---------------------------------------------------
        temp_appNum = str(self.application_number).replace(',','')
        temp_appNum = temp_appNum.replace('/', '')
        #print('\n\nTemp appNum: ' + temp_appNum)

        url = self.FILEHISTORY_BASE_URL + temp_appNum + '.zip'
        #print('\n\nPAIR URL: ' + url + '\n\n')
        z = None
        try: z = ZipFile(HttpFile(url))
        except: pass

        if z : self.file_history = url
        #print('\n\nfile history link: ' + str(self.file_history) + '\n\n')


        #---------------------------------------------------
        # Get the Claims
        #---------------------------------------------------
        claims = []     # Initialize the claims array to an emtpy array

        # Google Patents keeps the claims deep within a div having a class="patent-claims-section"
        # Within this div is a div that has a class="claims".  This is the only div in the page having class=claims
        # Using BS4, we can extract this div by searching on class_="claims".
        soupClaimsContainer = bSoup.find('div', class_="claims")

        # The soupClaimsContainer contains DIV elements that represent each claim.
        # Each claim has a class that is either "claim" (for independent claims) or "claim-dependent" (for dependent claims)
        soupClaimsList = soupClaimsContainer.find_all('div', recursive=False)


        # Each claim will comprise NavigableStrings and other Tag elements (mostly DIVs containing other DIVs or NavigableStrings)
        # The <div class="claim [claim-dependent]"> container will contain a single DIV with id=:CLM-XXXXX", num="XXXXX", class="claim"
        # This is the outer-most container of the individual claim information.
        # Iterating through the soupClaimsList list, we can extract information or further process each individual claim
        for iClaim in soupClaimsList:
            claim = {'depends-from':None}       # initialize an object to contain the claim information
                                                # for our GooglePatentPublication object
                                                # initially, we set the "depends-from" property to None to default to an
                                                # independent claim

            # claimContainer will be the DIV with id, num and class attributes
            # set recursive=False because we only want the top level DIVs
            claimContainer = iClaim.find('div', recursive=False)

            # Add the 'number' property to the claim object  Number identifies the claim by number
            claim['number'] = int(claimContainer['num'])

            # claimElementContainersList will be a list of DIV elements that contain the text of the claim
            # set recursive=False because we only want the top level DIVs
            claimElementContainersList = claimContainer.find_all('div', recursive=False)
            # BuildClaim will create the JSON structure for each claim
            BuildClaim(claimElementContainersList, claim)

            # Add the JSON claim to the claims list
            claims.append(claim)

        self.claims = claims

def BuildClaim(containerList, claim):
    ''' Analyze the claim information returned from Google Patents and transform it into a JSON representation.'''

    # Initialize an array to hold the claim elements
    claim_elements = []
    # containerList was passed in as a parameter and holds a list of DIV elements that contain element text and
    # other DIVs comprising sub-elements.
    # We loop through the list and determine if this is a dependent or independent claim
    for container in containerList:
        #look for a <claim-ref> tag.  If it exists, this is a dependent claim, so we will
        # set claim['depends-from'] = to the clim's parent number, which can be derived from the claim-ref tag's
        # idref attribute
        claimref = container.find('claim-ref')
        if claimref:
            # idref is in the form CLM-XXXXX.  We split that string and select only the numerical portion.
            # don't forget to cast the number to an INTEGER
            claim['depends-from'] = int(claimref['idref'].split('-')[1])

        # TODO: There are tags that will appear in some patent claims and not others (e.g., <CHEMISTRY>.
        # Need to add support for these as they arise.

        # Now pass the container to the BuildClaimElement function, which returns a JSON object representing the
        # claim element.  Then, append that claim element to the claim_elements list
        claim_elements.append(BuildClaimElement(container))


    # after all the container items have been processed, the claim_elements list should contain a JSON object representing
    # all of the elements in the claim.  We then add that object to the 'elements' property of the claim object.
    claim['elements'] = claim_elements
    return


def BuildClaimElement(container):
    ''' Build an element of the JSON claim structure. '''
    element = {}                                                    #initialize the element object
    element_text = ''                                               #initialize the element's text
    element_children = container.find_all('div', recursive=False)   #find all child elements, if any

    # interate through all the contents of the bSoup container to build the text of the claim element
    for child in container.children:
        # if the child element is a NavigableString, it's part of the text for the claim element
        # otherwise, it's probably a child element
        if (child.string and (not child.name == 'div')):
        #if (isinstance(child, NavigableString) and not(child.string.strip() == '')) or child.name == 'claim-ref' :
            element_text += child.string

    # Once the element text is built, add it to the 'text' property of the element object
    element['text'] = (strip_claim_number(element_text.strip())).strip()
    #element['text'] = (element_text.strip()).strip()

    element['children'] = []        # child elements will be stored in an array of element objects, so init the children property

    # Now loop through the child elements we found above and call this function recursively to build the child elements
    for elem in element_children:
        new_elements = []
        element['children'].append(BuildClaimElement(elem))

    #elements.append(element)
    return element


def strip_claim_number(text):
    import re
    pattern = '^\d{0,3}\.\s{1,5}'

    return re.sub(pattern, '', text)



def validate_publication( publication_number ):
    import re

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

# This function will take a string and replace entities that were badly decoded from unicode by BS4
# This is a stop-gap until I figure out a more elegant solution
# Add entities as they are discovered.
def character_replace( strng ):
    strng = strng.replace("\\xe2\\x80\\x98", "'")
    strng = strng.replace("\\xe2\\x80\\x99", "'")
    strng = strng.replace("\\n","")

    return strng

def process_citation( strng ):
    cite = {}
    if "*" not in strng:
        cite = {'publication_number': strng.strip(),
                'cited_by_examiner': False}
    else:
        strng = strng.replace('*','')
        cite = {'publication_number': strng.strip(),
                'cited_by_examiner': True}
    return cite


if __name__ == "__main__":

    #pat = GooglePatentPublication("US8123456")
    #pat = GooglePatentPublication("US8623013")
    pat = GooglePatentPublication("US8501436")
    #pat = GooglePatentPublication("w;lejtw")
