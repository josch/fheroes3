#!/usr/bin/env python
"""
    heroes renaissance
    copyright 2008  - Johannes 'josch' Schauer <j.schauer@email.de>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import gzip
import struct
import pyglet

def extract(filename):
    h3m_data = gzip.open(filename)
    map_data = {}
    #read general info
    (map_data["version"], ) = struct.unpack("<I", h3m_data.read(4))
    if map_data["version"] != 0x1C:
        return
    (map_data["hero_present"], map_data["map_size"], map_data["underworld"], 
        ) = struct.unpack("<BIB", h3m_data.read(6))
    (name_length, ) = struct.unpack("<I", h3m_data.read(4))
    map_data["map_name"] = h3m_data.read(name_length)
    (desc_length, ) = struct.unpack("<I", h3m_data.read(4))
    map_data["map_desc"] = h3m_data.read(desc_length)
    (map_data["difficulty"], map_data["level_limit"], 
        ) = struct.unpack("<BB", h3m_data.read(2))
    
    #player info
    for color in ("Red", "Blue", "Tan", "Green", "Orange", "Purple", "Teal", "Pink"):
        map_data[color] = {}
        (map_data[color]["is_human"], map_data[color]["is_computer"],
            map_data[color]["behaviour"], map_data[color]["isCityTypesOpt"],
            map_data[color]["cityTypes"], map_data[color]["randomCity"],
            ) = struct.unpack("<BBBBHB", h3m_data.read(7))
        (main_city, ) = struct.unpack("<B", h3m_data.read(1))
        if main_city:
            map_data[color]["main_city"] = {}
            (map_data[color]["main_city"]["generate_hero"],
                map_data[color]["main_city"]["type"], 
                ) = struct.unpack("<BB", h3m_data.read(2))
            map_data[color]["main_city"]["coords"] = struct.unpack("<BBB", h3m_data.read(3))
        (map_data[color]["random_hero"], map_data[color]["hero_type"], 
            ) = struct.unpack("<BB", h3m_data.read(2))
        if map_data[color]["hero_type"] != 0xFF:
            (map_data[color]["hero_portrait"], ) = struct.unpack("<B", h3m_data.read(1))
            (name_length, ) = struct.unpack("<I", h3m_data.read(4))
            map_data[color]["hero_name"] = h3m_data.read(name_length)
        h3m_data.read(1) #junk
        (map_data[color]["heroes_count"], ) = struct.unpack("<I", h3m_data.read(4))
        if map_data[color]["heroes_count"] > 0:
            map_data[color]["heroes"] = {}
            for i in xrange(map_data[color]["heroes_count"]):
                (map_data[color]["heroes"]["portrait"], ) = struct.unpack("<B", h3m_data.read(1))
                (name_length, ) = struct.unpack("<I", h3m_data.read(4))
                map_data[color]["heroes"]["name"] = h3m_data.read(name_length)
    
    #special victory condition
    (map_data["victory_conditions"], ) = struct.unpack("<B", h3m_data.read(1))
    if map_data["victory_conditions"] != 0xFF:
        map_data["victory_conditions"] = {"id":map_data["victory_conditions"]}
        (map_data["victory_conditions"]["canStandardEnd"], ) = struct.unpack("<B", h3m_data.read(1))
        (map_data["victory_conditions"]["canComputer"], ) = struct.unpack("<B", h3m_data.read(1))
        if map_data["victory_conditions"]["id"] == 0x00:
            (map_data["victory_conditions"]["artID"], ) = struct.unpack("<B", h3m_data.read(1))
        elif map_data["victory_conditions"]["id"] == 0x01:
            (map_data["victory_conditions"]["creatureID"], ) = struct.unpack("<B", h3m_data.read(1))
            (map_data["victory_conditions"]["creatureCount"], ) = struct.unpack("<H", h3m_data.read(2))
        elif map_data["victory_conditions"]["id"] == 0x02:
            (map_data["victory_conditions"]["resID"], ) = struct.unpack("<B", h3m_data.read(1))
            (map_data["victory_conditions"]["resCount"], ) = struct.unpack("<I", h3m_data.read(4))
        elif map_data["victory_conditions"]["id"] == 0x03:
            raise NotImplementedError
        elif map_data["victory_conditions"]["id"] in (0x04, 0x05, 0x06, 0x07):
            (map_data["victory_conditions"]["x"], ) = struct.unpack("<B", h3m_data.read(1))
            (map_data["victory_conditions"]["y"], ) = struct.unpack("<B", h3m_data.read(1))
            (map_data["victory_conditions"]["z"], ) = struct.unpack("<B", h3m_data.read(1))
        elif map_data["victory_conditions"]["id"] in (0x08, 0x09):
            pass
        elif map_data["victory_conditions"]["id"] == 0x0A:
            raise NotImplementedError
        else:
            raise NotImplementedError
    
    #special loss condition
    (map_data["loss_conditions"], ) = struct.unpack("<B", h3m_data.read(1))
    if map_data["loss_conditions"] != 0xFF:
        map_data["loss_conditions"] = {"id":map_data["loss_conditions"]}
        if map_data["loss_conditions"]["id"] in (0x00, 0x01):
            (map_data["loss_conditions"]["x"], ) = struct.unpack("<B", h3m_data.read(1))
            (map_data["loss_conditions"]["y"], ) = struct.unpack("<B", h3m_data.read(1))
            (map_data["loss_conditions"]["z"], ) = struct.unpack("<B", h3m_data.read(1))
        elif map_data["loss_conditions"]["id"] == 0x02:
            #to be researched
            struct.unpack("<B", h3m_data.read(1))
            struct.unpack("<B", h3m_data.read(1))
        elif map_data["loss_conditions"]["id"] == 0x03:
            (map_data["loss_conditions"]["days"], ) = struct.unpack("<H", h3m_data.read(1))
        else:
            raise NotImplementedError
    
    #Teams
    (map_data["commands_count"], ) = struct.unpack("<B", h3m_data.read(1))
    if map_data["commands_count"] > 0:
        map_data["commands"] = struct.unpack("<8B", h3m_data.read(8))
    
    #Free Heroes
    h3m_data.read(20) #free heroes
    h3m_data.read(4) #junk
    (map_data["heroes_count"], ) = struct.unpack("<B", h3m_data.read(1))
    if map_data["heroes_count"] > 0:
        map_data["free_heroes"] = []
        for i in xrange(map_data["heroes_count"]):
            (hero_id, ) = struct.unpack("<B", h3m_data.read(1))
            (hero_portrait, ) = struct.unpack("<B", h3m_data.read(1))
            (name_length, ) = struct.unpack("<I", h3m_data.read(4))
            hero_name = h3m_data.read(name_length)
            (hero_players, ) = struct.unpack("<B", h3m_data.read(1))
            map_data["free_heroes"].append({"id": hero_id, "portrait":hero_portrait, "name":hero_name, "players":hero_players})
    h3m_data.read(31) #junk
    
    #artefacts
    h3m_data.read(18)
    
    #spells
    h3m_data.read(9)
    
    #sec skillz
    h3m_data.read(4)
    
    #rumors
    (map_data["rumor_count"], ) = struct.unpack("<I", h3m_data.read(4))
    if map_data["rumor_count"] > 0:
        map_data["rumors"] = []
        for i in xrange(map_data["rumor_count"]):
            (name_length, ) = struct.unpack("<I", h3m_data.read(4))
            rumor_name = h3m_data.read(name_length)
            (text_length, ) = struct.unpack("<I", h3m_data.read(4))
            rumor_text = h3m_data.read(text_length)
            map_data["rumors"].append({"name":rumor_name, "text":rumor_text})
    
    #hero options
    for i in xrange(156):
        (hero_enable, ) = struct.unpack("<B", h3m_data.read(1))
        if hero_enable == 1:
            (isExp, ) = struct.unpack("<B", h3m_data.read(1))
            if isExp == 0x01:
                (exp, ) = struct.unpack("<I", h3m_data.read(4))
            (isSecSkill, ) = struct.unpack("<B", h3m_data.read(1))
            if isSecSkill == 0x01:
                (skills_count) = struct.unpack("<I", h3m_data.read(4))
                for i in xrange(skills_count):
                    (skill_id, ) = struct.unpack("<B", h3m_data.read(1))
                    (skill_lvl, ) = struct.unpack("<B", h3m_data.read(1))
            (isArtifact, ) = struct.unpack("<B", h3m_data.read(1))
            if isArtifact == 0x01:
                raise NotImplementedError
            (isBiography, ) = struct.unpack("<B", h3m_data.read(1))
            if isBiography == 0x01:
                (length, ) = struct.unpack("<I", h3m_data.read(4))
                biography = h3m_data.read(length)
            (gender, ) = struct.unpack("<B", h3m_data.read(1))
            (isSpells, ) = struct.unpack("<B", h3m_data.read(1))
            if isSpells == 0x01:
                spells = struct.unpack("<9B", h3m_data.read(9))
            (isPrimarySkills, ) = struct.unpack("<B", h3m_data.read(1))
            if isPrimarySkills == 0x01:
                (attack, defense, power, knowledge) = struct.unpack("<4B", h3m_data.read(4))
    
    map_data["upper_terrain"] = [[] for i in xrange(map_data["map_size"])]
    #read upper world
    for i in xrange(map_data["map_size"]**2):
        x = i%map_data["map_size"]
        y = (i-x)/map_data["map_size"]
        map_data["upper_terrain"][y].append(struct.unpack("<7B", h3m_data.read(7)))
    
    #read underworld
    if map_data["underworld"]:
        map_data["lower_terrain"] = [[] for i in xrange(map_data["map_size"])]
        for i in xrange(map_data["map_size"]**2):
            x = i%map_data["map_size"]
            y = (i-x)/map_data["map_size"]
            map_data["lower_terrain"][y].append(struct.unpack("<7B", h3m_data.read(7)))
    
    (map_data["object_count"], ) = struct.unpack("<I", h3m_data.read(4))
    map_data["objects"] = []
    for i in xrange(map_data["object_count"]):
        (length, ) = struct.unpack("<I", h3m_data.read(4))
        filename = h3m_data.read(length)
        h3m_data.read(6) #passability
        h3m_data.read(6) #actions
        h3m_data.read(2) #landscape
        h3m_data.read(2) #land_edit_groups
        (obj_class, ) = struct.unpack("<I", h3m_data.read(4)) #class
        (obj_number, ) = struct.unpack("<I", h3m_data.read(4)) #number
        (obj_group, ) = struct.unpack("<B", h3m_data.read(1)) #group
        h3m_data.read(1) #isOverlay
        h3m_data.read(16) #junk
        map_data["objects"].append({"filename":filename.lower(), "class":obj_class,
            "number":obj_number, "group":obj_group})
    
    (map_data["tunedobj_count"], ) = struct.unpack("<I", h3m_data.read(4))
    
    map_data["tunedobj"] = []
    for i in xrange(map_data["tunedobj_count"]):
        (x, y, z) = struct.unpack("<3B", h3m_data.read(3))
        (object_id, ) = struct.unpack("<I", h3m_data.read(4))
        #print x,y,z,object_id,
        junk = h3m_data.read(5) #junk
        if junk != "\x00\x00\x00\x00\x00":
            for c in junk:
                print "%02d"%ord(c),
            break
        #print i, map_data["objects"][object_id]["filename"],
        #print map_data["objects"][object_id]["class"]
        
        map_data["tunedobj"].append({"id":object_id, "x":x, "y":y, "z":z})
        
        if object_id in (0,1):
            pass
        elif map_data["objects"][object_id]["class"] == 53:
            if map_data["objects"][object_id]["number"] == 7:
                h3m_data.read(4)
            else:
                h3m_data.read(4)
        elif map_data["objects"][object_id]["class"] in (76, 79):
            (isText, ) = struct.unpack("<B", h3m_data.read(1))
            if isText == 0x01:
                (length, ) = struct.unpack("<I", h3m_data.read(4))
                text = h3m_data.read(length)
                (isGuards, ) = struct.unpack("<B", h3m_data.read(1))
                if isGuards == 0x01:
                    for i in xrange(7):
                        (guard_id, guard_count) = struct.unpack("<HH", h3m_data.read(4))
                h3m_data.read(4) #junk
            (quantity, ) = struct.unpack("<I", h3m_data.read(4))
            h3m_data.read(4) #junk
        elif map_data["objects"][object_id]["class"] in (34, 70, 62):
            (hero_id, color, hero) = struct.unpack("<IBB", h3m_data.read(6))
            (isName, ) = struct.unpack("<B", h3m_data.read(1))
            if isName == 0x01:
                (length, ) = struct.unpack("<I", h3m_data.read(4))
                name = h3m_data.read(length)
            (isExp, ) = struct.unpack("<B", h3m_data.read(1))
            if isExp == 0x01:
                (exp, ) = struct.unpack("<I", h3m_data.read(4))
            (isPortrait, ) = struct.unpack("<B", h3m_data.read(1))
            if isPortrait == 0x01:
                (portrait, ) = struct.unpack("<B", h3m_data.read(1))
            (isSecSkill, ) = struct.unpack("<B", h3m_data.read(1))
            if isSecSkill == 0x01:
                (skills_count, ) = struct.unpack("<I", h3m_data.read(4))
                for i in xrange(skills_count):
                    (skill_id, ) = struct.unpack("<B", h3m_data.read(1))
                    (skill_lvl, ) = struct.unpack("<B", h3m_data.read(1))
            (isCreature, ) = struct.unpack("<B", h3m_data.read(1))
            if isCreature == 0x01:
                for i in xrange(7):
                    (guard_id, ) = struct.unpack("<H", h3m_data.read(2))
                    (guard_count, ) = struct.unpack("<H", h3m_data.read(2))
            (creaturesFormation, ) = struct.unpack("<B", h3m_data.read(1))
            (isArtifact, ) = struct.unpack("<B", h3m_data.read(1))
            if isArtifact == 0x01:
                (headID, shouldersID, neckID, rightHandID, leftHandID, 
                trunkID, rightRingID, leftRingID, legsID, misc1ID, misc2ID,
                misc3ID, misc4ID, machine1ID, machine2ID, machine3ID,
                machine4ID, magicbook, misc5ID) \
                    = struct.unpack("<19H", h3m_data.read(38))
                (knapsack_count, ) = struct.unpack("<H", h3m_data.read(2))
                if knapsack_count > 0:
                    for i in xrange(knapsack_count):
                        (knapsackID, ) = struct.unpack("<H", h3m_data.read(2))
            (zoneRadius, ) = struct.unpack("<B", h3m_data.read(1))
            (isBiography, ) = struct.unpack("<B", h3m_data.read(1))
            if isBiography == 0x01:
                (length, ) = struct.unpack("<I", h3m_data.read(4))
                biography = h3m_data.read(length)
            (gender, ) = struct.unpack("<B", h3m_data.read(1))
            (isSpells, ) = struct.unpack("<B", h3m_data.read(1))
            if isSpells == 0x01:
                spells = struct.unpack("<9B", h3m_data.read(9))
            (isPrimarySkills, ) = struct.unpack("<B", h3m_data.read(1))
            if isPrimarySkills == 0x01:
                (attack, defense, power, knowledge) = struct.unpack("<4B", h3m_data.read(4))
            h3m_data.read(16) #unknown
        elif map_data["objects"][object_id]["class"] in (17, 20, 42):
            (owner, ) = struct.unpack("<I", h3m_data.read(4))
        elif map_data["objects"][object_id]["class"] == 93:
            (isText, ) = struct.unpack("<B", h3m_data.read(1))
            if isText == 0x01:
                (length, ) = struct.unpack("<I", h3m_data.read(4))
                text = h3m_data.read(length)
                (isGuards, ) = struct.unpack("<B", h3m_data.read(1))
                if isGuards == 0x01:
                    for i in xrange(7):
                        (guard_id, guard_count) = struct.unpack("<HH", h3m_data.read(4))
                h3m_data.read(4) #junk
            (spell_id, ) = struct.unpack("<I", h3m_data.read(4))
        elif map_data["objects"][object_id]["class"] == 216:
            (owner, ) = struct.unpack("<I", h3m_data.read(4))
            (junk, ) = struct.unpack("<I", h3m_data.read(4))
            if junk == 0x00:
                (towns, ) = struct.unpack("<H", h3m_data.read(2))
            (minlevel, maxlevel, ) = struct.unpack("<2B", h3m_data.read(2))
        elif map_data["objects"][object_id]["class"] in (54, 71, 72, 73, 74, 75, 162, 163, 164):
            (monster_id, ) = struct.unpack("<I", h3m_data.read(4))
            (monster_count, ) = struct.unpack("<H", h3m_data.read(2))
            (mood, ) = struct.unpack("<B", h3m_data.read(1))
            (isTreasureOrText, ) = struct.unpack("<B", h3m_data.read(1))
            if isTreasureOrText == 0x01:
                (length, ) = struct.unpack("<I", h3m_data.read(4))
                text = h3m_data.read(length)
                (wood, mercury, ore, sulfur, crystal, gem, gold, artefactID) \
                    = struct.unpack("<7IH", h3m_data.read(30))
            (mosterNeverRunAway, ) = struct.unpack("<B", h3m_data.read(1))
            (monsterDontGrowUp, ) = struct.unpack("<B", h3m_data.read(1))
            h3m_data.read(2) #junk
        elif map_data["objects"][object_id]["class"] in (98, 77):
            h3m_data.read(4) #junk
            (owner, ) = struct.unpack("<B", h3m_data.read(1))
            (isName, ) = struct.unpack("<B", h3m_data.read(1))
            if isName == 0x01:
                (length, ) = struct.unpack("<I", h3m_data.read(4))
                name = h3m_data.read(length)
            (isGuard, ) = struct.unpack("<B", h3m_data.read(1))
            if isGuard == 0x01:
                for i in xrange(7):
                    (guard_id, guard_count) = struct.unpack("<HH", h3m_data.read(4))
            (formation, ) = struct.unpack("<B", h3m_data.read(1))
            (isBuildings, ) = struct.unpack("<B", h3m_data.read(1))
            if isBuildings == 0x01:
                build = struct.unpack("6B", h3m_data.read(6))
                active = struct.unpack("6B", h3m_data.read(6))
            else:
                (isFort, ) = struct.unpack("<B", h3m_data.read(1))
            mustSpells = struct.unpack("<9B", h3m_data.read(9))
            canSpells = struct.unpack("<9B", h3m_data.read(9))
            (eventQuantity, ) = struct.unpack("<I", h3m_data.read(4))
            if eventQuantity > 0:
                for i in xrange(eventQuantity):
                    (length, ) = struct.unpack("<I", h3m_data.read(4))
                    event_name = h3m_data.read(length)
                    (length, ) = struct.unpack("<I", h3m_data.read(4))
                    event_text = h3m_data.read(length)
                    (wood, mercury, ore, sulfur, crystal, gem, gold, 
                    players_affected, human_affected, ai_affected, 
                    day_of_first_event, event_iteration) \
                        = struct.unpack("<7I3B2H", h3m_data.read(35))
                    h3m_data.read(16) #junk
                    buildings = struct.unpack("<6B", h3m_data.read(6))
                    creatures = struct.unpack("<7H", h3m_data.read(14))
                    h3m_data.read(4) #junk
            h3m_data.read(4) #junk
        elif map_data["objects"][object_id]["class"] in (5, 65, 66, 67, 68, 69):
            (isText, ) = struct.unpack("<B", h3m_data.read(1))
            if isText == 0x01:
                (length, ) = struct.unpack("<I", h3m_data.read(4))
                text = h3m_data.read(length)
                (isGuards, ) = struct.unpack("<B", h3m_data.read(1))
                if isGuards == 0x01:
                    for i in xrange(7):
                        (guard_id, guard_count) = struct.unpack("<HH", h3m_data.read(4))
                h3m_data.read(4) #junk
        elif map_data["objects"][object_id]["class"] in (33, 219):
            (color, ) = struct.unpack("<I", h3m_data.read(4))
            for i in xrange(7):
                (guard_id, guard_count) = struct.unpack("<HH", h3m_data.read(4))
            (undeleteSoldiers, ) = struct.unpack("<B", h3m_data.read(1))
            h3m_data.read(8)
        elif map_data["objects"][object_id]["class"] == 87:
            (owner, ) = struct.unpack("<I", h3m_data.read(4))
        elif map_data["objects"][object_id]["class"] == 83:
            (quest, ) = struct.unpack("<B", h3m_data.read(1))
            
            if quest == 0x00:
                pass
            elif quest == 0x01:
                (level, ) = struct.unpack("<I", h3m_data.read(4))
            elif quest == 0x02:
                (offence, defence, power, knowledge) = struct.unpack("4B", h3m_data.read(4))
            elif quest == 0x03:
                (hero_id, ) = struct.unpack("<I", h3m_data.read(4))
            elif quest == 0x04:
                (monster_id, ) = struct.unpack("<I", h3m_data.read(4))
            elif quest == 0x05:
                (art_quantity, ) = struct.unpack("<B", h3m_data.read(1))
                for i in xrange(art_quantity):
                    (art, ) = struct.unpack("<H", h3m_data.read(2))
            elif quest == 0x06:
                (creatures_quantity, ) = struct.unpack("<B", h3m_data.read(1))
                for i in xrange(creatures_quantity):
                    (guard_id, ) = struct.unpack("<H", h3m_data.read(2))
                    (guard_count, ) = struct.unpack("<H", h3m_data.read(2))
            elif quest == 0x07:
                resources = struct.unpack("7I", h3m_data.read(28))
            elif quest == 0x08:
                (hero_id, ) = struct.unpack("<B", h3m_data.read(1))
            elif quest == 0x09:
                (player, ) = struct.unpack("<B", h3m_data.read(1))
            else:
                raise NotImplementedError
            
            (time_limit, ) = struct.unpack("<I", h3m_data.read(4))
            (length, ) = struct.unpack("<I", h3m_data.read(4))
            quest_begin = h3m_data.read(length)
            (length, ) = struct.unpack("<I", h3m_data.read(4))
            quest_running = h3m_data.read(length)
            (length, ) = struct.unpack("<I", h3m_data.read(4))
            quest_end = h3m_data.read(length)
            
            (reward, ) = struct.unpack("<B", h3m_data.read(1))
            if reward == 0x00:
                pass
            elif reward == 0x01:
                (exp, ) = struct.unpack("<I", h3m_data.read(4))
            elif reward == 0x02:
                (spell_points, ) = struct.unpack("<I", h3m_data.read(4))
            elif reward == 0x03:
                (morale, ) = struct.unpack("<B", h3m_data.read(1))
            elif reward == 0x04:
                (lucky, ) = struct.unpack("<B", h3m_data.read(1))
            elif reward == 0x05:
                (resID, ) = struct.unpack("<B", h3m_data.read(1))
                (res_quantity, ) = struct.unpack("<I", h3m_data.read(4))
            elif reward == 0x06:
                (priSkillID, ) = struct.unpack("<B", h3m_data.read(1))
                (priSkillBonus, ) = struct.unpack("<B", h3m_data.read(1))
            elif reward == 0x07:
                (secSkillID, ) = struct.unpack("<B", h3m_data.read(1))
                (secSkillBonus, ) = struct.unpack("<B", h3m_data.read(1))
            elif reward == 0x08:
                (artID, ) = struct.unpack("<H", h3m_data.read(2))
            elif reward == 0x09:
                (spellID, ) = struct.unpack("<B", h3m_data.read(1))
            elif reward == 0x0A:
                (creatureID, ) = struct.unpack("<H", h3m_data.read(2))
                (creatureQuantity, ) = struct.unpack("<H", h3m_data.read(2))
            else:
                raise NotImplementedError
            
            h3m_data.read(2) #junk
        elif map_data["objects"][object_id]["class"] in (91, 59):
            (length, ) = struct.unpack("<I", h3m_data.read(4))
            text = h3m_data.read(length)
            h3m_data.read(4) #junk
        elif map_data["objects"][object_id]["class"] == 113:
            (secSkills, ) = struct.unpack("<I", h3m_data.read(4))
        elif map_data["objects"][object_id]["class"] in (88, 89, 90):
            (spellID, ) = struct.unpack("<I", h3m_data.read(4))
        elif map_data["objects"][object_id]["class"] == 215:
            (quest, ) = struct.unpack("<B", h3m_data.read(1))
            
            if quest == 0x00:
                pass
            elif quest == 0x01:
                (level, ) = struct.unpack("<I", h3m_data.read(4))
            elif quest == 0x02:
                (offence, defence, power, knowledge) = struct.unpack("4B", h3m_data.read(4))
            elif quest == 0x03:
                (hero_id, ) = struct.unpack("<I", h3m_data.read(4))
            elif quest == 0x04:
                (monster_id, ) = struct.unpack("<I", h3m_data.read(4))
            elif quest == 0x05:
                (art_quantity, ) = struct.unpack("<B", h3m_data.read(1))
                for i in xrange(art_quantity):
                    (art, ) = struct.unpack("<H", h3m_data.read(2))
            elif quest == 0x06:
                (creatures_quantity, ) = struct.unpack("<B", h3m_data.read(1))
                for i in xrange(creatures_quantity):
                    (guard_id, ) = struct.unpack("<H", h3m_data.read(2))
                    (guard_count, ) = struct.unpack("<H", h3m_data.read(2))
            elif quest == 0x07:
                resources = struct.unpack("7I", h3m_data.read(28))
            elif quest == 0x08:
                (hero_id, ) = struct.unpack("<B", h3m_data.read(1))
            elif quest == 0x09:
                (player, ) = struct.unpack("<B", h3m_data.read(1))
            else:
                raise NotImplementedError
            
            (time_limit, ) = struct.unpack("<I", h3m_data.read(4))
            (length, ) = struct.unpack("<I", h3m_data.read(4))
            quest_begin = h3m_data.read(length)
            (length, ) = struct.unpack("<I", h3m_data.read(4))
            quest_running = h3m_data.read(length)
            (length, ) = struct.unpack("<I", h3m_data.read(4))
            quest_end = h3m_data.read(length)
        elif map_data["objects"][object_id]["class"] == 36:
            (radius, ) = struct.unpack("<B", h3m_data.read(1))
            h3m_data.read(3) #junk
        elif map_data["objects"][object_id]["class"] == 220:
            (resources, ) = struct.unpack("<B", h3m_data.read(1))
            h3m_data.read(3) #junk
        elif map_data["objects"][object_id]["class"] == 217:
            (owner, towns) = struct.unpack("<II", h3m_data.read(8))
            if towns==0x00:
                (towns,) = struct.unpack("<H", h3m_data.read(2))
        elif map_data["objects"][object_id]["class"] == 218:
            (owner, minlvl, maxlvl) = struct.unpack("<IBB", h3m_data.read(6))
        elif map_data["objects"][object_id]["class"] == 81:
            (bonus_type, primaryID) = struct.unpack("<BI", h3m_data.read(5))
            h3m_data.read(3) #junk
        elif map_data["objects"][object_id]["class"] == 6:
            (isText, ) = struct.unpack("<B", h3m_data.read(1))
            if isText == 0x01:
                (length, ) = struct.unpack("<I", h3m_data.read(4))
                text = h3m_data.read(length)
                (isGuards, ) = struct.unpack("<B", h3m_data.read(1))
                if isGuards == 0x01:
                    for i in xrange(7):
                        (guard_id, guard_count) = struct.unpack("<HH", h3m_data.read(4))
                h3m_data.read(4) #junk
            (exp, spell_points, morals, luck, wood, mercury, ore, sulfur,
            crystal, gem, gold, offence, defence, power, knowledge) = \
                struct.unpack("<IIBBIIIIIIIBBBB", h3m_data.read(42))
            (secSkills, ) = struct.unpack("<B", h3m_data.read(1))
            if secSkills > 0:
                for i in xrange(secSkills):
                    (skill_id, skill_lvl) = struct.unpack("<BB", h3m_data.read(2))
            (artefacts, ) = struct.unpack("<B", h3m_data.read(1))
            if artefacts > 0:
                for i in xrange(artefacts):
                    (artID, ) = struct.unpack("<H", h3m_data.read(2))
            (spells, ) = struct.unpack("<B", h3m_data.read(1))
            if spells > 0:
                for i in xrange(spells):
                    (spellID, ) = struct.unpack("<B", h3m_data.read(1))
            (monsters, ) = struct.unpack("<B", h3m_data.read(1))
            if monsters > 0:
                for i in xrange(monsters):
                    (guard_id, guard_count) = struct.unpack("<HH", h3m_data.read(4))
            h3m_data.read(8) #junk
        elif map_data["objects"][object_id]["class"] == 26:
            (isText, ) = struct.unpack("<B", h3m_data.read(1))
            if isText == 0x01:
                (length, ) = struct.unpack("<I", h3m_data.read(4))
                text = h3m_data.read(length)
                (isGuards, ) = struct.unpack("<B", h3m_data.read(1))
                if isGuards == 0x01:
                    for i in xrange(7):
                        (guard_id, guard_count) = struct.unpack("<HH", h3m_data.read(4))
                h3m_data.read(4) #junk
            (exp, spell_points, morals, luck, wood, mercury, ore, sulfur,
            crystal, gem, gold, offence, defence, power, knowledge) = \
                struct.unpack("<IIBBIIIIIIIBBBB", h3m_data.read(42))
            (secSkills, ) = struct.unpack("<B", h3m_data.read(1))
            if secSkills > 0:
                for i in xrange(secSkills):
                    (skill_id, skill_lvl) = struct.unpack("<BB", h3m_data.read(2))
            (artefacts, ) = struct.unpack("<B", h3m_data.read(1))
            if artefacts > 0:
                for i in xrange(artefacts):
                    (artID, ) = struct.unpack("<H", h3m_data.read(2))
            (spells, ) = struct.unpack("<B", h3m_data.read(1))
            if spells > 0:
                for i in xrange(spells):
                    (spellID, ) = struct.unpack("<B", h3m_data.read(1))
            (monsters, ) = struct.unpack("<B", h3m_data.read(1))
            if monsters > 0:
                for i in xrange(monsters):
                    (guard_id, guard_count) = struct.unpack("<HH", h3m_data.read(4))
            h3m_data.read(8) #junk
            (players, isAICan, disableAfterFirstDay) = struct.unpack("<BBB", h3m_data.read(3))
            h3m_data.read(4) #junk
    
    try:
        (gevents_count, ) = struct.unpack("<I", h3m_data.read(4))
        for i in xrange(gevents_count):
            (length, ) = struct.unpack("<I", h3m_data.read(4))
            name = h3m_data.read(length)
            (length, ) = struct.unpack("<I", h3m_data.read(4))
            text = h3m_data.read(length)
            h3m_data.read(7*4) #resources
            (players_affected, ) = struct.unpack("<B", h3m_data.read(1))
            (human_affected, ) = struct.unpack("<B", h3m_data.read(1))
            (ai_affected, ) = struct.unpack("<B", h3m_data.read(1))
            (day_of_first_event,) = struct.unpack("<H", h3m_data.read(2))
            (event_iteration,) = struct.unpack("<H", h3m_data.read(2))
            h3m_data.read(16) #junk
    except:
        print "d'ough...'"
    
    h3m_data.read(124) #junk
    
    return map_data
