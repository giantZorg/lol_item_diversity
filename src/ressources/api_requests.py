'''

Functions to request data from the Riot APIs

'''


###
# Imports
from datetime import datetime
import json
import logging
import os
import time
from typing import Dict, List, Union, Tuple

from bs4 import BeautifulSoup
import pandas as pd
from PIL import Image
from pytz import timezone
import requests
from tqdm import tqdm


###
# Load ressources
try:
    import src.ressources.constants as const
except Exception:
    import ressources.constants as const


###
# Logging
logger = logging.getLogger(__name__)


###
# Functions

##
# Set proxy
def setApiKeyAndProxy() -> Tuple[str, Union[Dict, None]]:
    '''
    Load api key and proxy informations from environment variables
    '''

    logger.info('Load api key and proxy information from environment variables')

    ###
    # Load the API key
    if (apiKey := os.environ.get(const.API_KEY, None)) is None:
        raise AssertionError('API key not found')


    ###
    # Check the two variables http_proxy and https_proxy, if one is missing set the object to None
    proxies = {'http': os.environ.get('http_proxy'), 'https': os.environ.get('https_proxy')}

    if proxies['http'] is None or proxies['https'] is None:
        proxies = None


    ###
    # Return the proxy information
    return(apiKey, proxies)


##
# Get current time as unix-time
def currentTime() -> int:
    '''
    Returns the current time in unix time
    '''
    return(int(time.mktime(datetime.today().astimezone(timezone(const.TIME_ZONE)).timetuple())))


##
# Get initial summoner id
def getInitialSummonerId(region: str, summonerName: str, apiKey: str, proxies: Union[Dict, None]) -> str:
    '''
    Send API request to get the summoner id for the initial summoner which starts the whole
    search chain
    '''

    logger.debug('Get summoner id for summoner %s in region %s', summonerName, region)


    ###
    # Repeated try to get the data. Repeated as this could break if the proxy is reset during operation
    successfull = False
    while not successfull:
        try:
            initialAccountResponse = requests.get(const.URL_ID_FOR_NAME.format(
                region = region, userName = summonerName, apiKey = apiKey
            ), verify = False, proxies = proxies)   # Set verify to False to disable SSL verification

            if successfull := (initialAccountResponse.status_code == 200):
                logger.debug('Summoner id successfull retrieved')

            else:
                logger.warning('Could not retrieve summoner id, retrying')

                # Add a sleep period to prevent more requests than allowed
                if initialAccountResponse.status_code == 429:
                    time.sleep(int(initialAccountResponse.headers['Retry-After']) + 1)
                else:
                    time.sleep(const.URL_SLEEP_AFTER_REQUEST)


        except Exception as err:
            logger.error('Unexpected error while retrieving the inital summoner id: %s', str(err))

            time.sleep(const.URL_SLEEP_ON_ERROR)


    ###
    # Extract id and account id from the retrieved json data, then add the current time
    initialAccount = {keyDict: json.loads(initialAccountResponse.text)[keyJson] for keyJson, keyDict in
        zip(('id', 'accountId'), ('SummonerId', 'SummonerAccountId'))}
    initialAccount['TimeCreated'] = currentTime()


    ###
    # Return the account information
    return(initialAccount)


##
# Get the match history for a summoner id
def getMatchHistory(region: str, summonerAccountId: str, apiKey: str, proxies: Union[Dict, None]) -> Dict:
    '''
    Send API request to get the match history for a given summoner account id. Be aware that only the last 100
    games of an account are sent back by the API (could be changed, but should change the result much)
    '''

    logger.debug('Get match history for summoner id %s in region %s', summonerAccountId, region)


    ###
    # Repeated try to get the data. Repeated as this could break if the proxy is reset during operation
    successfull = False
    while not successfull:
        try:
            matchHistory = requests.get(const.URL_MATCH_HISTORY.format(
                region = region, accountId = summonerAccountId, apiKey = apiKey
            ), verify = False, proxies = proxies)   # Set verify to False to disable SSL verification

            if successfull := (matchHistory.status_code == 200):
                logger.debug('Match history for summoner id %s successfull retrieved', summonerAccountId)

            elif matchHistory.status_code in (400, 404):
                # Bad request, cannot be fixed, probably changed account id or deleted or something else
                logger.warning('Bad request returned for summoner id %s', summonerAccountId)
                break

            else:
                logger.warning('Could not retrieve match history for summoner id %s, retrying', summonerAccountId)

                # Add a sleep period to prevent more requests than allowed
                if matchHistory.status_code == 429:
                    time.sleep(int(matchHistory.headers['Retry-After']) + 1)
                else:
                    time.sleep(const.URL_SLEEP_AFTER_REQUEST)


        except Exception as err:
            logger.error('Unexpected error while retrieving the match history for summoner id %s: %s',
                summonerAccountId, str(err))

            time.sleep(const.URL_SLEEP_ON_ERROR)

    ##
    # Add a sleep period in order not to send too many API requests
    logger.debug('Match history for summoner id %s retrieved, start sleep period', summonerAccountId)
    time.sleep(const.URL_SLEEP_AFTER_REQUEST)


    ##
    # Transform and return the request object to a dictionary which is used later on
    if successfull:
        return(json.loads(matchHistory.text))
    else:
        return(dict())


##
# Get the match information for a match id
def getMatchInformation(region: str, matchId: int, apiKey: str, proxies: Union[Dict, None]) -> Dict:
    '''
    Send API request to get the match information for a given match id
    '''

    logger.debug('Get match information for match id %i in region %s', matchId, region)


    ###
    # Repeated try to get the data. Repeated as this could break if the proxy is reset during operation
    successfull = False
    while not successfull:
        try:
            matchInformation = requests.get(const.URL_MATCH_INFO.format(
                region = region, matchId = matchId, apiKey = apiKey
            ), verify = False, proxies = proxies)   # Set verify to False to disable SSL verification

            if successfull := (matchInformation.status_code == 200):
                logger.debug('Match information for match id %s successfull retrieved', matchId)

            elif matchInformation.status_code in (400, 404):
                # Bad request, cannot be fixed, probably changed account id or deleted or something else
                logger.warning('Bad request returned for match id %s', matchId)
                break

            else:
                logger.warning('Could not retrieve match information for match id %s, retrying', matchId)

                # Add a sleep period to prevent more requests than allowed
                if matchInformation.status_code == 429:
                    time.sleep(int(matchInformation.headers['Retry-After']) + 1)
                else:
                    time.sleep(const.URL_SLEEP_AFTER_REQUEST)


        except Exception as err:
            logger.error('Unexpected error while retrieving the match information for match id %s: %s',
                matchId, str(err))

            time.sleep(const.URL_SLEEP_ON_ERROR)

    ##
    # Add a sleep period in order not to send too many API requests
    logger.debug('Match information for match id %s retrieved, start sleep period', matchId)
    time.sleep(const.URL_SLEEP_AFTER_REQUEST)


    ##
    # Transform and return the request object to a dictionary which is used later on
    if successfull:
        return(json.loads(matchInformation.text))
    else:
        return(dict())


##
# Get the match timeline for a match id
def getMatchTimeline(region: str, matchId: int, apiKey: str, proxies: Union[Dict, None]) -> Dict:
    '''
    Send API request to get the match timeline for a given match id
    '''

    logger.debug('Get match timeline for match id %i in region %s', matchId, region)


    ###
    # Repeated try to get the data. Repeated as this could break if the proxy is reset during operation
    successfull = False
    while not successfull:
        try:
            matchTimeline = requests.get(const.URL_MATCH_TIMELINE.format(
                region = region, matchId = matchId, apiKey = apiKey
            ), verify = False, proxies = proxies)   # Set verify to False to disable SSL verification

            if successfull := (matchTimeline.status_code == 200):
                logger.debug('Match timeline for match id %s successfull retrieved', matchId)

            else:
                logger.warning('Could not retrieve match timeline for match id %s, retrying', matchId)

                # Add a sleep period to prevent more requests than allowed
                if matchTimeline.status_code == 429:
                    time.sleep(int(matchTimeline.headers['Retry-After']) + 1)
                else:
                    time.sleep(const.URL_SLEEP_AFTER_REQUEST)


        except Exception as err:
            logger.error('Unexpected error while retrieving the match timeline for match id %s: %s',
                matchId, str(err))

            time.sleep(const.URL_SLEEP_ON_ERROR)

    ##
    # Add a sleep period in order not to send too many API requests
    logger.debug('Match timeline for match id %s retrieved, start sleep period', matchId)
    time.sleep(const.URL_SLEEP_AFTER_REQUEST)


    ##
    # Transform and return the request object to a dictionary which is used later on
    return(json.loads(matchTimeline.text))


##
# Get the item information json
def getItemInformation(proxies: Union[Dict, None]) -> List[Dict]:
    '''
    Download the full item information from http://ddragon.leagueoflegends.com/cdn/11.10.1/data/en_US/item.json
    then also only take the subset containing the mythic and legendary items.

    The mythic and legendary items are not marked as such inside the json, this information is taken from
    lolwiki (https://leagueoflegends.fandom.com/wiki/Mythic_item and )
    '''

    logger.debug('Get the item informations')


    ###
    # Download the data from data dragon
    itemRawData = requests.get(const.DDRAGON_ITEMS, verify = False, proxies = proxies)

    if itemRawData.status_code != 200:
        raise AssertionError('Item data from data dragon could not be downloaded')

    itemRawData = json.loads(itemRawData.text)


    ###
    # Download the legendary and mythic items

    ##
    # Mythic items
    mythicItemsHtml = requests.get(const.LOL_WIKI_MYTHICS, verify = False, proxies = proxies)

    if mythicItemsHtml.status_code != 200:
        raise AssertionError('Mythic item information from lol wiki cound not be downloaded')

    mythicItemsHtml = BeautifulSoup(mythicItemsHtml.text, features = "html.parser")

    # Extract all the entries from the table containing the mythic items.
    # They are found in <span ...>...</span> blocks which have the attribute data-item
    mythicItems = {itemDescription.text.strip().lower() for itemDescription
        in mythicItemsHtml.find_all('span', {'data-item': True})}


    ##
    # Legendary items
    legendaryItemsHtml = requests.get(const.LOL_WIKI_LEGENDARIES, verify = False, proxies = proxies)

    if legendaryItemsHtml.status_code != 200:
        raise AssertionError('Mythic item information from lol wiki cound not be downloaded')

    legendaryItemsHtml = BeautifulSoup(legendaryItemsHtml.text, features = "html.parser")

    # Extract all the entries from the table containing the mythic items.
    # They are found in <span ...>...</span> blocks which have the attribute data-item
    legendaryItems = {itemDescription.text.strip().lower() for itemDescription
        in legendaryItemsHtml.find_all('span', {'data-item': True})}


    ###
    # Extract the relevant item ids as mappings from the raw item data
    legendaryItemsIds = dict()
    mythicItemsIds = dict()

    for itemId, itemDescription in itemRawData['data'].items():
        if itemDescription['name'].lower() in legendaryItems:
            legendaryItemsIds[int(itemId)] = itemDescription['name']

        elif itemDescription['name'].lower() in mythicItems:
            mythicItemsIds[int(itemId)] = itemDescription['name']

    # Ensure that all items were successfully mapped
    if len(legendaryItems) != len(legendaryItemsIds):
        raise AssertionError('Not all legendary items were successfully mapped')

    if len(mythicItems) != len(mythicItemsIds):
        raise AssertionError('Not all mythic items were successfully mapped')


    ###
    # Get the ids for the tear items because they evolve and therefore could theoretically confuse
    # the evaluation. This will be solved by mapping the evolved version onto the base version
    tearItemMappings = dict()
    for evolvedItem, basicItem in const.ITEMS_MAPPING.items():
        for itemId, itemName in legendaryItemsIds.items():
            if itemName == evolvedItem:
                evolvedItemId = itemId
            elif itemName == basicItem:
                basicItemId = itemId

        tearItemMappings[evolvedItemId] = basicItemId


    ###
    # Return the various informations
    return(itemRawData, legendaryItemsIds, mythicItemsIds, tearItemMappings)



##
# Get champion data
def getChampionInfoAndIcons(proxies: Union[Dict, None]) -> None:
    '''
    Download the json with the champion information, save the relevant mapping and in addition
    the champion icons
    '''

    logger.debug('Get champion information and icons')

    ###
    # Download champion information
    championRawInformation = requests.get(const.DDRAGON_CHAMPIONS, verify = False, proxies = proxies)

    if championRawInformation.status_code != 200:
        raise AssertionError('Champion information from data dragon could not be downloaded')

    championRawInformation = json.loads(championRawInformation.text)


    ##
    # Extract the name <-> id mapping
    championsIds = list()
    championsIdName = list()
    championsNames = list()

    for championEntry in championRawInformation['data'].values():
        championsIdName.append(championEntry['id'])
        championsIds.append(championEntry['key'])
        championsNames.append(championEntry['name'])

    # Concatenate and save the information
    championInformation = pd.DataFrame({'Id': championsIds, 'IdName': championsIdName, 'Name': championsNames})
    championInformation['Id'] = championInformation['Id'].astype(int)

    championInformation.to_csv('{}{}'.format(const.FOLDER_DATA, const.CHAMPION_IDS), index = False)


    ###
    # Download and save the icons
    for championIdName in tqdm(championInformation['IdName']):
        championIcon = Image.open(requests.get(const.DDRAGON_CHAMPION_ICONS.format(champion = championIdName),
            stream = True, proxies = proxies).raw)

        championIcon.save('{}{}.png'.format(const.FOLDER_ICONS, championIdName))


    ###
    # End of function
    return


##
# Get item icons
def getItemIcons(legendaryItemsIds: Dict, mythicItemsIds: Dict, proxies: Union[Dict, None]) -> None:
    '''
    Download the json with the champion information, save the relevant mapping and in addition
    the champion icons
    '''

    logger.debug('Get item icons')


    ###
    # Create list of item ids, then download and save them. Use the id and not the name
    # as the names don't make for good filenames
    itemIds = list(legendaryItemsIds.keys()) + list(mythicItemsIds.keys())

    for itemId in tqdm(itemIds):
        itemIcon = Image.open(requests.get(const.DDRAGON_ITEM_ICONS.format(itemId = itemId),
            stream = True, proxies = proxies).raw)

        itemIcon.save('{}{}.png'.format(const.FOLDER_ICONS, itemId))


    ###
    # End of function
    return
