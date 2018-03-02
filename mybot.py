import json
import math
import random
import time
from collections import OrderedDict
from datetime import datetime

import requests
import urllib3
import ast

from api import API
from mapping import inventory_type_map, buy_type_map, summon_source_map, experience_level_up_map, \
    summon_type_map, decoration_upgrade_cost, max_class_level_map, market_upgrade_cost_map, element_map, scenario_id_map
from qpyou import QPYOU
from tools import find, get_monster_name_by_id



class Bot:
    def __init__(self, user_='', user_mail_='', pw_='', device_id_='', device_=None, region_='eu'):
        self.uid, self.did, self.sessionkey, appID = QPYOU(device_id_, device_).hiveLogin(user_, pw_)
        self.bot = API(self.uid, self.did, user_, user_mail_, self.sessionkey, device_, appID)
        self.bot.set_region(region_)
        self.bot.game_commander = self.GameCommander()
        self.bot.login()
        self.loginDay = datetime.today().date()
        self.bot.GetDailyQuests()
        self.bot.GetMiscReward()
        self.bot.GetMailList()

        if not self.bot.daily_reward_info['is_checked']:
            self.bot.log('Collecting daily reward for day ''{}.'.format(self.bot.daily_reward_info['check_count']))
            self.bot.CheckDailyReward()

        self.bot.GetArenaLog()

        if self.bot.guild['guild_info']:
            self.bot.GetGuildSiegeStatusInfo()

        self.bot.CheckDarkPortalStatus()
        self.bot.GetCostumeCollectionList()

        self.bot.ReceiveDailyRewardSpecial()
        self.bot.receiveDailyRewardInactive()

        if self.bot.guild['guild_info']:
            self.bot.GetGuildSiegeParticipationInfo()
            self.bot.GetGuildSiegeParticipatedSiegeIdList()

        self.bot.GetFriendRequest()
        self.bot.getUnitUpgradeRewardInfo()
        self.bot.GetRTPvPInfo_v3()
        self.bot.GetChatServerInfo()

        self.bot.getRtpvpRejoinInfo()
        self.bot.GetEventTimeTable()
        self.bot.GetNoticeChat()
        self.bot.GetNoticeDungeon()
        self.bot.GetDungeonList()
        self.bot.GetInstanceList()

        self.maintainFriendList()
        self.last_shop_refresh = 0
        self.last_arena_refresh = 0
        self.weekly_devilmon_bought = False
        self.weekly_angelmon_bought = False
        self.current_shop_items = None
        self.scroll_types = [2, 8, 9, 10]

    def refreshEnergy(self):
        # shop item 100001 is energy refresh
        self.checkAndBuy(100001, 0, 0, 0)

    def checkAndBuy(self, item_id, building_id, pos_x, pos_y):
        if self.bot.wizard_info[buy_type_map[self.bot.shop_item_list[item_id]['buy_type']]] >= \
                self.bot.shop_item_list[item_id]['buy_cost'][0]:
            self.bot.BuyShopItem(item_id, building_id, pos_x, pos_y)
        else:
            self.bot.log('Not enough {type} ({amount}) to buy item. {cost} {type} needed.'.format(
                type=buy_type_map[self.bot.shop_item_list[item_id]['buy_type']],
                amount=self.bot.wizard_info[buy_type_map[self.bot.shop_item_list[item_id]['buy_type']]],
                cost=self.bot.shop_item_list[item_id]['buy_cost'][0]))

    def openShopSlots(self):
        current_slots = self.bot.market_info['open_slots']
        # self.bot.log(current_slots)
        while current_slots < 12:
            upgrade_cost = market_upgrade_cost_map[current_slots + 1]['cost']
            type_ = market_upgrade_cost_map[current_slots + 1]['type']
            if self.bot.wizard_info[type_] >= upgrade_cost:
                self.bot.OpenBlackMarketSlot()
                self.bot.log('Upgraded Blackmarket slots to {}.'.format(current_slots + 1))
            else:
                self.bot.log('Not enough {} to open blackmarket slots to {}'.format(type_, current_slots + 1))
                return
            current_slots = self.bot.market_info['open_slots']

    def swapUnitsInExpBuilding(self, unit_id_in, unit_id_out):
        unit_list = self.bot.unit_list
        unit_1_id, unit_1_island = unit_id_in, unit_list[unit_id_in]['island_id']
        unit_1_posx, unit_1_posy = unit_list[unit_id_in]['pos_x'], unit_list[unit_id_in]['pos_y']
        unit_in_dict = {'unit_id': unit_1_id, 'island_id': unit_1_island, 'pos_x': unit_1_posx, 'pos_y': unit_1_posy}
        unit_2_id, unit_2_island = unit_id_out, unit_list[unit_id_out]['island_id']
        unit_2_posx, unit_2_posy = unit_list[unit_id_out]['pos_x'], unit_list[unit_id_out]['pos_y']
        unit_out_dict = {'unit_id': unit_2_id, 'island_id': unit_2_island, 'pos_x': unit_2_posx, 'pos_y': unit_2_posy}
        self.bot.MoveUnitBuilding([unit_in_dict, unit_out_dict])

    def checkCoordinates(self, island_id, pos_x, pos_y):
        if (pos_x, pos_y) in self.bot.island_list[island_id]['base_coords'] \
                and self.bot.island_list[island_id]['occupied_coords'][(pos_x, pos_y)]['occ'] == 0:
            return pos_x, pos_y
        else:
            distance = [abs(coord[0] - pos_x) + abs(coord[1] - pos_y) for coord in
                        self.bot.island_list[island_id]['base_coords'] if
                        self.bot.island_list[island_id]['occupied_coords'][(coord[0], coord[1])] == 0]
            pos_x, pos_y = self.bot.island_list[island_id]['base_coords'][distance.index(min(distance))]
            return pos_x, pos_y

    def buyWeeklyGuildRainbowmon(self):
        self.bot.log(self.bot.shop_interval_list)
        self.bot.log(self.bot.shop_item_list)
        try:
            if self.bot.shop_interval_list[1200005]['remained_time'] <= 0:
                if self.getMonsterSpaceLeft() > 0:
                    try:
                        if self.bot.shop_item_list[1200005]['enable'] == 1:
                            if self.bot.shop_interval_list[1200005]['remained_time'] <= 0:
                                if self.bot.wizard_info['guild_point'] >= \
                                        self.bot.shop_item_list[1200005]['buy_cost'][0]:
                                    pos_x = self.bot.buildings[2]['pos_x'] + random.randint(-5, 5)
                                    pos_y = self.bot.buildings[2]['pos_y'] + random.randint(-5, 5)
                                    pos_array = self.checkCoordinates(self.bot.buildings[2]['island_id'], pos_x, pos_y)
                                    pos_x, pos_y = pos_array[0], pos_array[1]
                                    if self.bot.BuyShopItem(1200005, self.bot.buildings[2]['island_id'], pos_x, pos_y):
                                        self.weekly_angelmon_bought = True
                                else:
                                    self.bot.log('Not enough guild points ({}) to buy weekly rainbowmon. '
                                                 '150 guild points needed.'.format(self.bot.wizard_info['guild_point']))
                            else:
                                self.bot.log(
                                    'Not able to buy weekly rainbowmon. {} '
                                    'seconds remeining unitl next possible buy.'.format(
                                        self.bot.shop_interval_list[1200005]['remained_time']))
                                self.weekly_angelmon_bought = True

                        else:
                            self.bot.log('Not able to buy weekly rainbowmon.')
                    except ValueError:
                        self.bot.log('Not allowed to buy weekly rainbowmon.')
                    except KeyError:
                        self.bot.log('Error buying weekly rainbowmon.')
                else:
                    put_in_storage = 1
                    unit_ids = []
                    for unit, info_ in self.bot.unit_list.items():
                        if put_in_storage > 0:
                            if info_['building_id'] == 0:
                                unit_ids.append(unit)
                                put_in_storage -= 1
                        else:
                            break
                    self.bot.log('Now attempting to move {} units to storage.'.format(len(unit_ids)))
                    if not self.moveUnitsToStorage(unit_ids):
                        self.bot.log('Not able to move units to storage. Buy aborted.')
                        return
                    self.buyWeeklyGuildRainbowmon()
            else:
                self.weekly_angelmon_bought = True
        except KeyError:
            return

    def buyWeeklyDevilmon(self):
        self.bot.log(self.bot.shop_interval_list)
        self.bot.log(self.bot.shop_item_list)
        try:
            if self.bot.shop_interval_list[901002]['remained_time'] <= 0:
                if self.getMonsterSpaceLeft() > 0:
                    try:
                        if self.bot.shop_interval_list[901002]['remained_time'] <= 0:
                            self.bot.log('{}'.format(self.bot.shop_interval_list[901002]['remained_time']))
                            if self.bot.wizard_info['honor_point'] >= self.bot.shop_item_list[901002]['buy_cost'][0]:
                                pos_x = self.bot.buildings[2]['pos_x'] + random.randint(-5, 5)
                                pos_y = self.bot.buildings[2]['pos_y'] + random.randint(-5, 5)
                                pos_array = self.checkCoordinates(self.bot.buildings[2]['island_id'], pos_x, pos_y)
                                pos_x, pos_y = pos_array[0], pos_array[1]
                                self.bot.BuyShopItem(901002, self.bot.buildings[2]['island_id'],
                                                     pos_x,
                                                     pos_y)
                                self.weekly_devilmon_bought = True
                            else:
                                self.bot.log('Not enough honor points ({}) to buy weekly devilmon. '
                                             '180 honor points needed.'.format(self.bot.wizard_info['honor_point']))
                        else:
                            self.bot.log('Not able to buy weekly devilmon. {} seconds remeining until next '
                                         'possible buy.'.format(self.bot.shop_interval_list[901002]['remained_time']))
                            self.weekly_devilmon_bought = True
                    except KeyError:
                        self.bot.log('Error buying weekly devilmon.')
                else:
                    put_in_storage = 1
                    unit_ids = []
                    for unit, info_ in self.bot.unit_list.items():
                        if put_in_storage > 0:
                            if info_['building_id'] == 0:
                                unit_ids.append(unit)
                                put_in_storage -= 1
                        else:
                            break
                    self.bot.log('Now attempting to move {} units to storage.'.format(len(unit_ids)))
                    if not self.moveUnitsToStorage(unit_ids):
                        self.bot.log('Not able to move units to storage. Buy aborted.')
                        return
                    self.buyWeeklyDevilmon()
            else:
                self.weekly_devilmon_bought = True
        except KeyError:
            return

    def buyPremiumPack(self):
        if self.bot.wizard_info['wizard_crystal'] >= self.bot.shop_item_list[1100155]['buy_cost'][0]:
            self.bot.BuyShopItem(1100155, 0, 0, 0)
        else:
            self.bot.log('Not enough crystals ({}) to buy item. '
                         '750 crystals needed.'.format(self.bot.wizard_info['wizard_crystal']))

    def levelUnitsInBuildings(self):
        building_ids = []
        try:
            building_ids.append(self.bot.buildings[22]['building_id'])
        except KeyError:
            pass
        try:
            building_ids.append(self.bot.buildings[23]['building_id'])
        except KeyError:
            pass
        # self.bot.log('{}'.format(building_ids))
        if building_ids:
            for unit, info_ in self.bot.unit_list.items():
                if info_['building_id'] in building_ids:
                    if info_['unit_level'] < max_class_level_map[info_['class']]:
                        if info_['exp_gained'] >= experience_level_up_map[info_['class']][info_['unit_level']]:
                            if self.bot.UpdateUnitExpGained([{'unit_id': unit}]):
                                self.bot.log('Successfully leveled up unit {} in exp building.'.format(unit))
                            else:
                                self.bot.log('Error leveling up unit {} in exp building.'.format(unit))
                    else:
                        self.bot.log('Unit {} already on max level {} for its class {}.'.format(
                            unit, info_['unit_level'], info_['class']))
                        id_out = unit
                        id_in = 0
                        for unit_in, info_in in self.bot.unit_list.items():
                            if info_in['building_id'] == 0:
                                if info_in['unit_level'] < max_class_level_map[info_in['class']]:
                                    if info_in['unit_master_id'] not in [15105, 14314]:
                                        id_in = unit_in
                        if id_in:
                            self.bot.log('Swapping unit {} in exp building to unit {}'.format(id_out, id_in))
                            self.swapUnitsInExpBuilding(id_in, id_out)
                        else:
                            self.bot.log('No suitabel unit found to swap into exp building.')
        else:
            self.bot.log('No exp buildings found.')

    def refreshShop(self, crystal_refresh=False):
        # check if shop refresh possible
        if not crystal_refresh:
            self.bot.GetBlackMarketList(False)
            self.last_shop_refresh = math.ceil(time.time()) - (3600 - self.bot.market_info['update_remained'])
            for i, item in enumerate(self.bot.market_list):
                if item['item_master_type'] == 1:
                    monster = get_monster_name_by_id(item['item_master_id'])
                    element = element_map[int(str(item['item_master_id'])[-1])]
                    self.bot.log('{}: Monster - {} {} {}'.format(i + 1, monster, element, item['item_master_id']))
                elif item['item_master_type'] == 9:
                    self.bot.log('{}: Scroll - {}, amount: {}'.format(i + 1, summon_source_map[item['item_master_id']],
                                                                      item['amount']))
                elif item['item_master_type'] == 8:
                    self.bot.log('{}: Rune - {}'.format(i + 1, Bot.parseRune(item['runes'][0])))
                else:
                    self.bot.log('{}: Unknown shop item type {}'.format(i + 1, item['item_master_type']))
        elif crystal_refresh:
            self.bot.log('Shop successfully refreshed using crystals.')
            self.bot.GetBlackMarketList(crystal_refresh)
            self.last_shop_refresh = math.ceil(time.time())
            i = 0
            for item in self.bot.market_list:
                if item['item_master_type'] == 1:
                    self.bot.log('{}: Monster {}'.format(i, item['item_master_id']))
                    i += 1
                elif item['item_master_type'] == 9:
                    self.bot.log('{}: Scroll {}, amount: {}'.format(i, summon_source_map[item['item_master_id']],
                                                                    item['amount']))
                    i += 1
                elif item['item_master_type'] == 8:
                    self.bot.log('{}: Rune {}'.format(i, Bot.parseRune(item['runes'][0])))
                    i += 1
                else:
                    self.bot.log('{}: Unknown shop item type {}'.format(i, item['item_master_type']))
                    i += 1

    def buyShopItems(self, item_list_=None):
        if item_list_ and self.bot.market_list:
            for item in self.bot.market_list:
                if item['item_master_type'] in item_list_:
                    if item['item_master_type'] == 8:
                        if self.checkRuneFilter(item['runes'][0]):
                            if self.bot.wizard_info['wizard_mana'] >= item['buy_mana'] and item['available']:
                                self.bot.log('Bought rune {} for {} mana.'.format(Bot.parseRune(item['runes'][0]),
                                                                                  item['buy_mana']))
                                self.bot.BuyBlackMarketItem(item['item_no'], item['item_master_type'],
                                                            item['item_master_id'], item['amount'])
                            else:
                                self.bot.log('Not enough mana to buy rune:')
                        else:
                            self.bot.log('Rune not matching given filters.')
                    else:
                        if self.bot.wizard_info['wizard_mana'] >= item['buy_mana'] and item['available'] and \
                                item['item_master_id'] in self.scroll_types:
                            self.bot.log('Bought item {} for {} mana.'.format(summon_source_map[item['item_master_id']],
                                                                              item['buy_mana']))
                            self.bot.BuyBlackMarketItem(item['item_no'], item['item_master_type'],
                                                        item['item_master_id'], item['amount'])
                        elif self.bot.wizard_info['wizard_mana'] < item['buy_mana'] and item['available']:
                            self.bot.log('Not enough mana to buy '
                                         'item {}.'.format(summon_source_map[item['item_master_id']]))
                        else:
                            self.bot.log('Not the right scroll item to buy: '
                                         '{}'.format(summon_source_map[item['item_master_id']]))

    def saveShopItemList(self, item_list_):
        if item_list_:
            self.current_shop_items = item_list_

    def checkRuneFilter(self, rune_data):
        rune = self.parseRune(rune_data)
        if rune:
            # Keep runes of quality rare and up, subject to configuration
            if rune['Quality'] > 2:
                # Keep runes with 4 stars and above, subject to configuration
                if rune['Stars'] >= 4:
                    if rune['Slot'] == 1:
                        is_percentage = 0
                        is_flat = 0
                        for substat_element in rune['Substats']:
                            if substat_element[0] < 6 and substat_element[0] % 2 == 1:
                                is_flat += 1
                            else:
                                is_percentage += 1
                    elif rune['Slot'] == 2:
                        # check for flat main stats
                        if rune['Main Stat'] < 6 and rune['Main Stat'] % 2 == 1:
                            return False
                        else:
                            return True
                    elif rune['Slot'] == 3:
                        is_percentage = 0
                        is_flat = 0
                        for substat_element in rune['Substats']:
                            if substat_element[0] < 6 and substat_element[0] % 2 == 1:
                                is_flat += 1
                            else:
                                is_percentage += 1
                    elif rune['Slot'] == 4:
                        # check for flat main stats + crit rate
                        if (rune['Main Stat'] < 6 and rune['Main Stat'] % 2 == 1) or rune['Main Stat'] == 9:
                            return False
                        else:
                            return True
                    elif rune['Slot'] == 5:
                        is_percentage = 0
                        is_flat = 0
                        for substat_element in rune['Substats']:
                            if substat_element[0] < 6 and substat_element[0] % 2 == 1:
                                is_flat += 1
                            else:
                                is_percentage += 1
                    elif rune['Slot'] == 6:
                        # check for flat main stats + acc and res
                        if (rune['Main Stat'] < 6 and rune['Main Stat'] % 2 == 1) or rune['Main Stat'] > 10:
                            return False
                        else:
                            return True
                else:
                    return False
            else:
                return False
        else:
            return None

    @staticmethod
    def parseRune(rune_data):
        if rune_data:
            type_ = rune_data.get('set_id')
            slot = rune_data.get('slot_no')
            stars = rune_data.get('class')
            quality = rune_data.get('rank')

            main_stat_old = rune_data.get('pri_eff')
            mainstat_arr = []
            main_stat = 0
            main_stat_value = 0
            if main_stat_old:
                main_stat = int(main_stat_old[0])
                main_stat_value = int(main_stat_old[1])
                mainstat_arr.append(main_stat)
                mainstat_arr.append(main_stat_value)

            innate_stat_old = rune_data.get('prefix_eff')
            innatestat_arr = []
            innatestat_dic = {}
            if innate_stat_old:
                innate_stat = int(innate_stat_old[0])
                innate_stat_value = int(innate_stat_old[1])
                innatestat_arr.append(innate_stat_old)
                innatestat_arr.append(innate_stat_value)
                innatestat_dic.update({'Innate Stat': innate_stat, 'Innate Stat value': innate_stat_value})

            substats = rune_data.get('sec_eff', [])
            substat_arr = []
            substat_dic = {}
            if len(substats) >= 1:
                substat_1 = int(substats[0][0])
                substat_1_value = int(substats[0][1])
                substat_arr.append([substat_1, substat_1_value])
                substat_dic.update({'Substat 1': substat_1, 'Substat 1 value': substat_1_value})

            if len(substats) >= 2:
                substat_2 = int(substats[1][0])
                substat_2_value = int(substats[1][1])
                substat_arr.append([substat_2, substat_2_value])
                substat_dic.update({'Substat 2': substat_2, 'Substat 2 value': substat_2_value})

            if len(substats) >= 3:
                substat_3 = int(substats[2][0])
                substat_3_value = int(substats[2][1])
                substat_arr.append([substat_3, substat_3_value])
                substat_dic.update({'Substat 3': substat_3, 'Substat 3 value': substat_3_value})

            if len(substats) >= 4:
                substat_4 = int(substats[3][0])
                substat_4_value = int(substats[3][1])
                substat_arr.append([substat_4, substat_4_value])
                substat_dic.update({'Substat 4': substat_4, 'Substat 4 value': substat_4_value})
            substat_dic2 = {'Substats': substat_arr}

            rune = {'Type': type_, 'Slot': slot, 'Stars': stars, 'Quality': quality,
                    'Main Stat': main_stat, 'Main Stat value': main_stat_value}
            rune.update(innatestat_dic)
            # rune.update(substat_dic)
            rune.update(substat_dic2)

            return rune
        else:
            return None

    def upgradeRuneTo(self, rune_id, upgrade_curr, upgrade=15):
        upgrade = max(upgrade, 15)
        self.bot.log('Upgrading rune {} to level {}'.format(rune_id, upgrade))
        while upgrade_curr < upgrade:
            old = upgrade_curr
            new_rune_data = self.bot.UpgradeRune(rune_id, upgrade_curr)
            upgrade_curr = new_rune_data['rune']['upgrade_curr']
            if new_rune_data['ret_code'] == 0:
                if old >= upgrade_curr:
                    self.bot.log('Upgrade failed, rune {} still at level {}'.format(rune_id, upgrade_curr))
                else:
                    self.bot.log('Upgrade successful, rune {} now at level {}'.format(rune_id, upgrade_curr))
                time.sleep(random.uniform(1, 2.5))
            else:
                self.bot.log('Error while upgrading rune {}. '
                             'Maybe not enough mana. Rune at level {}.'.format(rune_id, upgrade_curr))
                break

    def doDailyWish(self):
        wish_outcome = self.bot.DoRandomWishItem()['wish_info']
        self.bot.log('Wish granted {} with amount of {}'.format(inventory_type_map[wish_outcome['item_master_type']],
                                                                wish_outcome['amount']))

    def collectAllMail(self):
        # collects all mails, but not social points
        # items_to_collect = []
        for mail_item, info_ in self.bot.mailList.items():
            if info_['sender_type'] != 1:
                # items_to_collect.append(mail_item['mail_id'])
                self.bot.ReceiveMail([{'mail_id': mail_item}])
                time.sleep(random.uniform(0.5, 1.5))

    def collectAllSocialPoints(self):
        collecible_points = self.bot.wizard_info['social_point_max'] - self.bot.wizard_info['social_point_current']
        collectible_points_list = []
        collected_points = 0
        if collecible_points > 0:
            for mail_item, info_ in self.bot.mailList.items():
                if collected_points < collecible_points:
                    if info_['sender_type'] == 1:
                        collectible_points_list.append({'mail_id': mail_item})
                        collected_points += 10
                else:
                    break
            if collectible_points_list:
                self.bot.ReceiveMail(collectible_points_list)
                self.bot.log('Collected all social points. Current social points {}'.format(
                    self.bot.wizard_info['social_point_current']))
                return
            else:
                self.bot.log('No social points found in mail list. Returning to other activities.')
                return
        else:
            self.bot.log('Not able to collect any more social points. Current social points: {}'.format(
                self.bot.wizard_info['social_point_current']))

    def checkMailForCollectibles(self):
        collectibles = 0
        self.bot.log('Mail list: {}'.format(self.bot.mailList))
        for mail_item, info_ in self.bot.mailList.items():
            if info_['sender_type'] != 1:
                collectibles += 1
        self.bot.log('Rewards to collect: {}'.format(collectibles))
        return collectibles

    def checkMailForSocialPoints(self):
        for mail_item, info_ in self.bot.mailList.items():
            if info_['sender_type'] == 1:
                return True

    def doDailyQuests(self):
        """
        Do the daily quests.
        1. Use 20 energy
        2. Power up 3 monsters
        3. Summon 3 monsters
        4. Power up runes 3 times
        5. Use rep monster of friend 3 times
        6. Fight arena 3 times
        7. Complete Giants dungeon 1 time
        8. Complete Hall of Magic 1 time
        9. Send social points 5 times
        (10.) Complete daily Elemental dungeon 1 time
        Collect rewards afterwards

        Combine energy use with giant and hall of magic + essence
        Combine hall of magic + essence with using rep

        :return:
        """

        helper_used = 0
        # do giants dungeon
        if not self.bot.daily_quest_list[9]['completed'] == 1:
            clear_time = random.randint(60, 120)
            helper = self.getNextBestRep()
            self.bot.doDungeon(8001, 1, clear_time, units=None, helper_list=helper, win_lose=1)
            helper_used += 1
            if self.bot.daily_quest_list[9]['completed'] == 1:
                self.bot.log('Successfully finished giants dungeon quest. Now collecting reward.')
                self.collectDailyRewards()
        elif not self.bot.daily_quest_list[9]['rewarded'] == 1:
            self.bot.log('Daily giants dungeon quest already finished, but not collected yet. Collecting reward now.')
            self.collectDailyRewards()
        else:
            self.bot.log('Daily giants dungeon quest already finished and collected.')

        if 1001 in [dungeon['dungeon_id'] for dungeon in self.bot.dungeon_list] \
                and 10 in list(self.bot.daily_quest_list.keys()):
            # do monday elemental dungeon
            if not self.bot.daily_quest_list[10]['completed'] == 1:
                clear_time = random.randint(60, 120)
                helper = self.getNextBestRep()
                self.bot.doDungeon(1001, 1, clear_time, units=None, helper_list=helper, win_lose=1)
                helper_used += 1
                if self.bot.daily_quest_list[10]['completed'] == 1:
                    self.bot.log('Successfully finished monday elemental dungeon quest. Now collecting reward.')
                    self.collectDailyRewards()
            elif not self.bot.daily_quest_list[10]['rewarded'] == 1:
                self.bot.log('Monday elemental dungeon quest already finished, but not collected yet. '
                             'Collecting reward now.')
                self.collectDailyRewards()
            else:
                self.bot.log('Monday elemental dungeon quest already finished and collected.')

        if 2001 in [dungeon['dungeon_id'] for dungeon in self.bot.dungeon_list] \
                and 11 in list(self.bot.daily_quest_list.keys()):
            # do tuesday elemental dungeon
            if not self.bot.daily_quest_list[11]['completed'] == 1:
                clear_time = random.randint(60, 120)
                helper = self.getNextBestRep()
                self.bot.doDungeon(2001, 1, clear_time, units=None, helper_list=helper, win_lose=1)
                helper_used += 1
                if self.bot.daily_quest_list[11]['completed'] == 1:
                    self.bot.log('Successfully finished tuesday elemental dungeon quest. Now collecting reward.')
                    self.collectDailyRewards()
            elif not self.bot.daily_quest_list[11]['rewarded'] == 1:
                self.bot.log('Tuesday elemental dungeon quest already finished, but not collected yet. '
                             'Collecting reward now.')
                self.collectDailyRewards()
            else:
                self.bot.log('Tuesday elemental dungeon quest already finished and collected.')

        if 3001 in [dungeon['dungeon_id'] for dungeon in self.bot.dungeon_list] \
                and 12 in list(self.bot.daily_quest_list.keys()):
            # do wednesday elemental dungeon
            if not self.bot.daily_quest_list[12]['completed'] == 1:
                clear_time = random.randint(60, 120)
                helper = self.getNextBestRep()
                self.bot.doDungeon(3001, 1, clear_time, units=None, helper_list=helper, win_lose=1)
                helper_used += 1
                if self.bot.daily_quest_list[12]['completed'] == 1:
                    self.bot.log('Successfully finished wednesday elemental dungeon quest. Now collecting reward.')
                    self.collectDailyRewards()
            elif not self.bot.daily_quest_list[12]['rewarded'] == 1:
                self.bot.log('Wednesday elemental dungeon quest already finished, but not collected yet. '
                             'Collecting reward now.')
                self.collectDailyRewards()
            else:
                self.bot.log('Wednesday elemental dungeon quest already finished and collected.')

        if 4001 in [dungeon['dungeon_id'] for dungeon in self.bot.dungeon_list] \
                and 13 in list(self.bot.daily_quest_list.keys()):
            # do thursday elemental dungeon
            if not self.bot.daily_quest_list[13]['completed'] == 1:
                clear_time = random.randint(60, 120)
                helper = self.getNextBestRep()
                self.bot.doDungeon(4001, 1, clear_time, units=None, helper_list=helper, win_lose=1)
                helper_used += 1
                if self.bot.daily_quest_list[13]['completed'] == 1:
                    self.bot.log('Successfully finished thursday elemental dungeon quest. Now collecting reward.')
                    self.collectDailyRewards()
            elif not self.bot.daily_quest_list[13]['rewarded'] == 1:
                self.bot.log('Thursday elemental dungeon quest already finished, but not collected yet. '
                             'Collecting reward now.')
                self.collectDailyRewards()
            else:
                self.bot.log('Thursday elemental dungeon quest already finished and collected.')

        if 7001 in [dungeon['dungeon_id'] for dungeon in self.bot.dungeon_list] \
                and 15 in list(self.bot.daily_quest_list.keys()):
            # do sunday elemental dungeon
            if not self.bot.daily_quest_list[15]['completed'] == 1:
                clear_time = random.randint(60, 120)
                helper = self.getNextBestRep()
                self.bot.doDungeon(7001, 1, clear_time, units=None, helper_list=helper, win_lose=1)
                helper_used += 1
                if self.bot.daily_quest_list[15]['completed'] == 1:
                    self.bot.log('Successfully finished sunday elemental dungeon quest. Now collecting reward.')
                    self.collectDailyRewards()
            elif not self.bot.daily_quest_list[15]['rewarded'] == 1:
                self.bot.log('Sunday elemental dungeon quest already finished, but not collected yet. '
                             'Collecting reward now.')
                self.collectDailyRewards()
            else:
                self.bot.log('Sunday elemental dungeon quest already finished and collected.')

        if 5001 in [dungeon['dungeon_id'] for dungeon in self.bot.dungeon_list] \
                and 14 in list(self.bot.daily_quest_list.keys()):
            # do magic dungeon
            if not self.bot.daily_quest_list[14]['completed'] == 1:
                while helper_used < 3:
                    clear_time = random.randint(60, 120)
                    helper = self.getNextBestRep()
                    self.bot.doDungeon(5001, 1, clear_time, units=None, helper_list=helper, win_lose=1)
                    helper_used += 1
                if self.bot.daily_quest_list[14]['completed'] == 1:
                    self.bot.log('Successfully finished magic dungeon quest. Now collecting reward.')
                    self.collectDailyRewards()
            elif not self.bot.daily_quest_list[14]['rewarded'] == 1:
                self.bot.log('Magic dungeon quest already finished, but not collected yet. Collecting reward now.')
                self.collectDailyRewards()
            else:
                self.bot.log('Magic dungeon quest already finished and collected.')

        # do energy quest
        if not self.bot.daily_quest_list[1]['completed'] == 1:
            while not self.bot.daily_quest_list[1]['completed'] == 1:
                clear_time = random.randint(30, 90)
                self.bot.do_scenario(3, 7, 1, clear_time, units=None, helper_list=None, win_lose=1)
            if self.bot.daily_quest_list[1]['completed'] == 1:
                self.bot.log('Successfully finished energy quest. Now collecting reward.')
                self.collectDailyRewards()
        elif not self.bot.daily_quest_list[1]['rewarded'] == 1:
            self.bot.log('Daily energy quest already finished, but not collected yet. Collecting reward now.')
            self.collectDailyRewards()
        else:
            self.bot.log('Daily energy quest already finished and collected.')

        # do rune quest
        if not self.bot.daily_quest_list[4]['completed'] == 1:
            while not self.bot.daily_quest_list[4]['completed'] == 1:
                rune_to_upgrade = None
                upgrade_curr = None
                for rune, info_ in self.bot.rune_list.items():
                    if info_['upgrade_curr'] < 6:
                        rune_to_upgrade = rune
                        upgrade_curr = info_['upgrade_curr']
                        self.bot.log('Found rune to upgrade {} with current upgrade {}'.format(rune_to_upgrade,
                                                                                               upgrade_curr))
                        break
                if rune_to_upgrade:
                    self.bot.UpgradeRune(rune_to_upgrade, upgrade_curr)
                    time.sleep(2)
                else:
                    break
            if self.bot.daily_quest_list[4]['completed'] == 1:
                self.bot.log('Successfully finished rune quest. Now collecting reward.')
                self.collectDailyRewards()
        elif not self.bot.daily_quest_list[4]['rewarded'] == 1:
            self.bot.log('Daily rune quest already finished, but not collected yet. Collecting reward now.')
            self.collectDailyRewards()
        else:
            self.bot.log('Daily rune quest already finished and collected.')

        # do sacrifice/upgrade quest
        if not self.bot.daily_quest_list[2]['completed'] == 1:
            while not self.bot.daily_quest_list[2]['completed'] == 1:
                unit_to_upgrade = None
                island_id = None
                building_id = None
                pos_x = None
                pos_y = None
                unit_to_use = None
                for unit, info_ in self.bot.unit_list.items():
                    if info_['building_id'] == 0 and info_['unit_master_id'] not in [15105, 14314]:
                        if info_['class'] >= 3 and info_['unit_level'] < max_class_level_map[info_['class']]:
                            unit_to_upgrade = unit
                            island_id = info_['island_id']
                            building_id = info_['building_id']
                            pos_x = info_['pos_x']
                            pos_y = info_['pos_y']
                            break
                for unit, info_ in self.bot.unit_list.items():
                    if info_['building_id'] == 0:
                        if info_['class'] < 2 and info_['unit_master_id'] not in \
                                [15105, 14314, 142, 14211, 14212, 14213, 14214, 14215, 182, 18211, 18212, 18213,
                                 18214, 18215]:
                            unit_to_use = unit
                            break
                if unit_to_upgrade and unit_to_use:
                    self.bot.SacrificeUnit(target_id=unit_to_upgrade, source_list=[{'source_id': unit_to_use}],
                                           island_id=island_id, building_id=building_id, pos_x=pos_x, pos_y=pos_y)
                    time.sleep(3)
                else:
                    break
            if self.bot.daily_quest_list[2]['completed'] == 1:
                self.bot.log('Successfully finished upgrading quest. Now collecting reward.')
                self.collectDailyRewards()
        elif not self.bot.daily_quest_list[2]['rewarded'] == 1:
            self.bot.log('Daily upgrading quest already finished, but not collected yet. Collecting reward now.')
            self.collectDailyRewards()
        else:
            self.bot.log('Daily upgrading quest already finished and collected.')

        # do helper quest
        if not self.bot.daily_quest_list[7]['completed'] == 1:
            unit_id_list = []
            for unit in self.bot.defense_unit_list[:-1]:
                unit_id_list.append({'unit_id': unit['unit_id']})
            while not self.bot.daily_quest_list[7]['completed'] == 1:
                clear_time = random.randint(30, 90)
                helper = self.getNextBestRep()
                if helper:
                    self.bot.do_scenario(3, 7, 1, clear_time, units=unit_id_list, helper_list=helper, win_lose=1)
                else:
                    break
            if self.bot.daily_quest_list[7]['completed'] == 1:
                self.bot.log('Successfully finished helper quest. Now collecting reward.')
                self.collectDailyRewards()
        elif not self.bot.daily_quest_list[7]['rewarded'] == 1:
            self.bot.log('Daily helper quest already finished, but not collected yet. Collecting reward now.')
            self.collectDailyRewards()
        else:
            self.bot.log('Daily helper quest already finished and collected.')

        # Summon 3 monsters with social points if not yet completed
        if not self.bot.daily_quest_list[3]['completed'] == 1:
            summon_progress = self.bot.daily_quest_list[3]['progressed']
            summon_mode = 5
            if summon_progress > 0:
                self.bot.log('Continuing daily summoning quest. Already {} summons done.'.format(summon_progress))
            else:
                self.bot.log('Starting daily summoning quest.')
            summon_end = 3
            while summon_progress < summon_end:
                if self.getMonsterSpaceLeft() > 0:
                    summon_result = self.summonMonster(summon_mode)
                    if summon_result == 0:
                        summon_progress += 1
                    elif summon_result == 1:
                        self.bot.log('Not enough social points to summon more.')
                        if summon_mode == 5:
                            self.bot.log('Now switching to summoning Unknown Scrolls.')
                            summon_mode = 1
                        else:
                            self.bot.log('Not enough social points or Unknown Scrolls. Stopping the summoning quest.')
                            break
                else:
                    self.bot.log('Couldn\'t finish quest of summoning 3 Monsters. Did only {} summons, '
                                 'now trying to put monsters in storage.'.format(summon_progress))
                    put_in_storage = self.getMonsterSpaceLeft() + summon_end - summon_progress
                    unit_ids = []
                    for unit, info_ in self.bot.unit_list.items():
                        if put_in_storage > 0:
                            if info_['building_id'] == 0:
                                unit_ids.append(unit)
                                put_in_storage -= 1
                        else:
                            break
                    self.bot.log('Now attempting to move {} units to storage.'.format(len(unit_ids)))
                    if not self.moveUnitsToStorage(unit_ids):
                        self.bot.log('Not able to make space for all daily summons. '
                                     'Stopping for now after {} summons.'.format(summon_progress))
                        break
            if summon_progress == summon_end and self.bot.daily_quest_list[3]['completed'] == 1:
                self.bot.log('Successfully finished summoning quest. Now collecting reward.')
                self.collectDailyRewards()
        elif not self.bot.daily_quest_list[3]['rewarded'] == 1:
            self.bot.log('Daily summoning quest already finished, but not collected yet. Collecting reward now.')
            self.collectDailyRewards()
        else:
            self.bot.log('Daily summoning quest already finished and collected.')

        # send social points
        if not self.bot.daily_quest_list[6]['completed'] == 1 and len(self.bot.friend_list) >= 5:
            sending_progress = self.bot.daily_quest_list[6]['progressed']
            if sending_progress > 0:
                self.bot.log('Continuing sending social points quest. Already {} times sent.'.format(sending_progress))
            else:
                self.bot.log('Starting sending social points quest.')
            sent = self.sendSocialPoints() + sending_progress
            if sent >= 5:
                if self.bot.daily_quest_list[6]['completed'] == 1:
                    self.bot.log('Successfully finished sending social points quest. Now collecting reward.')
                    self.collectDailyRewards()
            else:
                self.bot.log('Can\'t send enough social points. '
                             'Could only send social points to {} players.'.format(sent))
                while sent < 5:
                    self.bot.log('Doing one social summon.')
                    summon_response = self.summonMonster(5)
                    if summon_response == 0:
                        next_send = self.sendSocialPoints()
                        sent += next_send
                        self.bot.log('Sent social points to {} more friends.'.format(next_send))
                    elif summon_response == 1:
                        self.bot.log('Not enough social points to summon more.')
                        break
                    else:
                        unit_ids = []
                        put_in_storage = 1
                        for unit, info_ in self.bot.unit_list.items():
                            if put_in_storage > 0:
                                if info_['building_id'] == 0:
                                    unit_ids.append(unit)
                                    put_in_storage -= 1
                            else:
                                break
                        self.bot.log('Now attempting to move {} units to storage.'.format(len(unit_ids)))
                        if not self.moveUnitsToStorage(unit_ids):
                            self.bot.log('Not able to make space for social summon. '
                                         'Sent social points to {} friends in total'.format(sent))
                            break
                if sent >= 5 and self.bot.daily_quest_list[6]['completed'] == 1:
                    self.bot.log('Successfully finished sending social points quest. Now collecting reward.')
                    self.collectDailyRewards()
        elif len(self.bot.friend_list) < 5:
            self.bot.log('Not able to finish sending social points quest. '
                         'Only {} summoners on friend list.'.format(len(self.bot.friend_list)))
            self.bot.log('Now sending social points to summoners on friend list.')
            self.sendSocialPoints()
        elif not self.bot.daily_quest_list[6]['rewarded'] == 1:
            self.bot.log('Sending social points quest already finished, but not collected yet. Collecting reward now.')
            self.collectDailyRewards()
        else:
            self.bot.log('Sending social points quest already finished and collected.')

        # do Arena Fights, just maybe fight all
        if not self.bot.daily_quest_list[8]['completed'] == 1:
            self.ArenaFighter(units=None)
            if self.bot.daily_quest_list[8]['completed'] == 1 and not self.bot.daily_quest_list[8]['rewarded'] == 1:
                self.bot.log('Successfully finished arena quest. Now collecting reward.')
                self.collectDailyRewards()
        elif not self.bot.daily_quest_list[8]['rewarded'] == 1:
            self.bot.log('Daily arena quest already finished, but not collected yet. Collecting reward now.')
            self.collectDailyRewards()
        else:
            self.bot.log('Daily arena quest already finished and collected.')

    def moveUnitsToStorage(self, unit_ids):
        space_in_storage_left = self.bot.wizard_info['unit_slots']['number'] + \
                                self.bot.unit_depository_slots['number'] - len(self.bot.unit_list) - \
                                self.getMonsterSpaceLeft()
        if space_in_storage_left > 0:
            move_list = []
            for unit_id in unit_ids:
                if space_in_storage_left > 0:
                    pos_x = min(max(self.bot.buildings[25]['pos_x'] + random.randint(-5, 5), 0), 21)
                    pos_y = min(max(self.bot.buildings[25]['pos_y'] + random.randint(-5, 5), 0), 21)
                    move_list.append(OrderedDict([('unit_id', unit_id),
                                                  ('island_id', self.bot.buildings[25]['island_id']),
                                                  ('building_id', self.bot.buildings[25]['building_id']),
                                                  ('pos_x', pos_x),
                                                  ('pos_y', pos_y)]))
                    space_in_storage_left -= 1
                else:
                    self.bot.log('Running out of space to move all {} into storage. '
                                 'Attempting to move a part at leas.'.format(len(unit_ids)))
                    break
            for _ in move_list:
                if type(_) != str:
                    _ = json.dumps(_).replace(' ', '')
            self.bot.MoveUnitBuilding(move_list)
            self.bot.log('Moved {} units to storage.'.format(len(move_list)))
            return True
        else:
            self.bot.log('Not enough space in monster storage to store monster(s) {}.'.format(unit_ids))
            return False

    def expandStorage(self, cash_used=0):
        try:
            if cash_used:
                pass
            else:
                if self.bot.wizard_info['wizard_mana'] > self.bot.unit_depository_slots['upgrade']['mana']:
                    self.bot.ExpandUnitDepositorySlot(cash_used)
        except KeyError:
            pass

    def finishScenario(self, difficulty):
        scenarios = map(dict, self.bot.scenario_list)
        scenarios_to_go = {}
        with open('achievements.json', 'r', encoding='utf-8') as ach:
            achievements = json.load(ach)
        for scenario in scenarios:
            # print(scenario)
            if scenario['cleared'] == 1 and scenario['difficulty'] == difficulty:
                region_key = scenario_id_map[scenario['region_id']][difficulty]
                for ach in achievements:
                    quest_id = 0
                    if int(ach['required level']) > self.bot.wizard_info['wizard_level']:
                        break
                    for condition in ast.literal_eval(ach['conditions']):
                        if region_key == condition[1]:
                            quest_id = int(ach['quest id'])
                            break
                    if quest_id > 0:
                        if quest_id not in self.bot.quest_rewarded:
                            if not self.bot.quest_active[quest_id]['is_completed']:
                                for condition_ in self.bot.quest_active[quest_id]['conditions']:
                                    self.bot.UpdateAchievement([{'ach_id': quest_id, 'cond_id': condition_[0], 'current': condition_[1]}])
                            self.bot.ClaimAchievementReward(quest_id)
                pass
            elif scenario['difficulty'] == difficulty:
                scenarios_to_go.update({scenario.pop('region_id'): scenario})
        print(scenarios_to_go)
        if not scenarios_to_go:
            max_scenario = [scenario['region_id'] for scenario in map(dict, self.bot.scenario_list)
                            if scenario['difficulty'] == difficulty]
            print(max_scenario)
            scenarios_not_started = range(max(max_scenario) + 1, 14) if max(max_scenario) != 13 else []
        else:
            scenarios_not_started = range(max(scenarios_to_go) + 1, 14) if max(scenarios_to_go) != 13 else []
        print(scenarios_to_go)
        print(scenarios_not_started)
        for scenario, info_ in scenarios_to_go.items():
            stage_no_cleared = max([stage['stage_no'] for stage in info_['stage_list'] if stage['cleared'] == 1])
            while stage_no_cleared < 7:
                stage_no_cleared += 1
                clear_time = random.randint(20, 40)
                if not self.bot.do_scenario(scenario, stage_no_cleared, difficulty, clear_time):
                    return False
                region_key = scenario_id_map[scenario][difficulty]
                for ach in achievements:
                    quest_id = 0
                    if int(ach['required level']) > self.bot.wizard_info['wizard_level']:
                        break
                    for condition in ast.literal_eval(ach['conditions']):
                        if region_key == condition[1]:
                            quest_id = int(ach['quest id'])
                            break
                    if quest_id > 0:
                        if quest_id not in self.bot.quest_rewarded:
                            if not self.bot.quest_active[quest_id]['is_completed']:
                                for condition_ in self.bot.quest_active[quest_id]['conditions']:
                                    self.bot.UpdateAchievement(
                                        [{'ach_id': quest_id, 'cond_id': condition_[0], 'current': condition_[2]+1}])

                time.sleep(5)
        for scenario in scenarios_not_started:
            for stage_no in range(1, 8):
                clear_time = random.randint(20, 40)
                if not self.bot.do_scenario(scenario, stage_no, difficulty, clear_time):
                    return False
                region_key = scenario_id_map[scenario][difficulty]
                for ach in achievements:
                    quest_id = 0
                    if int(ach['required level']) > self.bot.wizard_info['wizard_level']:
                        break
                    for condition in ast.literal_eval(ach['conditions']):
                        if region_key == condition[1]:
                            quest_id = int(ach['quest id'])
                            break
                    if quest_id > 0:
                        if quest_id not in self.bot.quest_rewarded:
                            if not self.bot.quest_active[quest_id]['is_completed']:
                                for condition_ in self.bot.quest_active[quest_id]['conditions']:
                                    self.bot.UpdateAchievement(
                                        [{'ach_id': quest_id, 'cond_id': condition_[0], 'current': condition_[2] + 1}])

                time.sleep(5)
		self.bot.level8()

    def moveUnitsFromStorage(self, unit_ids):
        space_left = self.getMonsterSpaceLeft()
        if space_left > 0:
            move_list = []
            for unit_id in unit_ids:
                if space_left > 0:
                    pos_x = min(max(self.bot.buildings[25]['pos_x'] + random.randint(-5, 5), 0), 21)
                    pos_y = min(max(self.bot.buildings[25]['pos_y'] + random.randint(-5, 5), 0), 21)
                    move_list.append(OrderedDict([('unit_id', unit_id),
                                                  ('island_id', self.bot.buildings[25]['island_id']),
                                                  ('building_id', 0),
                                                  ('pos_x', pos_x),
                                                  ('pos_y', pos_y)]))
                    space_left -= 1
                else:
                    self.bot.log('Running out of space to get all {} out of storage. '
                                 'Attempting to move a part at least.'.format(len(unit_ids)))
                    break
            if type(move_list) != str:
                move_list = json.dumps(move_list).replace(' ', '')
            self.bot.MoveUnitBuilding(move_list)
            self.bot.log('Moved {} units to inventory.'.format(len(move_list)))
            return True
        else:
            self.bot.log('Not enough space in inventory to take monster(s) {} out of storage.'.format(unit_ids))
        return False

    def use20Energy(self):
        self.bot.GetDungeonList()
        if 8001 in [dungeon['dungeon_id'] for dungeon in self.bot.dungeon_list]:
            self.completeGiant(stage_id=10, units=None)
        if 1001 in [dungeon['dungeon_id'] for dungeon in self.bot.dungeon_list]:
            self.completeElementalDungeon(1001, stage_id=10, units=None)
        elif 2001 in [dungeon['dungeon_id'] for dungeon in self.bot.dungeon_list]:
            self.completeElementalDungeon(2001, stage_id=10, units=None)
        elif 3001 in [dungeon['dungeon_id'] for dungeon in self.bot.dungeon_list]:
            self.completeElementalDungeon(3001, stage_id=10, units=None)
        elif 4001 in [dungeon['dungeon_id'] for dungeon in self.bot.dungeon_list]:
            self.completeElementalDungeon(4001, stage_id=10, units=None)
        elif 7001 in [dungeon['dungeon_id'] for dungeon in self.bot.dungeon_list]:
            self.completeElementalDungeon(7001, stage_id=10, units=None)
        if 5001 in [dungeon['dungeon_id'] for dungeon in self.bot.dungeon_list]:
            self.completeElementalDungeon(5001, stage_id=10, units=None)
        pass

    def powerUpMonster(self):
        pass

    def summonMonster(self, mode=5):
        if mode == 5:
            return self.doSocialSummon()
        elif mode == 1:
            return self.doUnknownSummon()
        elif mode == 3:
            return self.doMysticalSummon()
        return False

    def powerUpRune(self):
        pass

    def fightArena(self):
        pass

    def completeGiant(self, stage_id, units, helper_list=None):
        if not helper_list:
            helper_list = []
        self.bot.doDungeon(8001, stage_id, units, helper_list)

    def completeHallOfMagic(self, stage_id, units, helper_list=None):
        if not helper_list:
            helper_list = []
        self.bot.doDungeon(5001, stage_id, units, helper_list)

    def completeElementalDungeon(self, dungeon_id, stage_id, units, helper_list=None):
        if not helper_list:
            helper_list = []
        self.bot.doDungeon(dungeon_id, stage_id, units, helper_list)

    def getArenaRating(self):
        return self.bot.pvp_info['arena_score']

    def ArenaHandler(self):
        self.bot.GetArenaLog()
        if time.time() - self.last_arena_refresh > 120:
            self.last_arena_refresh = time.time()
            self.bot.GetArenaWizardList(refresh=1)
        else:
            self.bot.GetArenaWizardList()

        npc_list = []
        revenge_list = []
        arena_fight_list = []

        for npc, info_ in self.bot.npc_list.items():
            if info_['next_battle'] <= 0:
                npc_list.append(npc)

        for wizard, info_ in self.bot.arena_log.items():
            if info_['STATUS'] == 0:
                opp_units = self.bot.GetArenaUnitList(wizard)['opp_unit_list']
                if info_['opp_arena_score'] <= self.getArenaRating() + 100 or len(opp_units) <= 2 \
                        or max([opp_unit['unit_info']['unit_level'] for opp_unit in opp_units]) <= 30:
                    revenge_list.append([wizard, info_['log_id']])

        for wizard, info_ in self.bot.arena_list.items():
            opp_units = self.bot.GetArenaUnitList(wizard)['opp_unit_list']
            if info_['arena_score'] <= self.getArenaRating() + 100 or len(opp_units) <= 2 \
                    or max([opp_unit['unit_info']['unit_level'] for opp_unit in opp_units]) <= 30:
                arena_fight_list.append(wizard)

        return npc_list, revenge_list, arena_fight_list

    def ArenaListNpc(self):
        self.bot.GetArenaWizardList()

        npc_list = []

        for npc, info_ in self.bot.npc_list.items():
            if info_['next_battle'] <= 0:
                npc_list.append(npc)

        return npc_list

    def ArenaFighterNpc(self, units=None):
        npc_list = self.ArenaListNpc()
        for npc in npc_list:
            if self.bot.wizard_info['arena_energy'] > 0:
                self.bot.log('Battling NPC in Arena: {}'.format(npc))
                self.bot.doArena(npc, units, win_lose=1, is_npc=True)
            else:
                self.bot.log('Not enough arena wings to do more battles.')
                return
        self.bot.log('No more NPCs ready to battle.')

    def ArenaFighter(self, units=None):
        npc_list, revenge_list, arena_list = self.ArenaHandler()

        for npc in npc_list:
            if self.bot.wizard_info['arena_energy'] > 0:
                self.bot.log('Battling NPC in Arena: {}'.format(npc))
                self.bot.doArena(npc, units, win_lose=1, is_npc=True)
            else:
                self.bot.log('Not enough arena wings to do more battles.')
                return

        self.bot.GetArenaLog()
        for revenge in revenge_list:
            if revenge[0] in [enemy for enemy in self.bot.arena_log]:
                if self.bot.wizard_info['arena_energy'] > 0:
                    if self.getArenaRating() > 1150:
                        self.bot.log('Battling revenge Summoner in Arena: {}'.format(revenge[0]))
                        self.bot.log('Attempt to lose because of high arena rating: {}'.format(self.getArenaRating()))
                        self.bot.doArena(revenge[0], units, win_lose=0, log_id=revenge[1])
                    else:
                        self.bot.log('Battling revenge Summoner in Arena: {}'.format(revenge[0]))
                        self.bot.doArena(revenge[0], units, win_lose=1, log_id=revenge[1])
                    self.bot.GetArenaLog()
                else:
                    self.bot.log('Not enough arena wings to do more battles.')
                    return
            else:
                pass

        for fight in arena_list:
            if self.bot.wizard_info['arena_energy'] > 0:
                if self.getArenaRating() > 1100:
                    self.bot.log('Battling Summoner in Arena: {}'.format(fight))
                    self.bot.log('Attempt to lose because of high arena rating: {}'.format(self.getArenaRating()))
                    self.bot.doArena(fight, units, win_lose=0)
                else:
                    self.bot.log('Battling Summoner in Arena: {}'.format(fight))
                    self.bot.doArena(fight, units, win_lose=1)
            else:
                self.bot.log('Not enough arena wings to do more battles.')
                return

    def sendSocialPoints(self):
        times_sent = 0
        for friend, info_ in self.bot.friend_list.items():
            if self.bot.wizard_info['social_point_current'] >= self.bot.wizard_info['social_point_max']:
                self.bot.log('Maximum social points reached. Stop sending social points for now.')
                break
            elif info_['next_gift_time'] <= 0:
                self.bot.SendDailyGift([{'wizard_id': friend}])
                times_sent += 1
                time.sleep(random.uniform(0.5, 2.5))
        return times_sent

    def collectDailyRewards(self):
        for daily_quest, info_ in self.bot.daily_quest_list.items():
            if info_['completed'] and not info_['rewarded']:
                self.bot.log('Collecting reward for quest {}.'.format(daily_quest))
                self.bot.RewardDailyQuest(daily_quest)

    def getRepList(self):
        reps = []
        if self.bot.helper_list:
            for friend, info_ in self.bot.helper_list.items():
                if int(info_['next_assist_time']) <= 0:
                    reps.append({'wizard_id': friend, 'unit_id': info_['rep_unit_id'],
                                 'arena_score': info_['arena_score'], 'wizard_level': info_['wizard_level']})
            return reps
        else:
            return reps

    def getNextBestRep(self):
        self.bot.log('{}'.format(self.bot.helper_list))
        rep_list = self.getRepList()
        self.bot.log('{}'.format(rep_list))
        if rep_list:
            try:
                max_arena_score_index = find(rep_list, 'arena_score',
                                             max([friend['arena_score'] for friend in rep_list if
                                                  friend['wizard_level'] > 15]))
            except ValueError:
                max_arena_score_index = find(rep_list, 'arena_score',
                                             max([friend['arena_score'] for friend in rep_list]))
            ret = [{'wizard_id': rep_list[max_arena_score_index]['wizard_id'],
                    'unit_id': rep_list[max_arena_score_index]['unit_id']}]
            self.bot.log('{}'.format(ret))
            return ret
        else:
            return []

    def doSocialSummon(self):
        if self.getMonsterSpaceLeft() > 0:
            if self.bot.wizard_info['social_point_current'] >= 100:
                self.bot.log('Summoning unit using {}'.format(summon_type_map[5]))
                self.bot.SummonUnit(5)
                return 0
            else:
                self.bot.log('Not enough social points to complete {}: '
                             '{}'.format(summon_type_map[5], self.bot.wizard_info['social_point_current']))
                return 1
        else:
            self.bot.log('Not enough space to summon. Maybe put monsters in storage. '
                         'Only {} available.'.format(self.bot.wizard_info['unit_slots']['number']))
        return 2

    def doUnknownSummon(self):
        if self.getMonsterSpaceLeft() > 0:
            if self.bot.wizard_info['wizard_mana'] >= 300:
                inventory_scroll_index = None
                for inventory_item, info_ in self.bot.inventory_list.items():
                    if info_['item_master_type'] == 9 and info_['item_master_id'] == 1:
                        inventory_scroll_index = self.bot.inventory_list.index(inventory_item)
                        break
                if inventory_scroll_index >= 0 and self.bot.inventory_list[inventory_scroll_index]['item_quantity'] > 0:
                    self.bot.log('Summoning unit using {}'.format(summon_type_map[1]))
                    self.bot.SummonUnit(1)
                    return 0
                else:
                    self.bot.log('None or not enough items found to do summon {}.'.format(summon_type_map[1]))
                    return 1
            else:
                self.bot.log('Not enough mana to complete {}: {}'.format(summon_type_map[1],
                                                                         self.bot.wizard_info['wizard_mana']))
                return 1
        else:
            self.bot.log('Not enough space to summon. Maybe put monsters in storage. '
                         'Only {} available.'.format(self.bot.wizard_info['unit_slots']['number']))
        return 2

    def doMysticalSummon(self):
        if self.getMonsterSpaceLeft() > 0:
            if self.bot.wizard_info['wizard_mana'] >= 10000:
                inventory_scroll_index = None
                for inventory_item, info_ in self.bot.inventory_list.items():
                    if info_['item_master_type'] == 9 and info_['item_master_id'] == 2:
                        inventory_scroll_index = self.bot.inventory_list.index(inventory_item)
                        break
                if inventory_scroll_index >= 0 and self.bot.inventory_list[inventory_scroll_index]['item_quantity'] > 0:
                    self.bot.log('Summoning unit using {}'.format(summon_type_map[3]))
                    self.bot.SummonUnit(3)
                    return 0
                else:
                    self.bot.log('None or not enough items found to do summon {}.'.format(summon_type_map[3]))
                    return 1
            else:
                self.bot.log('Not enough mana to complete {}: '
                             '{}'.format(summon_type_map[3], self.bot.wizard_info['wizard_mana']))
                return 1
        else:
            self.bot.log('Not enough space to summon. Maybe put monsters in storage. '
                         'Only {} available.'.format(self.bot.wizard_info['unit_slots']['number']))
        return 2

    def getMonsterSpaceLeft(self):
        unit_slots = self.bot.wizard_info['unit_slots']['number']
        for unit, info_ in self.bot.unit_list.items():
            if info_['building_id'] == 0:
                unit_slots -= 1
                if unit_slots == 0:
                    break
        return unit_slots

    def check_tutorial(self):
        if 1 in self.bot.quest_active:
            self.bot.log('Tutorial not done.')
        else:
            self.bot.log('Tutorial done.')

    def check_finished_ach(self):
        for ach in self.bot.quest_rewarded:
            if ach in self.bot.quest_active:
                self.bot.log('Error: completed quest {} also in active quests'.format(ach))
        self.bot.log('Finished quests: {}'.format(self.bot.quest_rewarded))

    def check_open_ach(self):
        with open('achievements.json', 'r', encoding='utf-8') as ach:
            achievements = json.load(ach)
        open_quest_list = []
        for open_ach, item_ in self.bot.quest_active.items():
            # print(open_ach)
            try:
                index = find(achievements, 'quest id', str(open_ach))
                open_quest_list.append([open_ach, item_['conditions'], achievements[index]['title_en'],
                                        ast.literal_eval(achievements[index]['conditions']),
                                        ast.literal_eval(achievements[index]['req id'])])
            except ValueError:
                self.bot.log('Open quest: {} not founrd.'.format(open_ach))
        self.bot.log(open_quest_list)

    def upgradeEnergyBuildings(self):
        try:
            deco_id_sanctum = self.bot.deco_list[10]['deco_id']
            level = self.bot.deco_list[10]['level']
            if level < 10:
                cost = decoration_upgrade_cost[10][level + 1]
                if self.bot.wizard_info['honor_point'] >= cost:
                    self.bot.UpgradeDeco(deco_id_sanctum)
                else:
                    self.bot.log('Not enough honor points ({}) to upgrade '
                                 'sanctum of energy to level {}'.format(self.bot.wizard_info['honor_point'], level + 1))
            else:
                self.bot.log('Sanctum of energy already maxed.')
        except KeyError:
            self.bot.log('Sanctum of energy not found in deco list.')
        try:
            deco_id_plant = self.bot.deco_list[11]['deco_id']
            # self.bot.UpgradeDeco(deco_id_plant)
            level = self.bot.deco_list[11]['level']
            if level < 10:
                cost = decoration_upgrade_cost[11][level + 1]
                if self.bot.wizard_info['honor_point'] >= cost:
                    self.bot.UpgradeDeco(deco_id_plant)
                else:
                    self.bot.log('Not enough honor points ({}) to upgrade myterious plant to level {}'.format(
                        self.bot.wizard_info['honor_point'], level + 1))
            else:
                self.bot.log('Myterious plant already maxed.')
        except KeyError:
            self.bot.log('Mysterious plant not found in deco list.')

    def maintainFriendList(self):
        if len(self.bot.friend_list) < 50:
            self.bot.GetGuildInfo()
            self.bot.GetFriendList()
            missing_friends = 50 - len(self.bot.friend_list)
            friend_requests = self.bot.GetFriendRequest()
            if missing_friends > 0:
                if friend_requests['friend_req_list']:
                    for new_friend in friend_requests['friend_req_list']:
                        if self.bot.AcceptFriendRequest(new_friend['wizard_id'], new_friend['wizard_name']):
                            missing_friends -= 1
                        else:
                            self.bot.log('Not able to accept request from {}'.format(
                                new_friend['wizard_name'] if new_friend['wizard_name'] else new_friend['wizard_id']))
                        if missing_friends == 0:
                            break
            if missing_friends > 0:
                pending_requests = self.bot.GetFriendRequestSend()['friend_req_list']
                recommended_friends = self.bot.GetFriendRecommended()
                for recommended_friend in recommended_friends['recommended_list']:
                    if recommended_friend['wizard_id'] not in [info_['wizard_id'] for
                                                               friend, info_ in self.bot.friend_list.items()] \
                            and recommended_friend['wizard_id'] not in [pending['wizard_id'] for
                                                                        pending in pending_requests]:
                        if self.bot.AddFriendRequestByUid(recommended_friend['channel_uid'],
                                                          recommended_friend['wizard_name']):
                            missing_friends -= 1
                        else:
                            self.bot.log('Not able to send friend request to {}'.format(
                                recommended_friend['wizard_name'] if recommended_friend['wizard_name']
                                else recommended_friend['wizard_id']))
                    else:
                        self.bot.log('Already sent friend request to {} or already in friend list.'.format(
                            recommended_friend['wizard_name'] if recommended_friend['wizard_name']
                            else recommended_friend['wizard_id']))

    def startingRoutine(self, user_='', user_mail_='', pw_='', device_id_='', device_=None, region_='eu'):
        pass

    class GameCommander:
        """
        Internal class of bot in order to control request and response sending handling.
        Will decide what requests are sent to the server.
        Prevent bot from mixing different requests and focusing on single aspect.
        """
        pass


class MailCommander:
    pass


class WishCommander:
    pass


class ShopCommander:
    pass


class BattleCommander:
    pass


if __name__ == "__main__":
    # Login-data:
    user = ''
    user_mail = ''
    pw = ''
    # device id
    device_id = 'xxx'
    region = ''
    autoplay = Bot(user, user_mail, pw, device_id, region)
	# Items to buy from shop
    item_list = [9, 13]
    while True:
        try:
            if datetime.today().date() > autoplay.loginDay:
                autoplay.loginDay = datetime.today().date()
                autoplay = Bot(user, user_mail, pw, device_id, device, region)

            while autoplay.bot.wish_list['trial_remained'] > 0:
                autoplay.bot.log('Doing daily wish.')
                autoplay.doDailyWish()
            if autoplay.checkMailForCollectibles() > 0:
                autoplay.bot.log('Collecting all mailed items.')
                autoplay.collectAllMail()
            if autoplay.checkMailForSocialPoints():
                autoplay.bot.log('Collecting social points from mail.')
                autoplay.collectAllSocialPoints()
            autoplay.refreshShop(False)
            start = time.time()

            autoplay.buyShopItems(item_list)
            autoplay.bot.log('Refreshed the shop.')
            autoplay.bot.log(autoplay.bot.buildings)
            for building, info in autoplay.bot.buildings.items():
                if 'harvest_available' in info and \
                        info['harvest_available'] > 0:
                    autoplay.bot.Harvest(info['building_id'])
                    time.sleep(random.uniform(0.5, 2.5))
            if 0 in [info['completed'] for quest, info in autoplay.bot.daily_quest_list.items()] \
                    or 0 in [info['rewarded'] for quest, info in autoplay.bot.daily_quest_list.items()]:
                autoplay.doDailyQuests()
            else:
                autoplay.bot.log('All daily quests already finished and collected.')
            autoplay.sendSocialPoints()
            autoplay.ArenaFighterNpc()
            autoplay.buyWeeklyDevilmon()
            autoplay.buyWeeklyGuildRainbowmon()
            autoplay.levelUnitsInBuildings()
            if autoplay.weekly_devilmon_bought:
                autoplay.upgradeEnergyBuildings()
            else:
                autoplay.bot.log('Prioritizing weekly devilmon before energy buildings.')
            autoplay.openShopSlots()

            autoplay.finishScenario(1)
			
            sleeper = max((autoplay.bot.market_info['update_remained'] - (time.time() - start) +
                           random.randint(1, 15)) / 2, 0)
            autoplay.bot.log('Now sleeping for {} seconds.'.format(sleeper))
            time.sleep(sleeper)
            autoplay.bot.GetMailList()
            autoplay.bot.GetDailyQuests()
            autoplay.bot.GetEventTimeTable()
        except (ConnectionResetError, urllib3.exceptions.ProtocolError, requests.exceptions.ConnectionError):
            time.sleep(random.randint(30, 90))
            autoplay = Bot(user, user_mail, pw, device_id, device, region)
