'''

Script to extract the data which mythic/legendary items were bought and save the data to file
for analysis/graphics

'''


###
# Imports
import logging

from tqdm import tqdm
import urllib3


###
# Load ressources
try:
    import src.ressources.mongodb as mongodb
    import src.ressources.data_processing as dataProcessing
    import src.ressources.api_requests as apiRequests
except Exception:
    import ressources.mongodb as mongodb
    import ressources.data_processing as dataProcessing
    import ressources.api_requests as apiRequests


###
# Logging
logging.basicConfig(level = 'INFO') # Set to DEBUG for more informations
logger = logging.getLogger(__name__)


###
# Set run-specific constants
REGION = 'euw1'


###
# Main loop
if __name__ == '__main__':
    ###
    # Create the MongoDB-client
    mongoDbClient, mongoDbDatabase = mongodb.setupClientAndDatabase()


    ###
    # Suppress SSL warnings (has to be disabled due to proxy)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


    ###
    # Generate the generator for the timeline data
    dataGenerator = mongodb.getTimelineDataGenerator(mongoDbDatabase = mongoDbDatabase,
        region = REGION)


    ###
    # Load proxy information
    _, proxies = apiRequests.setApiKeyAndProxy()


    ###
    # Get item informations
    itemRawData, legendaryItemsIds, mythicItemsIds, tearItemMappings = apiRequests.getItemInformation(
        proxies = proxies)


    ###
    # Get and save champion information and icons
    apiRequests.getChampionInfoAndIcons(proxies = proxies)


    ###
    # Get and save item icons
    apiRequests.getItemIcons(legendaryItemsIds = legendaryItemsIds, mythicItemsIds = mythicItemsIds,
        proxies = proxies)


    ###
    # Iterate over the data
    firstMythicItemCollected = list()
    legendaryAndMythicItemsCollected = list()

    for ct, matchData in tqdm(enumerate(dataGenerator)):
        ###
        # Get the queue id as well as the champion ids
        queueAndChampionIds = dataProcessing.extractQueueAndChampions(matchData)


        ###
        # Get the first 5 legendary/mythic items bought per champion as well as the mythic items per champion
        firstMythicItem, legendaryAndMythicItemsBought = dataProcessing.extractBoughtMythicAndLegendaryItems(
            matchData = matchData, legendaryItemsIds = legendaryItemsIds, mythicItemsIds = mythicItemsIds,
            queueAndChampionIds = queueAndChampionIds, ct = ct)


        ###
        # Save the extracted information
        firstMythicItemCollected.append(firstMythicItem)
        legendaryAndMythicItemsCollected.append(legendaryAndMythicItemsBought)


    ###
    # Concatenate the information and save it
    dataProcessing.concatenateAndSaveExtractedData(region = REGION, firstMythicItemCollected = firstMythicItemCollected,
        legendaryAndMythicItemsCollected = legendaryAndMythicItemsCollected, mythicItemsIds = mythicItemsIds)
