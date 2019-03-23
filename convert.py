import xml.etree.ElementTree as ET
import datetime
import sys
#import pdb 
import random

#user defined exception class to handle excetion during runtime
class IError(RuntimeError):
	def __init__(self, *args):
		self.args = args
	def __str__(self): 
		return(repr(self.value))

class temp(object):
	"""docstring for temp"""
	def __init__(self, record, root):
		super(temp, self).__init__()
		self.root = root
		self.records = record
		self.fields = dict()
		self._funct()
#method to extract text from the given element and its child and put them in fields = dict()
	def _setElem(self, elemName, recordName):
		#pdb.set_trace() 
		elem = self.root.find(elemName)
		if (elem is not None):
			self.fields[recordName] = elem.text
#creates a comma separated record
	def _toCSV(self):
		csvFields = map(self.__getRecord, self.records)
		return ';'.join(csvFields)
#get record from the fields = dict()
	def __getRecord(self, record):
		if (record in self.fields):
			return self.fields[record]
		return ''
#method to be used in inherited classes
	def _funct(self):
		pass
		
#Converter base class to parse the xml file and write the text into csv file.
class Converter(object):
#constructor method
	def __init__(self, xmlPath, outPutPath, InvoiceRecords, InvoiceRowRecords):
		self.tree = ET.parse(xmlPath)
		self.root = self.tree.getroot()
		self.rec = InvoiceRecords
		self.rowrec = InvoiceRowRecords
		self._parse()
		#self.row = []

#writes record in output file
	def _writeCSV(self, outPutPath):
		#pdb.set_trace()
		rows = [self.invoice] + [self.invoicerow]
		lines = map(lambda x: x._toCSV(), rows)
		output = '\n'.join(lines).encode('utf-8').strip()
		with open(outPutPath, 'wb') as f:
			f.write(output)

	def _parse(self):
		self.invoice = Invoice(self.rec, self.root)
			#pdb.set_trace()
			#self.invoicerows = map(lambda x: Invoicerows(self.rowrec, x), invoicerows)
		#invoicerowroot = list(self.root.iter("InvoiceRow")) 
		#for i in invoicerowroot:
		#	self.row = Invoicerows(self.rowrec, i)
		#self.invoicerow = list(self.row)
		for invoicerowroot in self.root.findall("InvoiceRow"):
			self.invoicerow = Invoicerows(self.rowrec, invoicerowroot)

class Invoice(temp):
		
#method to extract invoice details
	def _funct(self):
		for invoiceDetails in self.root.findall("InvoiceDetails"):
			invoiceTypeText = self.root.find("InvoiceDetails/InvoiceTypeCode").text
#if the typecode is not valid, trow error
			if (not invoiceTypeText in ('O', 'M', 'T', 'K', 'N')):
				raise ConError("The XML file does not conform to Finvoice 1.3")

			self.fields["InvoiceTypeCode"] = invoiceTypeText

			VatExcluded = invoiceDetails.find("InvoiceTotalVatExcludedAmount")
			currency = VatExcluded.get('AmountCurrencyIdentifier')
			self.fields["AmountCurrencyIdentifier"] = currency

		self._setElem("BuyerPartyDetails/BuyerPartyIdentifier", "BuyerPartyIdentifier")
		self._setElem("BuyerPartyDetails/BuyerOrganisationName", "BuyerOrganisationName")
		self._setElem("InvoiceDetails/PaymentTermsDetails/PaymentOverDueFineDetails/PaymentOverDueFinePercent", "PaymentOverDueFinePercent")
		self.__setBuyerPostalAddr()
		self.__setDeliveryPostalAddr()
		self.__setInvoiceDate()
		self._setElem("InvoiceDetails/InvoiceFreeText", "InvoiceFreeText")

#date format change 	
	def __setInvoiceDate(self):
		elem = self.root.find("InvoiceDetails/InvoiceDate")
		if (elem is None):
			return
		dateFormat = elem.get("Format")
		if (dateFormat is None):
			return
		# Python's date libraries can't handle the date format in the xml
		try:
			dateFormat = dateFormat.replace('C', '').replace("YY", "%Y").replace("MM", "%m").replace("DD", "%d")
			self.fields["InvoiceDate"] = datetime.datetime.strptime(elem.text, dateFormat).strftime('%d.%m.%Y')
		except ValueError as e:
			raise ConError("Date contained in InvoiceDate-element does not conform to the date format")
#buyer postal address details combined together
	def __setBuyerPostalAddr(self):
		name = self.root.find("BuyerPartyDetails/BuyerOrganisationName").text
		
		addressDetails = self.root.find("BuyerPartyDetails/BuyerPostalAddressDetails")
		
		if (addressDetails is None):
			return
		countryCodeElem = addressDetails.find("CountryCode")
		if (countryCodeElem is None):
			return
		
		street = addressDetails.find("BuyerStreetName").text
		town = addressDetails.find("BuyerTownName").text
		postCode = addressDetails.find("BuyerPostCodeIdentifier").text
		countryCode = countryCodeElem.text

		self.fields["BuyerPostalAddress"] = '\\'.join([name, street, postCode, town, countryCode])
#delivery postal address details combined together
	def __setDeliveryPostalAddr(self):
		name = self.root.find("DeliveryPartyDetails/DeliveryOrganisationName").text

		addressDetails = self.root.find("DeliveryPartyDetails/DeliveryPostalAddressDetails")
		
		if (addressDetails is None):
			return
		countryCodeElem = addressDetails.find("CountryCode")
		if (countryCodeElem is None):
			return

		street = addressDetails.find("DeliveryStreetName").text
		town = addressDetails.find("DeliveryTownName").text
		postCode = addressDetails.find("DeliveryPostCodeIdentifier").text
		countryCode = countryCodeElem.text

		self.fields["DeliveryPostalAddress"] = '\\'.join([name, street, postCode, town, countryCode])

class Invoicerows(temp):
#invoice row details gathered
	def _funct(self):
		#pdb.set_trace()
		#for rowdetail in self.root.findall("InvoiceRow"):
		self._setElem("ArticleName", "ArticleName")
		self._setElem("ArticleIdentifier", "ArticleIdentifier")
		self._setElem("OrderedQuantity", "OrderedQuantity")
		self._setElem("UnitPriceAmount", "UnitPriceAmount")
		self._setElem("RowVatRatePercent", "RowVatRatePercent")
		self.__setUnitCode()

	def __setUnitCode(self):
		quantity = self.root.find("OrderedQuantity")
		if (quantity is None):
			return
		unitCode = quantity.get("QuantityUnitCode")
		if (unitCode is None):
			return
		self.fields["QuantityUnitCode"] = unitCode

#reading from the record text file and returning only valid string values 
def readRecordList(fileName):
	with open(fileName, 'r') as f:
		records = list(f)
		cleanRecords = map(lambda x: x.rstrip(), records)
		return cleanRecords
#main method
def main():
	if len(sys.argv) < 2:
		print ("Program needs 1 Input and 1 Output file")
		return

	xmlPath = sys.argv[1]

	if len(sys.argv) > 2:
		outPutPath = sys.argv[2]
	else:
		outPutPath = 'exampleInvoice.csv'

	InvoiceRecords = readRecordList("record.txt")
	InvoiceRowRecords = readRecordList("rowrecords.txt")

	try:
		foo = Converter(xmlPath, outPutPath, InvoiceRecords, InvoiceRowRecords)
		foo._writeCSV(outPutPath)
	except IOError as e:
		print ('Error opening the xml file:', e.message)
	except ET.ParseError as e:
		print ('The file is not valid XML:', e.message)
	except IError as e:
		print ('Error:', e.args) 
	else:
		print ("CSV file: ' " + outPutPath + " ' ")

if __name__ == '__main__':
	main()