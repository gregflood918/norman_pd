# -*- coding: utf-8 -*-

"""
Greg Flood
CS 5970 Text Analytics


normanpd.py will contain all of the following functions outlined in 
the assignment:
    
    fetchincidents
    extractincidents
    createdb
    populatedb
    status

"""

#Imported packages
import urllib.request
import re
from bs4 import BeautifulSoup
import sqlite3
import os
from PyPDF2 import PdfFileReader
import random

'''
Function that downloads daily incident report pdfs from the Norman
Police department website.  This function creates a local directory in 
the current working directory to store the pdfs.
'''
def fetchincidents():
    
    f = urllib.request.urlopen('http://normanpd.normanok.gov/content/daily-activity').read().decode('utf-8')
    
    #Create BeautifulSoup object - allows us to parse html files
    soup = BeautifulSoup(f,'html.parser')

    #Create regexp object to match download links in html
    regexp = re.compile(r"^.*Daily Incident Summary.*$")
    
    #PDF links array
    pdfLinks = []

    #Use findAll function in BeautifulSoup to find all <a> tags that signify urls
    for tag in soup.findAll('a',href=True):
        hrefs = str(tag)
        test = regexp.search(hrefs)
        if test:
            pdfLinks.append(tag)
            
    #Make new directory to store PDFs
    pdfpath = "dailyIncidentPDFs"
    #Check if path exists
    if not os.path.exists(pdfpath):
        os.makedirs(pdfpath)     
        
    #Go through list of links, download pdf, and save in new folder we created
    for link in pdfLinks:
        url = urllib.request.urlopen('http://normanpd.normanok.gov/' + link['href'])
        
        #Extract useable filename
        match = re.compile(r'\d{4}-\d{2}-\d{2}')
        name = match.search(str(link))
        current = urllib.request.urlopen('http://normanpd.normanok.gov/' + link['href'])
        file = open(pdfpath + "/" + name.group() + ".pdf", "wb")
        file.write(current.read())
        file.close()    

    return
    
 
'''
Function that parses the PDF files downloaded from a call to 
fetchincidents() and returns a list of list.  Each inner list
has five elements corresponding to Date/Time, Incident, Number, Location,
Nature, and Incident ORI
'''
def extractincidents():
    
    #Extract files from dailyIncidentPDFs directory
    #This is created in the fetch incidents function
    fileNames = []
    for path, dirs, files, in os.walk(os.getcwd()+"/dailyIncidentPDFs"):
        
        #Test if directory contains files
        if not files:
            print("NO PDFs to Extract, run fetchIncidents()")
            return fileNames
        
        fileNames = files
    
    #Now, using the file names, we can cycle through list and create
    #PdfFileReader objects for each PDF.
    text = []

    #Regular expression for parsing
    regExp = r'(\d{1,2}/\d{1,2}/\d{4}\s\d{1,2}:\d{1,2})\s(\d{4}-\d{8})\s(.+?(?=\s[A-Z][a-z]{1,9}))\s(.+?(?=OK\d+|\d+))'
    for file in fileNames:
        
        myPDF = PdfFileReader(os.getcwd()+"/dailyIncidentPDFs/"+file)  
        
        #Iterate through PDF files
        for i in range(myPDF.getNumPages()):
            
            tempText = myPDF.getPage(i).extractText()
            tempText = tempText.replace("Daily Incident Summary (Public)","")
            tempText = " ".join(tempText.replace("\n", " ").strip().split())
    
            tempArr = re.compile(regExp).split(tempText)
            tempArr = tempArr[1:] #Leave out header
            
            text.extend(tempArr)

    #Use list comprehension make each incident a list with 5 elements
    incidents = [text[x:x+5] for x in range(0, len(text), 5)]
    return incidents
   

'''
Function that creates a SQLite database that will be used to store
the Norman daily incident report data. This db will be titled
"normanpd.db" and will be stored in the current working directory
'''
def createdb():
    conn = sqlite3.connect(r"normanpd.db")
    c = conn.cursor()
    
    #Create db - let ID be primary key. Thus, this function can't be run twice
    c.execute('''CREATE TABLE incidents
    (id INTEGER PRIMARY KEY,number TEXT,date_time TEXT,location TEXT,nature TEXT,ORI TEXT)''')   
    conn.commit()
    conn.close()
    return
    
    
'''
Function that will populate the database created with createdb(). 
This should be an list of list, where each inner list contains 
incidents to be inserted into the database
'''
def populatedb(incident):
    
    conn = sqlite3.connect(r"normanpd.db")
    c = conn.cursor()
    #Loop through array length
    for i in range(len(incident)):
        c.execute("INSERT INTO incidents VALUES (?,?,?,?,?,?)",
                  (i+1,incident[i][1],incident[i][0],incident[i][2],incident[i][3],incident[i][4]))
       
    conn.commit()
    conn.close()
    return
    
    
'''
Function that will print number of rows in database 'normanpd.db'
And will select 5 random rows to print to standard out
'''
def status():
    
    conn = sqlite3.connect(r"normanpd.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM incidents")
    dbLength=c.fetchone()[0]
    #Print db length

    print("Total Number of Rows: ",dbLength)
    
    #Repeatable results
    random.seed(100)
    #Grab 5 random rows
    for i in range(5):
        randInt = random.randint(1,(dbLength-1))
        c.execute("SELECT * FROM incidents WHERE id=(?)",(randInt,))
        print(c.fetchone())
    conn.close()
    
    return

    