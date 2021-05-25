'''

MongoDB functions

'''


###
# Imports
import copy
import logging
from typing import Dict, Set, Tuple

from pymongo import MongoClient, database, cursor


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
# Function to setup the client and the database
def setupClientAndDatabase() -> Tuple[MongoClient, database.Database]:
    '''
    Function which creates the MongoDB client and creates/connects the database as specified
    in the constants.
    '''

    logger.info('MongoDB client and database are setup')

    ##
    # Create the client
    mongoDbClient = MongoClient(const.MONGODB_PATH)


    ##
    # Create/connect to the database
    mongoDbDatabase = mongoDbClient[const.MONGODB_DATABASE.format(
        startDate = const.EARLIEST_DATE_FOR_GAMES, endDate = const.LATEST_DATE_FOR_GAMES)]

    # To delete the database run mongoDbClient.drop_database(const.MONGODB_DATABASE.format(startDate = const.EARLIEST_DATE_FOR_GAMES, endDate = const.LATEST_DATE_FOR_GAMES)) pylint: disable=line-too-long


    ##
    # Return both objects
    return(mongoDbClient, mongoDbDatabase)


##
# Return all ids of a collection
def getIdsOfCollection(mongoDbDatabase: database.Database, dbCollection: str, region: str) -> Set:
    '''
    Get the set of all ids of the given collection
    '''

    logger.debug('Get set of saved ids of collection %s', dbCollection.format(region = region))

#    return(set(mongoDbDatabase[dbCollection.format(region = region)].find().distinct('_id')))
    return(set([x['_id'] for x in mongoDbDatabase[dbCollection.format(region = region)].aggregate(
        [{'$group': {'_id': '$_id'}}])]))


##
# Save a summoner id information
def saveSummoner(mongoDbDatabase: database.Database, region: str,
        summonerInformation: Dict, checkIfExists: bool = True) -> None:
    '''
    Save the summoner information (id and account id) into the corresponding collection
    '''

    logger.debug('Save summoner id %s', summonerInformation['SummonerAccountId'])

    ###
    # If desired, check first whether the entry already exists. If it already exists,
    # the entry will be updated
    if checkIfExists:
        upsert = mongoDbDatabase[const.MONGODB_DOCUMENTS_SUMMONER_IDS.format(
            region = region)].find_one({'_id': summonerInformation['SummonerAccountId']}) is not None

    else:
        upsert = False


    ###
    # Get the collection object and insert the data.
    # MongoDB wants a unique id which gets added first. The copy is made in order not to
    # affect the original object
    summonerInformation = copy.deepcopy(summonerInformation)
    summonerInformation['_id'] = summonerInformation['SummonerAccountId']

    if upsert:
        logger.debug('Upsert summoner id %s', summonerInformation['_id'])

        mongoDbDatabase[const.MONGODB_DOCUMENTS_SUMMONER_IDS.format(region = region)
            ].find_one_and_replace(filter = {'_id': summonerInformation['SummonerAccountId']},
            replacement = summonerInformation, return_document = False)

    else:
        logger.debug('Insert summoner id %s', summonerInformation['_id'])

        mongoDbDatabase[const.MONGODB_DOCUMENTS_SUMMONER_IDS.format(region = region)
            ].insert_one(summonerInformation)


    ###
    # End of function
    return


##
# Save the processed summoner ids
def saveProcessedSummoner(mongoDbDatabase: database.Database, region: str, summonerAccountId: str) -> None:
    '''
    Save a summoner id to the collection of processed summoners
    '''

    logger.debug('Save summoner id %s to the collection of processed summoners', summonerAccountId)

    ###
    # Save the summoner id as the _id field
    mongoDbDatabase[const.MONGODB_DOCUMENTS_SUMMONER_IDS_PROCESSED.format(region = region)
        ].insert_one({'_id': summonerAccountId})


    ###
    # End of function
    return


##
# Save match data
def saveRetrievedMatchData(mongoDbDatabase: database.Database, region: str, matchId: str,
        matchInformation: Dict, matchTimeline: Dict) -> None:
    '''
    Save the retrieved match data and match timeline into the corresponding collection.
    The matchId is used in the _id field
    '''

    logger.debug('Save match data for match id %i, region %s', matchId, region)


    ###
    # Combine the data into a new dictionary
    matchInformation = copy.deepcopy(matchInformation)  # In order not to modify the original object
    matchInformation['timeline'] = matchTimeline
    matchInformation['_id'] = matchId


    ###
    # Save the data
    mongoDbDatabase[const.MONGODB_DOCUMENTS_GAME_INFORMATION.format(region = region)
        ].insert_one(matchInformation)


    ###
    # End of function
    return


##
# Generator for the timeline data
def getTimelineDataGenerator(mongoDbDatabase: database.Database, region: str) -> cursor.Cursor:
    '''
    Function which returns a generator which can be used to get the timeline data together with the
    queue id and the champions
    '''

    logger.debug('Create the timeline data generator')


    ###
    # Create the generator
    return(mongoDbDatabase[const.MONGODB_DOCUMENTS_GAME_INFORMATION.format(region = region)
        ].find(projection = ['queueId', 'timeline', 'participants', 'gameDuration']))
