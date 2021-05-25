'''

Functions to transform the retrieved data

'''


###
# Imports
import logging
import time
from typing import Dict, List, Set, Tuple

from datetime import datetime, timedelta


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
# Retrieve the matches from the relevant queues in the relevant time frame
def getRelevantMatchesFromHistory(matchHistory: Dict) -> Tuple[Dict, Set]:
    '''
    Extract the relevant matches from the match history. Relevant queues are normal, flex,
    ranked and ARAM within the prespecified time window
    '''

    logger.debug('Get relevant matches from match history')


    ###
    # Convert the dates to the relevant unix timestamps (could be done once to save some little computation time).
    # Multiply by 1000 as the Riot API is in milliseconds, not seconds
    startTimewindow = int(time.mktime(datetime.strptime(const.EARLIEST_DATE_FOR_GAMES, const.TIME_FORMAT).timetuple()))
    startTimewindow *= 1000

    endTimewindow = int(time.mktime((datetime.strptime(const.LATEST_DATE_FOR_GAMES, const.TIME_FORMAT)
        + timedelta(days = 1)).timetuple()))    # Add one day to include the specified date
    endTimewindow *= 1000


    ###
    # Go through the list of played games and keep only the relevant games
    if 'matches' in matchHistory.keys():
        relevantMatches = {match['gameId']: match for match in matchHistory['matches']
            if match['queue'] in const.QUEUES_EVALUATE
                and match['timestamp'] >= startTimewindow and match['timestamp'] < endTimewindow}

    else:
        logger.warning('No matches found in match history')
        relevantMatches = dict()


    ###
    # Collect the game ids into a set for quick comparisons
    if relevantMatches:
        relevantMatchIds = set(relevantMatches.keys())
    else:
        relevantMatchIds = set()


    ###
    # Return the relevant matches
    return(relevantMatches, relevantMatchIds)


##
# Extract the account ids for all participants
def extractAccountIdsFromMatchInformation(matchInformation: Dict,
        availableSummoners: Set, evaluatedSummoners: Set, summonerAccountId: str) -> List:
    '''
    Extract and prepare the summoner ids for all summoners which participated in a match
    '''

    logger.debug('Extract summoner ids from match information')


    ###
    # Extract summoner id and summoner account id (static ones, not the current version fields)
    # for all summoners which were not yet added to the list of available summoners
    newSummonersInMatch = dict()
    for summoner in matchInformation['participantIdentities']:
        summonerAccountIdMatch = summoner['player']['accountId']
        if (summonerAccountIdMatch not in evaluatedSummoners and summonerAccountIdMatch not in availableSummoners and
            summonerAccountId != summonerAccountIdMatch):

            newSummonersInMatch[summonerAccountIdMatch] = {'SummonerAccountId': summonerAccountIdMatch,
                'SummonerId': summoner['player']['summonerId']}


    ###
    # Return dictionary with extracted summoners
    return(newSummonersInMatch)
