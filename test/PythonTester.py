# ===================================================================================================
#                           _  __     _ _
#                          | |/ /__ _| | |_ _  _ _ _ __ _
#                          | ' </ _` | |  _| || | '_/ _` |
#                          |_|\_\__,_|_|\__|\_,_|_| \__,_|
#
# This file is part of the Kaltura Collaborative Media Suite which allows users
# to do with audio, video, and animation what Wiki platfroms allow them to do with
# text.
#
# Copyright (C) 2006-2011  Kaltura Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http:#www.gnu.org/licenses/>.
#
# @ignore
# ===================================================================================================
import sys
import os

oldpath = sys.path

codeDir = os.path.dirname(os.getcwd())

sys.path.append(codeDir)

from KalturaClient import KalturaClient
from KalturaClientBase import IKalturaLogger
from KalturaClientBase import KalturaConfiguration
from KalturaClientBase import KalturaObjectFactory, KalturaEnumsFactory

from KalturaCoreClient import KalturaSessionType
from KalturaCoreClient import KalturaMediaEntry, KalturaMediaEntryFilter, KalturaMediaEntryOrderBy
from KalturaCoreClient import KalturaMediaType
from KalturaCoreClient import KalturaDataEntry
from KalturaCoreClient import KalturaException
from KalturaCoreClient import KalturaFilterPager

from KalturaCoreClient import API_VERSION
testString = "API Test ver %s" % (API_VERSION,)

sys.path = oldpath

import logging
import urllib
import time
import re

logging.basicConfig(level = logging.DEBUG,
                    format = '%(asctime)s %(levelname)s %(message)s',
                    stream = sys.stdout)
# UPDATE THIS
PARTNER_ID = 54321
SECRET = "YOUR_USER_SECRET"
ADMIN_SECRET = "YOUR_ADMIN_SECRET"
SERVICE_URL = "http://www.kaltura.com"
USER_NAME = "testUser"

class KalturaLogger(IKalturaLogger):
    def log(self, msg):
        logging.info(msg)

def GetConfig():
    config = KalturaConfiguration(PARTNER_ID)
    config.serviceUrl = SERVICE_URL
    config.setLogger(KalturaLogger())
    return config

# copied from C# tester
def SampleMetadataOperations():
    # The metadata field we'll add/update
    metaDataFieldName = "SubtitleFormat"
    fieldValue = "VobSub"

    # The Schema file for the field
    # Currently, you must build the xsd yourself. There is no utility provided.
    xsdFile = "MetadataSchema.xsd"

    client = KalturaClient(GetConfig())
    
    ###NOW, 3.1.6-flip the plugins are loaded only after Client instantiation,
    ###        but not into global scope
    ### Here, we bring them into global scope (preserving test code below)
    ###     by going too deep into the API, IMHO.
    ###
    ### TODO: make this easier, but don't pollute namespaces above here
    ### (eg, don't just append to sys.path)
    KalturaMetadataProfile = KalturaObjectFactory.objectFactories['KalturaMetadataProfile']
    KalturaMetadataObjectType = KalturaEnumsFactory.enumFactories['KalturaMetadataObjectType']    
    KalturaMetadataProfileFilter = KalturaObjectFactory.objectFactories['KalturaMetadataProfileFilter']
    KalturaMetadataFilter = KalturaObjectFactory.objectFactories['KalturaMetadataFilter']
    KalturaMixEntry = KalturaObjectFactory.objectFactories['KalturaMixEntry']
    
    # start new session (client session is enough when we do operations in a users scope)
    ks = client.generateSession(ADMIN_SECRET, USER_NAME, KalturaSessionType.ADMIN, PARTNER_ID, 86400, "")
    client.setKs(ks)

    # Setup a pager and search to use
    pager = KalturaFilterPager()
    search = KalturaMediaEntryFilter()
    search.setOrderBy(KalturaMediaEntryOrderBy.CREATED_AT_ASC)
    search.setMediaTypeEqual(KalturaMediaType.VIDEO)  # Video only
    pager.setPageSize(10)
    pager.setPageIndex(1)

    print "List videos, get the first one..."

    # Get 10 video entries, but we'll just use the first one returned
    entries = client.media.list(search, pager).objects

    # make sure we have a metadata profile
    profile = KalturaMetadataProfile() 
    profile.setName('TestProfile %s' % (testString,))
    MetadataObjectType = KalturaMetadataObjectType.ENTRY
    
    profile.setMetadataObjectType(MetadataObjectType)
    viewsData = ""

    newProfile = client.metadata.metadataProfile.add(profile, file(xsdFile, 'rb').read(), viewsData)

    # Check if there are any custom fields defined in the KMC (Settings -> Custom Data)
    # for the first item returned by the previous listaction
    filter = KalturaMetadataProfileFilter()
    metadata = client.metadata.metadataProfile.list(filter, pager).objects

    name = entries[0].getName()
    id = entries[0].getId()
    if metadata[0].getXsd() != None:
        print "1. There are custom fields for video: " + name + ", entryid: " + id
    else:
        print "1. There are no custom fields for video: " + name + ", entryid: " + id

    # Add a custom data entry in the KMC  (Settings -> Custom Data)
    profile = KalturaMetadataProfile()
    profile.setName('TestProfile %s' % (testString,))
    profile.setMetadataObjectType(KalturaMetadataObjectType.ENTRY)
    viewsData = ""

    metadataResult = client.metadata.metadataProfile.update(newProfile.id, profile, file(xsdFile, 'rb').read(), viewsData)

    assert(metadataResult.xsd != None)

    # Add the custom metadata value to the first video
    filter2 = KalturaMetadataFilter()
    filter2.setObjectIdEqual(entries[0].id)
    xmlData = "<metadata><SubtitleFormat>" + fieldValue + "</SubtitleFormat></metadata>"
    metadata2 = client.metadata.metadata.add(newProfile.id, profile.metadataObjectType, entries[0].id, xmlData)

    assert(metadata2.xml != None)
    
    print "3. Successfully added the custom data field for video: " + name + ", entryid: " + id
    xmlStr = metadata2.xml
    print "XML used: " + xmlStr

    # Now lets change the value (update) of the custom field
    # Get the metadata for the video
    filter3 = KalturaMetadataFilter()
    filter3.setObjectIdEqual(entries[0].id)
    filter3.setMetadataProfileIdEqual(newProfile.id)
    metadataList = client.metadata.metadata.list(filter3).objects
    assert(metadataList[0].xml != None)

    print "4. Current metadata for video: " + name + ", entryid: " + id
    xmlquoted = metadataList[0].xml
    print "XML: " + xmlquoted
    xml = metadataList[0].xml
    # Make sure we find the old value in the current metadata
    pos = xml.find("<" + metaDataFieldName + ">" + fieldValue + "</" + metaDataFieldName + ">")
    assert(pos >= 0)

    pattern = re.compile("<" + metaDataFieldName + ">([^<]+)</" + metaDataFieldName + ">")
    xml = pattern.sub("<" + metaDataFieldName + ">Ogg Writ</" + metaDataFieldName + ">", xml)
    rc = client.metadata.metadata.update(metadataList[0].id, xml)
    print "5. Updated metadata for video: " + name + ", entryid: " + id
    xmlquoted = rc.xml
    print "XML: " + xmlquoted

# copied from C# tester
def AdvancedMultiRequestExample():
    client = KalturaClient(GetConfig())
    KalturaMixEntry = KalturaObjectFactory.objectFactories['KalturaMixEntry']
    KalturaEditorType = KalturaEnumsFactory.enumFactories['KalturaEditorType']
    
    
    client.startMultiRequest()

    # Request 1
    ks = client.session.start(ADMIN_SECRET, USER_NAME, KalturaSessionType.ADMIN, PARTNER_ID, 86400, "")
    client.setKs(ks) # for the current multi request, the result of the first call will be used as the ks for next calls

    mixEntry = KalturaMixEntry()
    mixEntry.setName(".Net Mix %s" % (testString,))
    mixEntry.setEditorType(KalturaEditorType.SIMPLE)

    # Request 2
    mixEntry = client.mixing.add(mixEntry)

    # Request 3
    uploadTokenId = client.media.upload(file('DemoVideo.flv', 'rb'))

    mediaEntry = KalturaMediaEntry()
    mediaEntry.setName("Media Entry For Mix %s" % (testString,))
    mediaEntry.setMediaType(KalturaMediaType.VIDEO)

    # Request 4
    mediaEntry = client.media.addFromUploadedFile(mediaEntry, uploadTokenId)

    # Request 5
    client.mixing.appendMediaEntry(mixEntry.id, mediaEntry.id)

    response = client.doMultiRequest()

    for subResponse in response:
        if isinstance(subResponse, KalturaException):
            print "Error occurred: " + subResponse.message

    # when accessing the response object we will use an index and not the response number (response number - 1)
    assert(isinstance(response[1], KalturaMixEntry))
    mixEntry = response[1]
    
    print "The new mix entry id is: " + mixEntry.id

# create session
client = KalturaClient(GetConfig())

ks = client.generateSession(ADMIN_SECRET, USER_NAME, KalturaSessionType.ADMIN, PARTNER_ID, 86400, "")
client.setKs(ks)

# add media
uploadTokenId = client.media.upload(file('DemoVideo.flv', 'rb'))

mediaEntry = KalturaMediaEntry()
mediaEntry.setName("Media Entry Using Python Client ver %s" % (API_VERSION,))
mediaEntry.setMediaType(KalturaMediaType(KalturaMediaType.VIDEO))
mediaEntry = client.media.addFromUploadedFile(mediaEntry, uploadTokenId)

# serve
DATA_ENTRY_CONTENT = 'bla bla bla'
dataEntry = KalturaDataEntry()
dataEntry.setName('test data entry')
dataEntry.setDataContent(DATA_ENTRY_CONTENT)
addedDataEntry = client.data.add(dataEntry)
serveUrl = client.data.serve(addedDataEntry.id)
f = urllib.urlopen(serveUrl)
assert(DATA_ENTRY_CONTENT == f.read())

# multi request
client = KalturaClient(GetConfig())

client.startMultiRequest()

ks = client.session.start(ADMIN_SECRET, USER_NAME, KalturaSessionType.ADMIN, PARTNER_ID, 86400, "")
client.setKs(ks)

listResult = client.baseEntry.list()

multiResult = client.doMultiRequest()
print multiResult[1].totalCount
client.setKs(multiResult[0])

# error
try:
    mediaEntry = client.media.get('invalid entry id')
    assert(False)
except KalturaException, e:
    assert(e.code == 'ENTRY_ID_NOT_FOUND')

# multi request error
client = KalturaClient(GetConfig())

client.startMultiRequest()

ks = client.session.start(ADMIN_SECRET, USER_NAME, KalturaSessionType.ADMIN, PARTNER_ID, 86400, "")
client.setKs(ks)

mediaEntry = client.media.get('invalid entry id')

multiResult = client.doMultiRequest()
client.setKs(multiResult[0])
assert(isinstance(multiResult[1], KalturaException))
assert(multiResult[1].code == 'ENTRY_ID_NOT_FOUND')

SampleMetadataOperations()
AdvancedMultiRequestExample()

print 'Finished running client library tests'