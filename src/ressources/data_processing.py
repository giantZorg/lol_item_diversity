'''

Functions for data processing

'''


###
# Imports
import logging
from typing import Dict, List

import numpy as np
import pandas as pd


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
# Extract the queue id and the champion ids
def extractQueueAndChampions(matchData: Dict) -> Dict:
    '''
    Extract and return the champion ids and the queue id
    '''

    logger.debug('Extract queue id and champion ids for match id %i', matchData['_id'])


    ###
    # Extract both the queue id as well as the chmapion id per participant id from the participant information
    return({'QueueId': matchData['queueId'], 'GameDuration': matchData['gameDuration'], **{
        'Champion_{}'.format(participant['participantId']): participant['championId']
        for participant in matchData['participants']}})


##
# Extract the bought items from the timeline
def extractBoughtMythicAndLegendaryItems(matchData: Dict, legendaryItemsIds: Dict,
        mythicItemsIds: Dict, queueAndChampionIds: Dict, ct: int) -> Dict:
    '''
    Extract the bought mythic and legendary items
    '''

    logger.debug('Extract bought items for match id %i', matchData['_id'])


    ###
    # Create sets for quicker comparisons
    legendaryItems = set(legendaryItemsIds.keys())
    mythicItems = set(mythicItemsIds.keys())


    ###
    # Champion IDs
    championIds = [queueAndChampionIds['Champion_{}'.format(i)] for i in range(1, 11)]


    ###
    # Create the objects for the data
    legendaryItemsEvents = dict()
    mythicItemsEvents = dict()
    for i in range(1, 11):
        legendaryItemsEvents[i] = {'ItemId': list(), 'Timestamp': list(), 'ItemBought': list(), 'ItemSale': list()}
        mythicItemsEvents[i] = {'ItemId': list(), 'Timestamp': list(), 'ItemBought': list(), 'ItemSale': list()}


    ###
    # Extract all item buy or undo events for legendary and mythic items
    for timeframe in matchData['timeline']['frames']:
        for event in timeframe['events']:
            # Item buy events
            if event['type'] == const.TIMELINE_ITEM_BOUGHT:
                # Legendary items
                if event['itemId'] in legendaryItems:
                    legendaryItemsEvents[event['participantId']]['ItemId'].append(event['itemId'])
                    legendaryItemsEvents[event['participantId']]['Timestamp'].append(event['timestamp'])
                    legendaryItemsEvents[event['participantId']]['ItemBought'].append(True)
                    legendaryItemsEvents[event['participantId']]['ItemSale'].append(False)

                # Mythic items
                elif event['itemId'] in mythicItems:
                    mythicItemsEvents[event['participantId']]['ItemId'].append(event['itemId'])
                    mythicItemsEvents[event['participantId']]['Timestamp'].append(event['timestamp'])
                    mythicItemsEvents[event['participantId']]['ItemBought'].append(True)
                    mythicItemsEvents[event['participantId']]['ItemSale'].append(False)

            # Item undo events
            elif event['type'] == const.TIMELINE_ITEM_RETURNED:
                # Legendary items
                if event['beforeId'] in legendaryItems:
                    legendaryItemsEvents[event['participantId']]['ItemId'].append(event['beforeId'])
                    legendaryItemsEvents[event['participantId']]['Timestamp'].append(event['timestamp'])
                    legendaryItemsEvents[event['participantId']]['ItemBought'].append(False)
                    legendaryItemsEvents[event['participantId']]['ItemSale'].append(False)

                # Mythic items
                elif event['beforeId'] in mythicItems:
                    mythicItemsEvents[event['participantId']]['ItemId'].append(event['beforeId'])
                    mythicItemsEvents[event['participantId']]['Timestamp'].append(event['timestamp'])
                    mythicItemsEvents[event['participantId']]['ItemBought'].append(False)
                    mythicItemsEvents[event['participantId']]['ItemSale'].append(False)

            # Item sale events
            elif event['type'] == const.TIMELINE_ITEM_SOLD:
                # Legendary items
                if event['itemId'] in legendaryItems:
                    legendaryItemsEvents[event['participantId']]['ItemId'].append(event['itemId'])
                    legendaryItemsEvents[event['participantId']]['Timestamp'].append(event['timestamp'])
                    legendaryItemsEvents[event['participantId']]['ItemBought'].append(False)
                    legendaryItemsEvents[event['participantId']]['ItemSale'].append(True)

                # Mythic items
                elif event['itemId'] in mythicItems:
                    mythicItemsEvents[event['participantId']]['ItemId'].append(event['itemId'])
                    mythicItemsEvents[event['participantId']]['Timestamp'].append(event['timestamp'])
                    mythicItemsEvents[event['participantId']]['ItemBought'].append(False)
                    mythicItemsEvents[event['participantId']]['ItemSale'].append(True)

    ###
    # Extract the first mythic item bought (there is the unlikely event that someone sells and buys another
    # mythic item later on in the game which is not considered here)
    firstMythicItem = list()
    mythicItemBought = dict()  # To use together with the legendary items
    for i in range(1, 11):
        # In most cases, there will only be one event
        nEvents = len(mythicItemsEvents[i]['ItemId'])

        # Defaults if none found
        mythicItemForSummoner = 0
        mythicItemBought[i] = pd.DataFrame({'Item': list(), 'Timestamp': list()})

        if nEvents == 1:
            if mythicItemsEvents[i]['ItemBought'][0]:
                mythicItemForSummoner = mythicItemsEvents[i]['ItemId'][0]
                mythicItemBought[i] = pd.DataFrame({'Item': mythicItemsEvents[i]['ItemId'][0],
                    'Timestamp': mythicItemsEvents[i]['Timestamp'][0]}, index = [0])

        elif nEvents > 1:
            # In this case, a mythic item has been bought, the sale undone and then maybe another mythic item
            # was bought. Sort the events by time and take the item before the first sale event, then after the last
            # undo event
            mythicItemSummonerEvents = pd.DataFrame(mythicItemsEvents[i])

            # Sort by time then select all items before the first sale
            mythicItemSummonerEvents = mythicItemSummonerEvents.sort_values('Timestamp').reset_index()
            mythicItemSummonerEvents = mythicItemSummonerEvents.loc[
                mythicItemSummonerEvents['ItemSale'].cumsum() == 0]

            # Select the last item buy event
            mythicItemSummonerEvents = mythicItemSummonerEvents.loc[mythicItemSummonerEvents['ItemBought']]

            if nLen := (mythicItemSummonerEvents.shape[0]):
                # int() is there to convert the numpy int type to standard int type
                mythicItemForSummoner = int(mythicItemSummonerEvents['ItemId'].iloc[nLen-1])
                mythicItemBought[i] = pd.DataFrame({'Item': int(mythicItemSummonerEvents['ItemId'].iloc[nLen-1]),
                    'Timestamp': int(mythicItemSummonerEvents['Timestamp'].iloc[nLen-1])}, index = [0])

        # In einer Liste abspeichern
        firstMythicItem.append(mythicItemForSummoner)

    # Zum Datenframe umwandeln
    firstMythicItem = pd.DataFrame({'Mythic': firstMythicItem, 'Champion': championIds})


    ###
    # Extract the first 5 legendary/mythic items
    legendaryAndMythicItemsBought = list()
    for i in range(1, 11):
        ##
        # Extract the legendary items with timestamps
        nEvents = len(legendaryItemsEvents[i]['ItemId'])

        legendaryItemsBoughtForSummoner = pd.DataFrame({'Item': list(), 'Timestamp': list()})

        # Only one event, no extra work needed
        if nEvents == 1:
            if legendaryItemsEvents[i]['ItemBought'][0]:
                legendaryItemsBoughtForSummoner = pd.DataFrame({'Item': legendaryItemsEvents[i]['ItemId'][0],
                    'Timestamp': legendaryItemsEvents[i]['Timestamp'][0]}, index = [0])

        elif nEvents > 1:
            # Sort the events by time. Then remove the sale events (we don't consider them for this analysis),
            # any major item sales should happen after the 5 item stage. Afterwards, match the undo (buy) events
            # to the previous event on the same item and remove both events.
            # Do not consider the tear items at this stage (not sure how they behave, only the base version should
            # appear as the upgrade is not technically a buy event, but might be)
            legendaryItemsSummonerEvents = pd.DataFrame(legendaryItemsEvents[i])

            # Remove sales events and sort by time
            legendaryItemsSummonerEvents = legendaryItemsSummonerEvents.loc[
                ~legendaryItemsSummonerEvents['ItemSale']].reset_index(drop = True).sort_values('Timestamp')

            if nBuyAndUndoEvents := legendaryItemsSummonerEvents.shape[0]:   # Case 0 shouldn't happen
                # Match and remove undo events
                undoEvents = np.where(~legendaryItemsSummonerEvents['ItemBought'])[0]

                if nUndoEvents := len(undoEvents):
                    indizesToKeep = [True] * nBuyAndUndoEvents
                    for j in range(0, nUndoEvents):
                        itemIdUndone = legendaryItemsSummonerEvents['ItemId'].iloc[undoEvents[j]]

                        for k in range(undoEvents[j] - 1, -1, -1):
                            if (indizesToKeep[k] and legendaryItemsSummonerEvents['ItemBought'].iloc[k]
                                and legendaryItemsSummonerEvents['ItemId'].iloc[k] == itemIdUndone):
                                indizesToKeep[k] = False

                    # Remove the undone sale events and the undo evens
                    legendaryItemsSummonerEvents = legendaryItemsSummonerEvents.loc[indizesToKeep]
                    legendaryItemsSummonerEvents = legendaryItemsSummonerEvents.loc[
                        legendaryItemsSummonerEvents['ItemBought']].reset_index(drop = True)

            legendaryItemsBoughtForSummoner = legendaryItemsSummonerEvents[['ItemId', 'Timestamp']].rename(
                columns = {'ItemId': 'Item'})

        ##
        # Combine mythic and legendary items, then select the first 5 or fill up to the first 5
        legendaryItemsBoughtForSummoner['Mythic'] = 0
        mythicItemBought[i]['Mythic'] = 1

        legendaryAndMythicTogether = pd.concat([legendaryItemsBoughtForSummoner, mythicItemBought[i]],
            ignore_index = True).sort_values('Timestamp').reset_index(drop = True).iloc[0:5].drop(
            columns = 'Timestamp')

        # Add identifiers (for later groupby's)
        legendaryAndMythicTogether['Champion'] = championIds[i-1]
        legendaryAndMythicTogether['Match'] = ct
        legendaryAndMythicTogether['N_Items'] = legendaryAndMythicTogether.shape[0]

        # Save the dataframe
        legendaryAndMythicItemsBought.append(legendaryAndMythicTogether)

    # Concatenate the items for the different champions
    legendaryAndMythicItemsBought = pd.concat(legendaryAndMythicItemsBought, ignore_index = True)


    ###
    # Add the queue and game duration information
    firstMythicItem['Queue'] = queueAndChampionIds['QueueId']
    firstMythicItem['GameTimeSeconds'] = queueAndChampionIds['GameDuration']

    legendaryAndMythicItemsBought['Queue'] = queueAndChampionIds['QueueId']
    legendaryAndMythicItemsBought['GameTimeSeconds'] = queueAndChampionIds['GameDuration']


    ###
    # Return the mythic and all items
    return(firstMythicItem, legendaryAndMythicItemsBought)


##
# Concatenate and save the extracted data
def concatenateAndSaveExtractedData(region: str, firstMythicItemCollected: List,
        legendaryAndMythicItemsCollected: List, mythicItemsIds: Dict) -> None:
    '''
    Concatenate and save the data extracted from the match data.
    Folder has to exist and will not be created.
    '''

    logger.debug('Save extracted data for region %s', region)

    # Concatenate data
    firstMythicItem = pd.concat(firstMythicItemCollected, ignore_index = True)
    legendaryAndMythicItems = pd.concat(legendaryAndMythicItemsCollected, ignore_index = True)

    legendaryAndMythicItems['Item'] = legendaryAndMythicItems['Item'].astype(int)

    # Save data
    firstMythicItem.to_csv('{}{}'.format(const.FOLDER_DATA, const.MYTHIC_DATA_FILE.format(
        region = region, dateFrom = const.EARLIEST_DATE_FOR_GAMES, dateTo = const.LATEST_DATE_FOR_GAMES
    )), index = False)
    legendaryAndMythicItems.to_csv('{}{}'.format(const.FOLDER_DATA, const.LEGENDARY_MYTHIC_DATA_FILE.format(
        region = region, dateFrom = const.EARLIEST_DATE_FOR_GAMES, dateTo = const.LATEST_DATE_FOR_GAMES
    )), index = False)

    pd.DataFrame(mythicItemsIds, index = [0]).transpose().reset_index().rename(
        columns = {'index': 'Id', 0: 'Item'}).to_csv('{}{}'.format(const.FOLDER_DATA,
        const.MYTHIC_IDS), index = False)

    ###
    # End of function
    return
