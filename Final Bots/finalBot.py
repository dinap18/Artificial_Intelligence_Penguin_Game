from penguin_game import *
from collections import *

#############
# CONSTANTS #
#############
DEBUG = True
UPGRADE_FACTOR = 0.78
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
neighbors_map = {}  # type: dict
front = []  # type: list(Iceberg)
need_protect = []  # type: list(Iceberg)

MAX_d = MIN_d = 0
circular = False
tricky = False
bonus_map = False
default_map = False
extraFar_t = False
extraFar = False
two_circular = False


def do_turn(game):
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
    global neighbors_map
    global front
    global need_protect

    global MAX_d
    global MIN_d
    global UPGRADE_FACTOR
    global AMBUSH_FACTOR

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
    front = battlefront()
    MAX_d = max_dis(all_icebergs)
    MIN_d = min_dis(all_icebergs)

    # find the current map
    if Game.turn == 1:
        find_map()

    # if len([g for g in enemy_penguin_groups if g.destination.owner.equals(player)]) > len(
    #        [g for g in my_penguin_groups if g.destination.owner.equals(enemy_player)]):
    #   UPGRADE_FACTOR = 0.6

    for ice in my_icebergs:
        # --------------------
        free_amount = find_free_amount(ice)
        safe_amount = keep_from_dying(ice)
        free_amount = min(free_amount, safe_amount)

        info = {"amount": free_amount, "acted": False}
        ice_data[ice.unique_id] = info

    my_future_ices = list(my_icebergs)  # type: List[Iceberg]
    future_enemy_icebergs = list(enemy_icebergs)  # type: List[Iceberg]
    future_neutral_icebergs = []

    # future icebergs
    for i in all_icebergs:  # type: Iceberg
        max_level = level_limit(i)
        owner, amount, max_dist = IceState(i)
        calc_future_state[i.unique_id] = {"owner": owner, "amount": amount, "inTurn": max_dist, "maxLevel": max_level}
        if not i.owner.equals(enemy_player) and not i.owner.equals(player):  # Neutral Ice
            if owner == player:
                my_future_ices.append(i)
            if owner == enemy_player:
                future_enemy_icebergs.append(i)
            if owner == neutral_player:
                future_neutral_icebergs.append(i)


def _upgrade():
    global ice_data
    avg_enemy_level = avg_level(enemy_icebergs)

    # if not have_more_icebergs():
    #    return
    for ice in my_icebergs:

        if ice.level < calc_future_state[ice.unique_id]["maxLevel"] and ice_data[ice.unique_id][
            "amount"] >= ice.upgrade_cost * UPGRADE_FACTOR:

            if ice_data[ice.unique_id]["amount"] >= ice.upgrade_cost * UPGRADE_FACTOR and not ice_data[ice.unique_id][
                "acted"] and ice.can_upgrade():
                ice.upgrade()
                ice_data[ice.unique_id]["acted"] = "Upgrade"

        if avg_enemy_level > ice.level and ice_data[ice.unique_id]["amount"] > 0:
            ice_data[ice.unique_id]["amount"] -= min(ice.upgrade_cost // 4, ice_data[ice.unique_id]["amount"])


def _protect():
    global ice_data

    need_protect = []
    can_help_ices = []

    if len(my_icebergs) < 2:
        return

    for ice in my_icebergs:
        if calc_future_state[ice.unique_id]["owner"] != player:
            need_protect.append(ice)
        else:
            can_help_ices.append(ice)

    need_protect = sorted(need_protect, key=lambda x: avg_distance_from_others(x, [y for y in my_icebergs if
                                                                                   not x.equals(y)]) / x.level)
    print(need_protect)
    print("can help: {}".format(can_help_ices))
    if need_protect:
        for needIce in need_protect:
            amount = calc_future_state[ice.unique_id]["amount"] + 1  # maybe use IceState

            can_help_ices = sorted(my_icebergs, key=lambda x: (Get_turns_till_arrival(x, needIce), x.penguin_amount))

            for ice in can_help_ices:

                if ice.equals(needIce):
                    continue

                if Get_turns_till_arrival(ice, needIce) >= MAX_d // 2 and not tricky:
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

    for ice in my_icebergs:

        #  special case:
        destination = special_dest(ice)

        if not destination:
            if not neutral_icebergs:
                return
            destination = get_best_natural_ice(ice)

        if destination and Get_turns_till_arrival(ice, destination) <= MAX_d // 2:
            amount = IceState(destination, Get_turns_till_arrival(ice, destination))[1] + 1
            if amount <= ice_data[ice.unique_id]["amount"] or circular:
                send_penguins(ice, destination, amount, "attck neutral")

        if tricky:
            amount = calc_future_state[ice.unique_id]["amount"] + 1
            if amount <= ice_data[ice.unique_id]["amount"]:
                send_penguins(ice, destination, amount, "attck neutral")


def _attack():
    if bonus_iceberg and bonus_iceberg.owner.equals(enemy_player):
        attack_dest = [bonus_iceberg]
    else:
        attack_dest = get_best_attack_ices()

    avg_enemy_level = avg_level(enemy_icebergs)

    if have_more_icebergs():
        for front_ice in front:
            if front_ice.level < avg_enemy_level or front_ice.level < 2:
                return

    for dest in attack_dest:

        free_ices = [ice for ice in my_icebergs if ice_data[ice.unique_id]["amount"] > 0 and ice_data[ice.unique_id
        ]["acted"] not in ["Upgrade", "Bridge"] and not ice.level < avg_enemy_level]

        free_ices.sort(key=lambda x: Get_turns_till_arrival(x, dest) * 0.9 + x.penguin_amount * 0.1)

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
            if g.source == ice:
                if worth_to_build_bridge(ice, g.destination):
                    create_bridge(ice, g.destination)


def _reinforce():
    global ice_data
    global front

    if Game.turn < 50 and bonus_map:
        return

    avg_amount = average_peng(my_icebergs)
    avg_enemy_level = avg_level(enemy_icebergs)

    free_ices = [ice for ice in my_icebergs if
                 ice_data[ice.unique_id]["acted"] not in ["Upgrade, Bridge"] and ice_data[ice.unique_id]["amount"] > 0]

    if circular:  # if the map is a circle,use the reinforce penguins to attack
        front = list(enemy_icebergs)

    if tricky:
        front = list(g.destination for g in enemy_penguin_groups if g.destination in my_icebergs)

    for ice in free_ices:

        if ice in front:
            continue

        if ice.level < avg_enemy_level:
            continue

        _amount = ice_data[ice.unique_id]["amount"]
        if _amount <= avg_amount and ice.level < level_limit(ice) * UPGRADE_FACTOR:
            continue

        front.sort(key=lambda x: Get_turns_till_arrival(ice, x))

        for f_ice in front:
            _amount -= _amount // len(free_ices)

            send_penguins(ice, f_ice, _amount, "reinforce")
            front.append(ice)
            break

    reach_max = []
    didnt_reach = []
    for ice in my_icebergs:
        if ice.penguin_amount == ice.max_penguins:
            reach_max.append(ice)
        else:
            didnt_reach.append(ice)

    if reach_max and didnt_reach:
        for ice in reach_max:
            dest = min(didnt_reach, key=lambda x: Get_turns_till_arrival(x, ice))
            send_penguins(ice, dest, ice.penguins_per_turn, "reinforce_max")


def create_bridge(ice, dest):
    global ice_data

    if not ice_data[ice.unique_id]["acted"] and ice.penguin_amount <= ice.bridge_cost:
        ice.create_bridge(dest)

        # update iceberg data
        ice_data[ice.unique_id]["amount"] -= Game.iceberg_bridge_cost
        ice_data[ice.unique_id]["acted"] = "Bridge"

        return True

    return False


def send_penguins(iceberg, target, amount, reason=""):
    # type: (Iceberg, Iceberg, int, bool) -> bool

    global ice_data

    if ice_data[iceberg.unique_id]["acted"] not in ["Upgrade", "Bridge"]:
        if ice_data[iceberg.unique_id][
            "amount"] >= amount:
            if iceberg.can_send_penguins(target, amount):
                iceberg.send_penguins(target, amount)

                ice_data[iceberg.unique_id]["amount"] -= amount
                ice_data[iceberg.unique_id]["acted"] = "Sending"

                if DEBUG:
                    print("{} Sent {} Penguins to {} - {}".format(iceberg.id, amount, target.id, reason))
                return True

    return False


def _bonus():
    global ice_data

    if not bonus_iceberg:
        return

    if (groups(bonus_iceberg, enemy_penguin_groups) or IceState(bonus_iceberg)[
        0] == enemy_player):  # or have_more_icebergs():
        for ice in my_icebergs:
            get_turns = Get_turns_till_arrival(ice, bonus_iceberg)
            d_owner, d_amount = IceState(bonus_iceberg, get_turns)[0:2]
            if d_owner != player and ice_data[ice.unique_id]["amount"] > d_amount and get_turns <= MAX_d // 2:
                send_penguins(ice, bonus_iceberg, d_amount + 1, "bonus")
                break


# ------------help functions------------#


# --------------neutral-----------------#

def get_best_natural_ice(my_ice):
    natural_ices_sent = [g.destination for g in my_penguin_groups]
    natural_ices_no_sent = [ice for ice in neutral_icebergs + future_enemy_icebergs if
                            not ice in natural_ices_sent and ice.penguin_amount < my_ice.max_penguins]

    for ice in natural_ices_sent:
        if ice is Iceberg and (
                calc_future_state[ice.unique_id]["owner"].equals(enemy_player) or calc_future_state[ice.unique_id][
            "amount"] < 2):
            return ice

    for ice in natural_ices_no_sent:
        groups = [g for g in enemy_penguin_groups if g.destination.equals(ice)]
        if default_map and groups and min(Turns_till_arrival(g) for g in groups) > Get_turns_till_arrival(my_ice, ice):
            natural_ices_no_sent.remove(ice)

    min_ice = neutral_icebergs[0]
    if natural_ices_no_sent:
        if bonus_map or extraFar_t:
            min_ice = min(natural_ices_no_sent, key=lambda ice: Get_turns_till_arrival(ice, my_ice))
        else:
            min_ice = min(natural_ices_no_sent,
                          key=lambda ice: (Get_turns_till_arrival(ice, my_ice) / ice.level, ice.penguin_amount))

    return min_ice


# --------------bridge-----------------#

def worth_to_build_bridge(source, dest):
    groupsList = [g for g in my_penguin_groups if g.source == source and g.destination == dest]
    avg_turns = avg_turns_till_arrival(groupsList)

    if dest in future_enemy_icebergs or groups(dest, my_penguin_groups) >= dest.penguin_amount > 10:
        if avg_turns / Game.iceberg_max_bridge_duration >= 0.4 and sum(
                g.penguin_amount for g in groupsList) > Game.iceberg_bridge_cost:
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
    global ice_data

    enemy_close = False
    for n in neighbors_map[ice.unique_id]:
        if n in future_enemy_icebergs:
            enemy_close = True

    if not enemy_close:
        return False

    if groups(ice, enemy_penguin_groups) >= ice_data[ice.unique_id]["amount"]:
        return False

    dis = Get_turns_till_arrival(ice, dest)
    for n in neutral_icebergs:

        if n.equals(bonus_iceberg):
            continue

        if Get_turns_till_arrival(ice, n) < dis:
            return False

    if avg_level(my_icebergs) < avg_level(enemy_icebergs) * UPGRADE_FACTOR:
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
            time = MAX_d

    curTime = 0
    for g in groups:
        if g.decoy:  # TODO: decoy always return false, need to change it
            continue
        turns_till_arrival = Turns_till_arrival(g)
        if owner != neutral_player and not ice.equals(bonus_iceberg) and amount < ice.max_penguins:
            amount += ((turns_till_arrival - curTime) * ice.level)
            amount = min(amount, ice.max_penguins)

        amount += g.penguin_amount if g.owner == owner else -g.penguin_amount
        if amount < 0:
            owner = g.owner
            amount *= -1
        if amount == 0:
            owner = neutral_player
        amount = min(amount, ice.max_penguins)
        curTime = turns_till_arrival

    if owner != neutral_player and not ice.equals(bonus_iceberg) and amount < ice.max_penguins:
        amount += ((time - curTime) * ice.level)
        amount = min(amount, ice.max_penguins)

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
    return float(sum_levels(icebergs)) / float(len(icebergs))


def find_free_amount(ice):
    '''
    Calculate the number of penguins that can act
    '''
    owner = ice.owner
    min_amount = amount = 1  # The minimum amount needs to owner the ice

    groups = [x for x in my_penguin_groups + enemy_penguin_groups if x.destination.equals(ice)]
    groups.sort(key=lambda gp: Turns_till_arrival(gp))

    curTime = 0
    for g in groups:
        if g.decoy:
            continue
        turns_till_arrival = Turns_till_arrival(g)
        if owner != neutral_player and not ice.equals(bonus_iceberg) and ice.penguin_amount < ice.max_penguins:
            amount += ((turns_till_arrival - curTime) * ice.level)
            amount = min(amount, ice.max_penguins)

        amount += g.penguin_amount if g.owner.equals(owner) else -g.penguin_amount

        if amount <= 0:
            min_amount += (-amount) + 1
            amount = 1

        min_amount = min(min_amount, ice.max_penguins)
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


def special_dest(ice):
    '''
    cases where the game map are unique, and unique destinations should be chosen
    '''
    global ice_data
    # tricky__map case

    if tricky:
        amount = groups(my_icebergs[0], enemy_penguin_groups)
        if amount:
            send_penguins(my_icebergs[0], enemy_icebergs[0], amount + 1)

        elif my_icebergs[0].penguin_amount > enemy_icebergs[0].penguin_amount:
            send_penguins(my_icebergs[0], enemy_icebergs[0], ice_data[my_icebergs[0].unique_id]["amount"],
                          "tricky_knockout")
            return

        if len(my_icebergs) == len(enemy_icebergs) == 1:
            e_ice, m_ice = enemy_icebergs[0], my_icebergs[0]
            dest = min(neutral_icebergs, key=lambda x: x.get_turns_till_arrival(m_ice))
            if 300 - Game.turn == Get_turns_till_arrival(m_ice, dest) / m_ice.bridge_speed_multiplier:
                m_ice.send_penguins(dest, dest.penguin_amount + 1)

                return

    # circle__map case
    if circular:
        amount = ice_data[ice.unique_id]["amount"]

        if have_more_icebergs():
            d = min(future_enemy_icebergs, key=lambda x: Get_turns_till_arrival(ice, x) + x.penguin_amount)
            if amount > d.penguin_amount > 4 and not groups(ice, enemy_penguin_groups):
                send_penguins(ice, d, d.penguin_amount, "circular_attack")
                return

            if sum(ice_data[i.unique_id]["amount"] for i in my_icebergs if i.penguin_amount > 5) + groups(d,
                                                                                                          my_penguin_groups) > \
                    IceState(d, avg_distance_from_others(d, my_icebergs))[1]:
                send_penguins(ice, d, ice_data[ice.unique_id]["amount"], "circular_attack")

        if not have_more_icebergs():
            return min(neutral_icebergs, key=lambda n: Get_turns_till_arrival(ice, n) + n.penguin_amount)

        d = min(neutral_icebergs, key=lambda n: Get_turns_till_arrival(ice, n))
        if Game.turn > 250 and len(my_icebergs) == len(enemy_icebergs) == 2:
            my_icebergs[0].send_penguins(d, my_icebergs[0].penguin_amount // 2)
            return
        if 300 - Game.turn == MIN_d:
            ice_data[ice.unique_id]["amount"] = ice.penguin_amount
            send_penguins(ice, d, d.penguin_amount + 1, "circular_attack")

    if two_circular:
        if neutral_icebergs:
            for ices in my_icebergs:
                if ice.penguin_amount > 5 and neutral_icebergs:
                    d = min(neutral_icebergs, key=lambda x: Get_turns_till_arrival(ice, x) + x.penguin_amount)
                    if not groups(d, my_penguin_groups):
                        ices.send_penguins(d, 2)

    if extraFar_t:
        if len(enemy_icebergs) <= 3 and len(my_icebergs) == 2:
            problem = [ice for ice in my_icebergs if groups(ice, enemy_penguin_groups)]
            if problem:
                my_icebergs[0].send_penguins(problem[0], my_icebergs[0].penguin_amount // 2)
            icess = [ice for ice in neutral_icebergs if ice.level == 3]
            d = min(icess, key=lambda x: Get_turns_till_arrival(my_icebergs[0], x))
            if d:
                if len(enemy_icebergs) == 3:
                    my_icebergs[0].send_penguins(d, my_icebergs[0].penguin_amount // 2)
                    my_icebergs[1].send_penguins(d, my_icebergs[1].penguin_amount)
                if my_icebergs[0].penguin_amount > 5 and not groups(my_icebergs[0], enemy_penguin_groups):
                    my_icebergs[0].send_penguins(my_icebergs[1], my_icebergs[0].penguin_amount // 2)
                if my_icebergs[1].penguin_amount > 5 and not groups(my_icebergs[1], enemy_penguin_groups):
                    my_icebergs[1].send_penguins(d, my_icebergs[1].penguin_amount)

        if Game.turn > 250 and have_more_icebergs:
            for ice in my_icebergs:
                d = min(enemy_icebergs, key=lambda x: Get_turns_till_arrival(ice, x))
                ice.send_penguins(d, ice.penguin_amount // 2)
        cool = [ice for ice in my_icebergs if ice.level >= 3]
        for ice in cool:
            d = min(enemy_icebergs, key=lambda x: Get_turns_till_arrival(ice, x))
            if ice_data[ice.unique_id]["amount"] > d.penguin_amount:
                ice.send_penguins(d, d.penguin_amount + Get_turns_till_arrival(ice, d) * d.penguins_per_turn)

    # Case #1: game starts where our ice and the enemy ice in the closest positions
    if len(my_icebergs) == len(enemy_icebergs) == 1:
        ice, enemyIce = my_icebergs[0], enemy_icebergs[0]
        if min_dis([ice], all_icebergs) == Get_turns_till_arrival(ice, enemyIce):

            if DEBUG:
                print("special case 1")
            if enemy_penguin_groups:
                ice.send_penguins(enemyIce, ice.penguin_amount)
            elif Game.turn > 100:
                # d=min(neutral_icebergs, key =lambda x: Get_turns_till_arrival(ice,x)+x.penguin_amount)
                ice.send_penguins(enemyIce, 2)
    if extraFar and len(enemy_icebergs) >= 2 and len(my_icebergs) == 1 and my_icebergs[0].penguin_amount == my_icebergs[
        0].max_penguins:
        my_icebergs[0].send_penguins(enemy_icebergs[0], my_icebergs[0].penguin_amount)
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
    for i in range(max(2, len(all_icebergs) // 5)):
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


def level_limit(ice):
    m, level = 0, 1
    while m <= ice.max_penguins:
        level += 1
        m = ice.upgrade_cost + ice.cost_factor * (level - ice.level - 1)
    return level


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

    set_ices = dfs(set(), mapping, my_icebergs[0])

    if (len(set_ices) / len(all_icebergs)) < 0.8:
        return False

    for neighbors in mapping.values():
        if len(neighbors) != 2:
            return False

    return True


def is_tricky_map():
    return len(all_icebergs) == 5


def is_bonus_map():
    return False
    # return max_dis(all_icebergs) != my_icebergs[0].get_turns_till_arrival(enemy_icebergs[0])


def is_extraFar_t():
    return [i for i in neutral_icebergs if i.level == 3] and MAX_d == my_icebergs[0].get_turns_till_arrival(
        enemy_icebergs[0])


def is_two_circular():
    if len(my_icebergs) == len(enemy_icebergs) == 1:
        if not [i for i in all_icebergs if i.level > 1]:
            return True
    return False


def is_extraFar():
    return min_dis([my_icebergs[0]], all_icebergs) == my_icebergs[0].get_turns_till_arrival(enemy_icebergs[0])


def find_map():
    global tricky
    global bonus_map
    global circular
    global two_circular
    global extraFar
    global default_map
    global extraFar_t

    tricky = is_tricky_map()
    bonus_map = is_bonus_map()
    circular = is_circular()
    extraFar = is_extraFar()
    extraFar_t = is_extraFar_t()
    two_circular = is_two_circular()

    if not (tricky or bonus_map or circular or two_circular or extraFar or extraFar_t):
        default_map = True

    if DEBUG:
        if tricky:
            print("tricky")
        if circular:
            print("circular")
        if two_circular:
            print("two_circular")
        if bonus_map:
            print("bonus_map")
        if extraFar_t:
            print("extraFar_t")
        if extraFar:
            print("extraFar")
        if default_map:
            print("default_map")

