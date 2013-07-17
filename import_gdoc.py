import gdata.docs.client
import sys
import getpass
import re

email = sys.argv[1]
password = getpass.getpass()
source = 'erasme-rouedesinventions'
url = key = sys.argv[2]

m = re.search('key=(\w+)', url)
if m and m.groups():
    key = m.groups()[0]

docid = 'spreadsheet:{}'.format(key)

print '+ authenticate to google server'
gd_client = gdata.docs.client.DocsClient()
gd_client.ssl = True
token = gd_client.ClientLogin(email, password, source)

print '+ get resource {}'.format(docid)
doc = gd_client.GetResourceById(docid)

print '+ get page 1 (principles)'
csv_principles = gd_client.download_resource_to_memory(doc, extra_params={'gid': 0, 'exportFormat': 'csv'})

print '+ get page 2 (inventions)'
csv_inventions = gd_client.download_resource_to_memory(doc, extra_params={'gid': 1, 'exportFormat': 'csv'})

print csv_principles
print csv_inventions
