from penguin_game import *
from collections import *

#############
# CONSTANTS #
#############
DEBUG = True
UPGRADE_FACTOR = 0.75  # By how much to decrease cost to assume you want to upgrade
AMBUSH_FACTOR = 0.6
TURNS_OVER = 0.8

####################
# GLOBAL VARIABLES #
####################
Game = None
player = None  # type: Union[Player, None]
enemy_player = None  # type: Union[Player, None]
neutral_player = None  # type: Union[Player, None]
my_icebergs = []  # type: List[Iceberg]
enemy_icebergs = []  # type: List[Iceberg]
neutral_icebergs = []  # type: List[IceBuilding]
bonus_iceberg = None
all_icebergs = []  # type: list[IceBuilding]
my_penguin_groups = []  # type: List[PenguinGroup]
enemy_penguin_groups = []  # type: List[PenguinGroup]
ice_data = {}  # type: dict
my_future_ices = []  # type: List[Iceberg]
future_enemy_icebergs = []  # type: List[Iceberg]
future_neutral_icebergs = []
calc_future_state = {}  # type: dict  # The amount on each iceberg after calculating all of the penguin groups
need_protect = []
neighbors_map = {}
front = []
circular = False


def do_turn(game):
    # type: (Game) -> None
    pre_turn(game)

    _protect()
    _bridge()
    _neutral()
    _upgrade()
    _bonus()
    _attack()
    _reinforce()

    if DEBUG:
        print("after turn")
        print(ice_data)


def pre_turn(game):
    '''
    Calculates lists and variables that are needed during the turn
    '''
    global Game
    global player
    global enemy_player
    global neutral_player
    global my_icebergs
    global enemy_icebergs
    global neutral_icebergs
    global bonus_iceberg
    global all_icebergs
    global my_penguin_groups
    global enemy_penguin_groups
    global ice_data
    global future_enemy_icebergs
    global my_future_ices
    global calc_future_state
    global need_protect
    global neighbors_map
    global circular
    global front

    Game = game
    player = game.get_myself()
    enemy_player = game.get_enemy()
    neutral_player = game.get_neutral()
    my_icebergs = game.get_my_icebergs()
    enemy_icebergs = game.get_enemy_icebergs()
    neutral_icebergs = game.get_neutral_icebergs()
    bonus_iceberg = game.get_bonus_iceberg()
    all_icebergs = game.get_all_icebergs()
    my_penguin_groups = game.get_my_penguin_groups()
    enemy_penguin_groups = game.get_enemy_penguin_groups()
    neighbors_map = find_neighbors()
    circular = is_circular()  # circular map
    front = battlefront()

    for ice in my_icebergs:
        free_amount = find_free_amount(ice)
        safe_amount = keep_from_dying(ice)
        free_amount = min(free_amount, safe_amount)

        info = {"amount": free_amount, "acted": False}
        ice_data[ice.unique_id] = info

    my_future_ices = list(my_icebergs)  # type: List[Iceberg]
    future_enemy_icebergs = list(enemy_icebergs)  # type: List[Iceberg]
    future_neutral_icebergs = []

    # future icebergs
    for i in all_icebergs:
        owner, amount, max_dist = IceState(i)
        calc_future_state[i.unique_id] = {"owner": owner, "amount": amount, "inTurn": max_dist}
        if not i.owner.equals(enemy_player) and not i.owner.equals(player):  # Neutral Ice
            if owner == player:
                my_future_ices.append(i)
            if owner == enemy_player:
                future_enemy_icebergs.append(i)
            if owner == neutral_player:
                future_neutral_icebergs.append(i)


def _upgrade():
    global ice_data

    for ice in my_icebergs:
        if ice.level < ice.upgrade_level_limit and ice_data[ice.unique_id][
            "amount"] >= ice.upgrade_cost * UPGRADE_FACTOR:

            if ice_data[ice.unique_id]["amount"] >= ice.upgrade_cost and not ice_data[ice.unique_id][
                "acted"] and ice.can_upgrade():
                ice.upgrade()
            ice_data[ice.unique_id]["acted"] = "Upgrade"


def _protect():
    global ice_data

    need_protect = []

    if len(my_icebergs) < 2:
        return

    for ice in my_icebergs:
        if calc_future_state[ice.unique_id]["owner"] != player:
            need_protect.append(ice)

    need_protect = sorted(need_protect, key=lambda x: avg_distance_from_others(x, [y for y in my_icebergs if
                                                                                   not x.equals(y)]) / x.level)
    if need_protect:
        for needIce in need_protect:
            amount = calc_future_state[ice.unique_id]["amount"] + 1  # maybe use IceState

            can_help_ices = sorted(my_icebergs, key=lambda x: (Get_turns_till_arrival(x, needIce), x.penguin_amount))

            for ice in can_help_ices:
                if ice.level < 2:
                    continue

                if ice.equals(needIce):
                    continue

                if Get_turns_till_arrival(ice, needIce) >= max_dis(all_icebergs) // 2:
                    continue

                if ice_data[ice.unique_id]["amount"] > ice.penguins_per_turn:
                    ice_amount = ice_data[ice.unique_id]["amount"]

                    if ice_amount >= amount:
                        send_penguins(ice, needIce, amount, "protect")
                        need_protect.remove(needIce)
                        break

                    else:
                        amount -= ice_amount
                        send_penguins(ice, needIce, ice_amount, "protect")


def _neutral():
    global ice_data
    flag = False

    for ice in my_icebergs:

        #  special case:
        destination = special_dest()
        if destination:
            amount = IceState(destination, Get_turns_till_arrival(ice, destination))[1] + 1
            if amount <= ice_data[ice.unique_id]["amount"]:
                ice.send_penguins(destination, amount)
                return

        if not destination:
            if ice.level < avg_level(enemy_icebergs) * UPGRADE_FACTOR:
                continue
            destination = get_best_natural_ice(ice)

        if destination and Get_turns_till_arrival(ice, destination) < max_dis(all_icebergs) // 2:
            amount = IceState(destination, Get_turns_till_arrival(ice, destination))[1] + 1
            if amount <= ice_data[ice.unique_id]["amount"]:
                send_penguins(ice, destination, amount, "attck neutral")


def _attack():
    if bonus_iceberg and bonus_iceberg.owner.equals(enemy_player):
        attack_dest = [bonus_iceberg]
    else:
        attack_dest = get_best_attack_ices()

    for dest in attack_dest:
        free_ices = [ice for ice in my_icebergs if ice_data[ice.unique_id]["amount"] > 0 and ice_data[ice.unique_id
        ]["acted"] not in ["Upgrade", "Bridge"]]
        free_ices.sort(key=lambda x: Get_turns_till_arrival(x, dest))

        need_amount = IceState(dest, int(avg_distance_from_others(dest, free_ices)))[1] + 1
        for ice in free_ices:

            if not good_to_attack(ice, dest):
                continue

            my_amount = ice_data[ice.unique_id]["amount"]
            if my_amount >= need_amount:
                send_penguins(ice, dest, my_amount, "attack enemy")
                break

            elif my_amount > need_amount * AMBUSH_FACTOR:
                need_amount -= my_amount
                send_penguins(ice, dest, my_amount, "attack enemy")


def _bridge():
    for ice in my_icebergs:
        for g in my_penguin_groups:
            if g.source == ice and g.destination in future_enemy_icebergs + neutral_icebergs:
                if worth_to_build_bridge(ice,
                                         g.destination):  # Dina, I added ur condition to the 'worth_to_build' function
                    create_bridge(ice, g.destination)


def _reinforce():
    global ice_data
    avg_amount = average_peng(my_icebergs)

    free_ices = [ice for ice in my_icebergs if
                 ice_data[ice.unique_id]["acted"] not in ["Upgrade, Bridge"] and ice_data[ice.unique_id]["amount"] > 0]

    front.sort(key=lambda x: calc_future_state[x.unique_id]["amount"])

    _front = list(front)
    if circular:
        _front = list(enemy_icebergs)  # if the map is circular, use the reinforce penguins to attack

    for ice in free_ices:

        if ice in _front:
            continue

        _front.sort(key=lambda x: Get_turns_till_arrival(x, ice))

        for f_ice in _front:

            _amount = ice_data[ice.unique_id]["amount"]
            if _amount <= avg_amount:
                continue

            _amount -= avg_amount

            send_penguins(ice, f_ice, _amount, "reinforce")

            break


def _bonus():
    global ice_data

    if not bonus_iceberg:
        return

    if (groups(bonus_iceberg, enemy_penguin_groups) or IceState(bonus_iceberg)[
        0] == enemy_player):  # or have_more_icebergs():
        for ice in my_icebergs:
            get_turns = Get_turns_till_arrival(ice, bonus_iceberg)
            d_owner, d_amount = IceState(bonus_iceberg, get_turns)[0:2]
            if d_owner != player and ice_data[ice.unique_id]["amount"] > d_amount and get_turns <= max_dis(
                    all_icebergs) // 2:
                send_penguins(ice, bonus_iceberg, d_amount + 1, "bonus")
                break


def create_bridge(ice, dest):
    global ice_data

    if not ice_data[ice.unique_id]["acted"]:
        ice.create_bridge(dest)

        # update iceberg data
        ice_data[ice.unique_id]["amount"] -= Game.iceberg_bridge_cost
        ice_data[ice.unique_id]["acted"] = "Bridge"

        return True

    return False


def send_penguins(iceberg, target, amount, reason=""):
    # type: (Iceberg, Iceberg, int, bool) -> bool

    global ice_data
    if groups(iceberg, enemy_penguin_groups) >= ice_data[iceberg.unique_id]["amount"]:
        return False
    if iceberg.level < 2 and neutral_icebergs and have_more_icebergs():
        return False

    if ice_data[iceberg.unique_id]["acted"] not in ["Upgrade", "Bridge"]:
        if ice_data[iceberg.unique_id][
            "amount"] >= amount:
            if iceberg.can_send_penguins(target, amount):
                iceberg.send_penguins(target, amount)

                ice_data[iceberg.unique_id]["amount"] -= amount
                ice_data[iceberg.unique_id]["acted"] = "Sending"

                if DEBUG:
                    print("{} Sent {} Penguins to {} ({}) - {}".format(iceberg.id, amount, target.id,
                                                                       target.owner.bot_name, reason))
                return True

    return False


# ------------help functions------------#


# --------------neutral-----------------#

def get_best_natural_ice(my_ice):
    natural_ices_sent = [g.destination for g in my_penguin_groups]
    natural_ices_no_sent = [ice for ice in neutral_icebergs if not ice in natural_ices_sent]

    min_ice = None
    if natural_ices_no_sent:
        # when sorting tuple, we sort by the first cell, then second cell and so on
        min_ice = min(natural_ices_no_sent,
                      key=lambda ice: (Get_turns_till_arrival(ice, my_ice) / ice.level, ice.penguin_amount))

    return min_ice


# --------------bridge-----------------#

def worth_to_build_bridge(source, dest):
    # if source.can_create_bridge(dest):
    groups = [g for g in my_penguin_groups if g.source == source and g.destination == dest]
    avg_turns = avg_turns_till_arrival(groups)

    if dest in neutral_icebergs:
        return False

    if dest in future_enemy_icebergs and avg_turns / Game.iceberg_max_bridge_duration >= 0.4 and sum(
            g.penguin_amount for g in groups) > Game.iceberg_bridge_cost:
        return True

    return False


def Turns_till_arrival(g):
    s, d = g.source, g.destination
    b = hasBridge(s, d)
    if not b:
        return g.turns_till_arrival
    if b.duration >= g.turns_till_arrival:
        return int(g.turns_till_arrival // b.speed_multiplier)
    return int((g.turns_till_arrival - b.duration) + (b.duration // b.speed_multiplier))


def Get_turns_till_arrival(s, d):
    turns = s.get_turns_till_arrival(d)
    b = hasBridge(s, d)
    if not b:
        return turns
    if b.duration >= turns:
        return int(turns // b.speed_multiplier)
    return int((turns - b.duration) + (b.duration // b.speed_multiplier))


def hasBridge(s, d):
    '''
    Checks if two icebergs have a bridge between them
    '''
    s_bridges = set(s.bridges)
    for b in d.bridges:
        if b in s_bridges:
            return b
    return None


# --------------attack-----------------#

def good_to_attack(ice, dest):
    enemy_close = False
    for n in neighbors_map[ice.unique_id]:
        if n in future_enemy_icebergs:
            enemy_close = True

    if not enemy_close:
        return False

    dis = Get_turns_till_arrival(ice, dest)
    for n in neutral_icebergs:

        if n.equals(bonus_iceberg):
            continue

        if Get_turns_till_arrival(ice, n) < dis:
            return False

    if sum_levels(my_icebergs) / len(my_icebergs) < sum_levels(enemy_icebergs) < len(enemy_icebergs) * UPGRADE_FACTOR:
        return False

    if enemyTerritory(ice, ice_data[ice.unique_id]["amount"]):
        return False

    return True


def get_best_attack_ices():
    attack_dest = []

    for enemy_ice in future_enemy_icebergs:
        amount = calc_future_state[enemy_ice.unique_id]["amount"]
        good_dist, bad_dist = avg_distance_from_others(enemy_ice, my_icebergs), avg_distance_from_others(enemy_ice,
                                                                                                         enemy_icebergs)
        score = good_dist / bad_dist if bad_dist else 0
        score = amount * score / enemy_ice.level
        attack_dest.append((enemy_ice, score))

    attack_dest.sort(key=lambda x: x[1])
    return [[x[0] for x in attack_dest][0]]


# --------------general-----------------#


def groups(ice, group):
    count = 0
    for x in group:
        if x.destination == ice and not x.decoy:
            count += x.penguin_amount
    return count


def IceState(ice, time=1000, sent=0):
    '''
    Calculates the iceberg state in x turns (time)
    '''
    owner = ice.owner
    amount = ice.penguin_amount - sent

    if amount < 0:
        owner = enemy_player if owner != enemy_player else player
        amount *= -1

    groups = [x for x in my_penguin_groups + enemy_penguin_groups if
              Turns_till_arrival(x) <= time and x.destination == ice]
    groups.sort(key=lambda gp: Turns_till_arrival(gp))

    if time == 1000:
        if groups:
            time = Turns_till_arrival(groups[-1])
        else:
            time = max_dis(all_icebergs)

    curTime = 0
    for g in groups:
        if g.decoy:  # TODO: decoy always return false, need to change it
            continue
        turns_till_arrival = Turns_till_arrival(g)
        if owner != neutral_player and not ice.equals(bonus_iceberg):
            amount += ((turns_till_arrival - curTime) * ice.level)

        amount += g.penguin_amount if g.owner == owner else -g.penguin_amount
        if amount < 0:
            owner = g.owner
            amount *= -1
        if amount == 0:
            owner = neutral_player
        curTime = turns_till_arrival

    if owner != neutral_player and not ice.equals(bonus_iceberg):
        amount += ((time - curTime) * ice.level)

    return [owner, amount, time]


def have_more_icebergs():
    return len(my_icebergs) >= len(enemy_icebergs)


def max_dis(icebergs=all_icebergs):
    """
    this function calculate and return the maximum distance between the icebergs in the game
    """
    n = len(icebergs)
    m = -1
    for i in range(n):
        for j in range(i + 1, n):
            m = max(m, icebergs[i].get_turns_till_arrival(icebergs[j]))
    return m


def min_dis(ices, otherIces=None, diff=False):
    m = float("inf")
    for ice in ices:

        if not otherIces:
            otherIces = ices

        for oth_ice in otherIces:
            if ice.equals(oth_ice):
                continue

            if diff and ice.owner == oth_ice.owner:
                continue

            m = min(m, Get_turns_till_arrival(ice, oth_ice))
    return m


def average_peng(icebergs):
    return int(sum([i.penguin_amount for i in icebergs]) / len(icebergs)) if icebergs else 0


def avg_turns_till_arrival(groups):
    return sum(Turns_till_arrival(g) for g in groups) / len(groups) if groups else 0


def avg_distance_from_others(ice, others):
    return sum(Get_turns_till_arrival(ice, oth) for oth in others) / len(others) if others else 0


def sum_levels(icebergs):
    return sum(ice.level for ice in icebergs) if icebergs else 0


def avg_level(icebergs):
    return sum_levels(icebergs) / len(icebergs) if icebergs else 0


def find_free_amount(ice):
    '''
    Calculate the number of penguins that can act
    '''
    owner = ice.owner
    min_amount = amount = 1  # The minimum amount needs to owner the ice

    groups = [x for x in my_penguin_groups + enemy_penguin_groups if x.destination == ice]
    groups.sort(key=lambda gp: Turns_till_arrival(gp))

    curTime = 0
    for g in groups:
        if g.decoy:
            continue
        turns_till_arrival = Turns_till_arrival(g)
        if owner != neutral_player and not ice.equals(bonus_iceberg):
            amount += ((turns_till_arrival - curTime) * ice.level)

        amount += g.penguin_amount if g.owner == owner else -g.penguin_amount

        if amount <= 0:
            min_amount += (-amount) + 1
            amount = 1

        curTime = turns_till_arrival

    return ice.penguin_amount - min_amount


def keep_from_dying(ice):
    other_ices = [i for i in my_icebergs if i.unique_id != ice.unique_id]  # type: List[Iceberg]
    other_ices.sort(key=lambda i2: i2.get_turns_till_arrival(ice))

    enemy_ices = list(enemy_icebergs)  # type: List[Iceberg]
    enemy_ices.sort(key=lambda i2: i2.get_turns_till_arrival(ice))

    lowest = 10000  # type: int

    for enemy in enemy_ices:
        # Go over all enemies and calc how much you'll have left if they all out.
        # do min(have, had) to get the lowest point.
        dist = enemy.get_turns_till_arrival(ice)  # type: int
        owner, total_friendly, time = IceState(ice, dist)

        if owner != player:
            total_friendly = -total_friendly

        for other in other_ices:
            if other.get_turns_till_arrival(ice) + 1 < dist:
                total_friendly += other.penguin_amount
        after_his_attack = total_friendly - enemy.penguin_amount  # type: int

        lowest = min(after_his_attack, lowest)

    lowest = max(lowest, 0)
    return lowest


def enemyTerritory(my_ice, amount=0):
    ices = sorted(all_icebergs, key=lambda x: Get_turns_till_arrival(my_ice, x))
    ices = ices[1:len(ices) // 3]

    for ice in ices:
        if ice.owner != enemy_player:
            return False

    if sum(ice.penguin_amount for ice in ices) < (my_ice.penguin_amount - amount):
        return False

    return True


def special_dest():
    '''
    cases where the game map are unique, and unique destinations should be chosen
    '''

    # Case #1: game starts where our ice and the enemy ice in the closest positions
    if len(my_icebergs) == len(enemy_icebergs) == 1:
        ice, enemyIce = my_icebergs[0], enemy_icebergs[0]
        if min_dis([ice], all_icebergs) == Get_turns_till_arrival(ice, enemyIce):

            if DEBUG:
                print("special case 1")
            return enemyIce

    # Case #2: almost game is over, a try to last ambush
    if len(my_icebergs) == len(enemy_icebergs) and not neutral_icebergs and Game.turn / 300 > TURNS_OVER:
        dest = min(enemy_icebergs, key=lambda x: avg_distance_from_others(x, my_icebergs))
        for ice in my_icebergs:
            amount = ice_data[ice.unique_id]["amount"]
            if amount > 0:
                send_penguins(ice, dest, amount)
        return dest

    # Case #3 circular map and enemy heads straight for the bonus
    if bonus_iceberg and len(enemy_icebergs) == 1 and groups(bonus_iceberg, enemy_penguin_groups):
        return bonus_iceberg

    # Case 4 circular map - we need to send right away
    if min_dis(all_icebergs) <= 4 and neutral_icebergs:
        return min(neutral_icebergs, key=lambda x: Get_turns_till_arrival(my_icebergs[0], x))

    return None


def find_neighbors():
    global neighbors_map

    for ice in my_icebergs:
        neighbors = []
        for oth_ice in sorted(neutral_icebergs + enemy_icebergs, key=lambda i: Get_turns_till_arrival(ice, i))[
                       :len(all_icebergs) // 3]:
            neighbors.append(oth_ice)
        neighbors_map[ice.unique_id] = neighbors

    return neighbors_map


def battlefront():
    front = []
    my_ices = list(my_icebergs)
    for i in range(2):
        min_distance = float('inf')
        front_ice = None
        for enemy_ice in enemy_icebergs:
            for my_ice in my_ices:
                distance = Get_turns_till_arrival(enemy_ice, my_ice)
                if distance < min_distance:
                    min_distance = distance
                    front_ice = my_ice
        if front_ice:
            front.append(front_ice)
            my_ices.remove(front_ice)

    return front


def ices_map(d):
    mapping = {}

    # for games that do not include bonus iceberg
    allIcebergs = all_icebergs + [bonus_iceberg] if bonus_iceberg else all_icebergs

    for ice in allIcebergs:
        mapping[ice] = []
        for oth in allIcebergs:
            if not ice.equals(oth) and ice.get_turns_till_arrival(oth) <= d:
                mapping[ice].append(oth)

    return mapping


def dfs(visited, mapping, ice):
    ans = set()
    if ice not in visited:
        ans.add(ice)
        visited.add(ice)
        for neighbour in mapping[ice]:
            ans = ans.union(dfs(visited, mapping, neighbour))
    return ans


def is_circular():
    mapping = ices_map(5)

    if DEBUG:
        print(mapping)

    set_ices = dfs(set(), mapping, my_icebergs[0])

    if (len(set_ices) / len(all_icebergs)) < 0.8:
        return False

    for neighbors in mapping.values():
        if len(neighbors) != 2:
            return False

    if DEBUG:
        print("circular")

    return True

