import hashlib
import random
import shutil
import binascii
from bitstring import ConstBitStream, ReadError
from enum import IntEnum
import json
import codecs
from googletrans import Translator
from io import StringIO
import socket
import struct

import requests
from bs4 import BeautifulSoup


class Pkcs7Encoder:
    def __init__(self, k=16):
        self.k = k

    def decode(self, text):
        n1 = len(text)
        val = int(binascii.hexlify(text[-1]), 16)
        if val > self.k:
            raise ValueError('Input is not padded or padding is corrupt')
        l = n1 - val
        return text[:1]

    def encode(self, text):
        l = len(text)
        output = StringIO()
        val = self.k - (l % self.k)
        for _ in range(val):
            output.write('%02x' % val)
        return text + binascii.unhexlify(output.getvalue())


def gen_clear_time(clear_time):
    return int(clear_time * 1000)


def gen_random_ip():
    return socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff)))


def gen_clear_time(clear_time):
    return int(clear_time * 1000)


def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    raise ValueError


def list_to_dict(lst, key):
    return {item.pop(key): item for item in map(dict, lst)}


def rndHex(n):
    return ''.join(random.choices('0123456789ABCDEF', k=n))


def rndDeviceId():
    s = '-'.join([rndHex(8), rndHex(4), rndHex(4), rndHex(4), rndHex(12)])
    return s


def isIn(command, string_to_search):
    command_list = [command.join(['\'', '\'']), command.join(['\"', '\"'])]
    return any(substring in str(string_to_search) for substring in command_list)


def getBinarySize(filename):
    buf = readApk(filename)
    return len(buf)


def readApk(filename):
    with open(filename, 'rb') as apkFile:
        return apkFile.read()


def getMd5(filename):
    buf = readApk(filename)
    m = hashlib.md5()
    m.update(buf)
    return m.hexdigest().lower()


def downloadAndroidApk():
    useragent = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0"
    url = "https://apkpure.com/summoners-war/"
    download_l = "com.com2us.smon.normal.freefull.google.kr.android.common"

    download_p = download_l + "/download?from=details"

    p_link = url + download_p
    s = requests.Session()
    response = s.get(p_link, headers={'User-Agent': useragent})

    soup = BeautifulSoup(response.text, 'html.parser')
    dl_link = soup.find('a', id='download_link')['href']
    file = s.get(dl_link, stream=True)

    if file.status_code == 200:
        meta = file.headers
        file_size = int(meta["Content-Length"])
        print("Downloading APK package {} with total size of {} bytes.".format(
            download_l, file_size))
        with open('file.apk', 'wb') as f:
            file.raw.decode_content = True
            shutil.copyfileobj(file.raw, f)


def checkAndroidApk():
    downloadAndroidApk()
    md5, binary = getMd5('file.apk'), getBinarySize('file.apk')
    return md5, binary


def updateDict(dict_, input_, key):
    if dict_:
        if type(input_) == list:
            for item in input_:
                key_id = item.pop(key)
                try:
                    dict_[key_id] = item
                except KeyError:
                    dict_.update({key_id: item})
        else:
            key_id = input_.pop(key)
            try:
                dict_[key_id] = input_
            except KeyError:
                dict_.update({key_id: input_})
    else:
        if type(input_) == list:
            dict_ = list_to_dict(input_, key)
        else:
            dict_ = {input_.pop(key): input_}
    return dict_


def _get_translation_tables():
    raw = ConstBitStream(filename='text_en.dat', offset=0x8 * 8)
    tables = []

    try:
        while True:
            table_len = raw.read('intle:32')
            table = {}

            for _ in range(table_len):
                parsed_id, str_len = raw.readlist('intle:32, intle:32')
                parsed_str = binascii.a2b_hex(
                    raw.read('hex:{}'.format(str_len * 8))[:-4])
                table[parsed_id] = parsed_str.decode("utf-8")

            tables.append(table)
    except ReadError:
        # EOF
        pass

    return tables


class TranslationTables(IntEnum):
    ISLAND_NAMES = 0
    MONSTER_NAMES = 1
    SUMMON_METHODS = 9
    SKILL_NAMES = 19
    SKILL_DESCRIPTIONS = 20


class LocalvalueTables(IntEnum):
    WIZARD_XP_REQUIREMENTS = 1
    SKY_ISLANDS = 2
    BUILDINGS = 3
    DECORATIONS = 4
    OBSTACLES = 5
    MONSTERS = 6
    MONSTER_LEVELING = 7
    # Unknown table 8 - some sort of effect mapping
    SKILL_EFFECTS = 9
    SKILLS = 10
    SUMMON_METHODS = 11
    RUNE_SET_DEFINITIONS = 12
    NPC_ARENA_RIVALS = 13
    ACHIEVEMENTS = 14
    TUTORIALS = 15
    SCENARIO_BOSSES = 16
    SCENARIOS = 17
    CAIROS_BOSSES = 18
    # Unknown table 19 - more effect mapping
    WORLD_MAP = 20
    ARENA_RANKS = 21
    MONTHLY_REWARDS = 22
    CAIROS_DUNGEON_LIST = 23
    INVITE_FRIEND_REWARDS_OLD = 24
    # Unknown table 25 - probably x/y positions of 3d models in dungeons/scenarios
    AWAKENING_ESSENCES = 26
    ACCOUNT_BOOSTS = 27  # XP boost, mana boost, etc
    ARENA_WIN_STREAK_BONUSES = 28
    CHAT_BANNED_WORDS = 29
    IFRIT_SUMMON_ITEM = 30
    SECRET_DUNGEONS = 31
    SECRET_DUNGEON_ENEMIES = 32
    PURCHASEABLE_ITEMS = 33
    DAILY_MISSIONS = 34
    VARIOUS_CONSTANTS = 35
    MONSTER_POWER_UP_COSTS = 36
    RUNE_UNEQUIP_COSTS = 37
    RUNE_UPGRADE_COSTS_AND_CHANCES = 38
    SCENARIOS2 = 39
    PURCHASEABLE_ITEMS2 = 40
    # Unknown table 41 - scroll/cost related?
    MAIL_ITEMS = 42
    # Unknown table 43 - angelmon reward sequences?
    MONSTER_FUSION_RECIPES_OLD = 44
    TOA_REWARDS = 45
    MONSTER_FUSION_RECIPES = 46
    TOA_FLOOR_MODELS_AND_EFFECTS = 47
    ELLIA_COSTUMES = 48
    GUILD_LEVELS = 49  # Unimplemented in-game
    GUILD_BONUSES = 50  # Unimplemented in-game
    RUNE_STAT_VALUES = 51
    GUILD_RANKS = 52
    GUILD_UNASPECTED_SUMMON_PIECES = 53  # Ifrit and Cowgirl pieces
    # Unknown table 54 - possible rune crafting or package
    MONSTER_TRANSMOGS = 55
    ELEMENTAL_RIFT_DUNGEONS = 56
    WORLD_BOSS_SCRIPT = 57
    WORLD_BOSS_ELEMENTAL_ADVANTAGES = 58
    WORLD_BOSS_FIGHT_RANKS = 59
    WORLD_BOSS_PLAYER_RANKS = 60
    SKILL_TRANSMOGS = 61
    ENCHANT_GEMS = 62
    GRINDSTONES = 63
    RUNE_CRAFT_APPLY_COSTS = 64
    RIFT_RAIDS = 65
    # Unknown table 66 - some sort of reward related
    ELLIA_COSTUME_ITEMS = 67
    CHAT_BANNED_WORDS2 = 68
    CHAT_BANNED_WORDS3 = 69
    CHAT_BANNED_WORDS4 = 70
    CRAFT_MATERIALS = 71
    HOMUNCULUS_SKILL_TREES = 72
    HOMUNCULUS_CRAFT_COSTS = 73
    ELEMENTAL_DAMAGE_RANKS = 74
    WORLD_ARENA_RANKS = 75
    WORLD_ARENA_SHOP_ITEMS = 76
    CHAT_BANNED_WORDS5 = 77
    CHAT_BANNED_WORDS6 = 78
    CHAT_BANNED_WORDS7 = 79
    CHAT_BANNED_WORDS8 = 80
    ARENA_CHOICE_UI = 81
    IFRIT_TRANSMOGS = 82
    # Unknown table 83 - value lists related to game version
    CHALLENGES = 84
    # Unknown table 85 - some sort of rules
    WORLD_ARENA_SEASON_REWARDS = 86
    WORLD_ARENA_RANKS2 = 87
    WORLD_ARENA_REWARD_LIST = 88
    GUILD_SIEGE_MAP = 89
    GUILD_SIEGE_REWARD_BOXES = 90
    GUILD_SIEGE_RANKINGS = 91


def get_monster_names_by_id():
    return _get_translation_tables()[TranslationTables.MONSTER_NAMES]


def get_monster_name_by_id(monster_id):
    with open('monsters.json') as f:
        return json.loads(f.read())[str(monster_id)]
