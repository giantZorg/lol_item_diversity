'''

Main module to download the necessary data for the item diversity analysis from the Riot games API
(https://developer.riotgames.com/).

The main goal of the analysis is to try to identify how much item diversity there exists is lol, once
for mythic items, followed by first/second/third/... item and maybe also item combination (without
considering the item order). Boots will probably be excluded.

This analysis could also be done for various regions, trying to identify differences between them.
In addition, it could also be done comparing normal/flex/ranked games e.g. to see whether people try
more things in normal/flex compared to ranked.

The data will be collected the following way:
- Start with an initial summoner (my summoner, currently gold 4, so somewhat average)
- Get a list of recently played normal/flex/ranked/ARAM games to get more summoner ids.
- Download the game information for all/some of the found games, storing the information either to
  file or to a NoSQL database. Be aware that the API by default only returns the last 100
  games played
- Select a new summoner id and repeat steps 2 and 3 until enough data has been collected.

For this project, a local MongoDB is used (https://docs.mongodb.com/guides/server/install/).

'''


###
# Imports
import logging

from tqdm import tqdm
import urllib3


###
# Load ressources
try:
    import src.ressources.constants as const
    import src.ressources.mongodb as mongodb
    import src.ressources.api_requests as apiRequests
    import src.ressources.api_data_transformations as apiDataTransformations
except Exception:
    import ressources.constants as const
    import ressources.mongodb as mongodb
    import ressources.api_requests as apiRequests
    import ressources.api_data_transformations as apiDataTransformations



###
# Logging
logging.basicConfig(level = 'INFO') # Set to DEBUG for more informations
logger = logging.getLogger(__name__)


###
# Set run-specific constants
# REGION = 'euw1'
REGION = 'na1'


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
    # Load api key and proxy information
    apiKey, proxies = apiRequests.setApiKeyAndProxy()


    ###
    # Get initial summoner id from provided summoner name. This has to be done as
    # all APIs work via a summoner id (which I think is modified by the used API key
    # and can vary therefore when using different keys).
    #
    # Afterwards, save it into the summoner collection in the database
    initialAccount = apiRequests.getInitialSummonerId(
        region = REGION,
        summonerName = const.INITIAL_ACCOUNTS[REGION],
        apiKey = apiKey,
        proxies = proxies
    )
    mongodb.saveSummoner(mongoDbDatabase = mongoDbDatabase, region = REGION,
        summonerInformation = initialAccount, checkIfExists = True)


    ###
    # Create sets for the available summoners, evaluated summoners and evaluated matches.
    # Having these sets in memory reduces the need to call the database
    evaluatedSummoners = mongodb.getIdsOfCollection(mongoDbDatabase = mongoDbDatabase,
        dbCollection = const.MONGODB_DOCUMENTS_SUMMONER_IDS_PROCESSED, region = REGION)

    availableSummoners = mongodb.getIdsOfCollection(mongoDbDatabase = mongoDbDatabase,
        dbCollection = const.MONGODB_DOCUMENTS_SUMMONER_IDS, region = REGION) - evaluatedSummoners

    savedMatches = mongodb.getIdsOfCollection(mongoDbDatabase = mongoDbDatabase,
        dbCollection = const.MONGODB_DOCUMENTS_GAME_INFORMATION, region = REGION)

    if not availableSummoners:
        raise AssertionError('No summoners to evaluate found after initialization')


    ###
    # Iterate over summoners:
    # First, find a new summoner that has not been evaluated yet. Then download the match history
    # for this summoner, selecting only normal, flex and ranked games. Add all new summoners to the
    # collection of summoners to be evaluated. Then save all the games in the relevant time window.

    for _ in tqdm(range(const.MAXIMUM_ACCOUNTS_TO_EVALUATE)):
        ##
        # Get a new summoner id. Inside a try statement because there will be an error if none is found
        logger.debug('Select new summoner to evaluate')
        try:
            summonerAccountId = availableSummoners.pop()

        except Exception:
            logger.warning('No summoners to evaluate available inside loop, end of loop')
            break


        ##
        # Retrieve match history and select the relevant matches
        logger.debug('Get match history for summoner %s', summonerAccountId)

        matchHistory = apiRequests.getMatchHistory(region = REGION, summonerAccountId = summonerAccountId,
            apiKey = apiKey, proxies = proxies)

        relevantMatches, relevantMatchIds = apiDataTransformations.getRelevantMatchesFromHistory(
            matchHistory = matchHistory)


        ##
        # Compare the played games with the already processed games to find those that have not yet been
        # processed
        newMatchIds = relevantMatchIds - savedMatches


        ##
        # If new matches are present, iterate over them to retrieve and save the match data
        if newMatchIds:
            logger.debug('Process found matches')

            for matchId in tqdm(newMatchIds):
                logger.debug('Process match with it %i', matchId)

                ##
                # Retrieve the match information and timeline
                matchInformation = apiRequests.getMatchInformation(region = REGION,
                    matchId = matchId, apiKey = apiKey, proxies = proxies)

                matchTimeline = apiRequests.getMatchTimeline(region = REGION,
                    matchId = matchId, apiKey = apiKey, proxies = proxies)


                ##
                # Save the match data into the corresponding collection
                mongodb.saveRetrievedMatchData(mongoDbDatabase = mongoDbDatabase, region = REGION,
                    matchId = matchId, matchInformation = matchInformation, matchTimeline = matchTimeline)


                ##
                # Extract the account ids for all new participants
                newSummonersInMatch = apiDataTransformations.extractAccountIdsFromMatchInformation(
                    matchInformation = matchInformation, availableSummoners = availableSummoners,
                    evaluatedSummoners = evaluatedSummoners, summonerAccountId = summonerAccountId)


                ##
                # Write the newly found summoners into the collection and set of available summoners
                for newSummonerAccount in newSummonersInMatch.values():
                    mongodb.saveSummoner(mongoDbDatabase = mongoDbDatabase, region = REGION,
                        summonerInformation = newSummonerAccount, checkIfExists = False)

                availableSummoners = availableSummoners.union(set(newSummonersInMatch.keys()))


                ##
                # Update the set with the saved matches
                savedMatches = savedMatches.union(set((matchId, )))



        ##
        # Update the sets and collection of evaluated summoner ids
        logger.debug('Update set and collection of processed summoner ids with id %s', summonerAccountId)

        evaluatedSummoners = evaluatedSummoners.union(set((summonerAccountId, )))
        mongodb.saveProcessedSummoner(mongoDbDatabase = mongoDbDatabase,
            region = REGION, summonerAccountId = summonerAccountId)
