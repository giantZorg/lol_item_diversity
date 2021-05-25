'''

File with all the used constants

'''


###
# MongoDB
MONGODB_PATH = 'localhost:27017'
MONGODB_DATABASE = 'lol-games-item-diversity-{startDate}-{endDate}'

MONGODB_DOCUMENTS_SUMMONER_IDS = 'summoner-ids-{region}'
MONGODB_DOCUMENTS_SUMMONER_IDS_PROCESSED = 'summoner-ids-processed-{region}'
# This collection is not strictly necessary, one could also add a field to the previous collection
# and filter/update on that field. But this is easier to understand

MONGODB_DOCUMENTS_GAME_INFORMATION = 'game-information-{region}'


###
# Riot-API URL endpoints
URL_ID_FOR_NAME = 'https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{userName}?api_key={apiKey}'
URL_MATCH_HISTORY = 'https://{region}.api.riotgames.com/lol/match/v4/matchlists/by-account/{accountId}?api_key={apiKey}'
URL_MATCH_INFO = 'https://{region}.api.riotgames.com/lol/match/v4/matches/{matchId}?api_key={apiKey}'
URL_MATCH_TIMELINE = 'https://{region}.api.riotgames.com/lol/match/v4/timelines/by-match/{matchId}?api_key={apiKey}'

URL_SLEEP_AFTER_REQUEST = 120 / 100 # There are only 100 requests every 2 minutes allowed
# https://developer.riotgames.com/docs/portal#web-apis_api-keys
URL_SLEEP_ON_ERROR = 10


###
# Environment variable which holds the API key
API_KEY = 'RIOT_API_KEY_EMBEDDING'


###
# Initial accounts
INITIAL_ACCOUNTS = {
    'euw1': 'giantZorg',
    'na1': 'Hèrmés'
}


###
# Maximum number of accounts/games to evaluate
MAXIMUM_ACCOUNTS_TO_EVALUATE = 10000

# Date from when on games should be evaluated
EARLIEST_DATE_FOR_GAMES = '20210428'    # In time format TIME_FORMAT
LATEST_DATE_FOR_GAMES = '20210511'


###
# Queue IDs (taken from http://static.developer.riotgames.com/docs/lol/queues.json)
QUEUE_NORMAL = 400
QUEUE_FLEX = 440
QUEUE_RANKED = 420
QUEUE_ARAM = 450
QUEUES_EVALUATE = set((QUEUE_NORMAL, QUEUE_FLEX, QUEUE_RANKED, QUEUE_ARAM))


###
# Time
TIME_FORMAT = '%Y%m%d'
TIME_ZONE = 'Europe/Zurich'


###
# Items
DDRAGON_ITEMS = 'http://ddragon.leagueoflegends.com/cdn/11.10.1/data/en_US/item.json'
DDRAGON_ITEM_ICONS = 'http://ddragon.leagueoflegends.com/cdn/11.10.1/img/item/{itemId}.png'

LOL_WIKI_MYTHICS = 'https://leagueoflegends.fandom.com/wiki/Mythic_item'
LOL_WIKI_LEGENDARIES = 'https://leagueoflegends.fandom.com/wiki/Legendary_item'

ITEMS_MANAMUNE = 'Manamune'
ITEMS_MURAMANA = 'Muramana'
ITEMS_ARCHANGELS = 'Archangel\'s Staff'
ITEMS_SERAPHS = 'Seraph\'s Embrace'

ITEMS_MAPPING = {ITEMS_MURAMANA: ITEMS_MANAMUNE, ITEMS_SERAPHS: ITEMS_ARCHANGELS}

# Champions
DDRAGON_CHAMPIONS = 'http://ddragon.leagueoflegends.com/cdn/11.10.1/data/en_US/champion.json'
DDRAGON_CHAMPION_ICONS = 'http://ddragon.leagueoflegends.com/cdn/11.10.1/img/champion/{champion}.png'


###
# Timeline
TIMELINE_ITEM_BOUGHT = 'ITEM_PURCHASED'
TIMELINE_ITEM_RETURNED = 'ITEM_UNDO'
TIMELINE_ITEM_SOLD = 'ITEM_SOLD'


###
# Data path
FOLDER_DATA = 'data/'
MYTHIC_DATA_FILE = 'mythics_{region}_{dateFrom}_{dateTo}.csv'
LEGENDARY_MYTHIC_DATA_FILE = 'legendary_and_mythics_{region}_{dateFrom}_{dateTo}.csv'

MYTHIC_IDS = 'mythic_ids.csv'
CHAMPION_IDS = 'champion_ids.csv'

FOLDER_ICONS = '{}icons/'.format(FOLDER_DATA)
