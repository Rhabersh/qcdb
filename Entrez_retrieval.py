#!/usr/bin/env python
#
#Author: Ryan Habershaw
#
#Date: 11 June, 2019
#
#Purpose: This code will search through the SRA database
#         and pull down the relevant metadata.
#
######################################################


from Bio import Entrez

import xmltodict, json, pprint

#from astropy.table import Table, Column
#import numpy as np

Entrez.email = "ryan_habershaw@brown.edu"
#Lets Entrez know who is using it

sra_handle = Entrez.esearch(db = "sra", term = "SRS643408", retmax = "10000")
#Searches the specified database for primary UIDs to be used by 'efetch'

#sra_post = Entrez.epost(db = "sra", id = "SRS643408")

sra_results = Entrez.read(sra_handle)
#Reads in the results of 'esearch' above

sra_id = sra_results["IdList"][0]
#Stores the required ID in a variable to be used by 'efetch'

sra_fetch = Entrez.efetch(db = "sra", id = sra_id, rettype="text", retmode="xml")
#Retrieves the records (specified by the id)

sra_table = sra_fetch.read()

parse_table = xmltodict.parse(sra_table)
#json_table = json.dumps(parse_table)
#json_decode = json.loads(json_table)

pp = pprint.PrettyPrinter(indent = 0, width = 25)
pp.pprint(parse_table)

#print(json.dumps(xmltodict.parse(sra_table)))



sra_handle.close()
sra_fetch.close()
