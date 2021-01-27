"""
This is an example for a bot.
"""
from penguin_game import *


# check if t is safe for us to upgrade instead of send penguins
def canUpgrade(game, my_iceberg):
    if len(game.get_enemy_icebergs()) > len(game.get_my_icebergs()):
        return False
    if len(game.get_my_penguin_groups()) <= len(game.get_my_penguin_groups()):
        return False
    return True


def groups(ice, group):
    count = 0
    for x in group:
        if x.destination == ice:
            count += x.penguin_amount
    return count


# check if the iceberg will stay netural or not.
def willStayNeutral(game, iceberg, my_iceberg):
    turn_till_arrivial = my_iceberg.get_turns_till_arrival(iceberg)
    for ei in game.get_enemy_icebergs():
        ei_amount = ei.penguin_amount + (turn_till_arrivial * iceberg.penguins_per_turn)
        if ei_amount >= (ei.get_turns_till_arrival(iceberg) * iceberg.penguins_per_turn):
            return False
    return True


def do_turn(game):
    """
    Makes the bot run a single turn.

    :param game: the current game state.
    :type game: Game
    """
    # Go over all of my icebergs.

    for my_iceberg in game.get_my_icebergs():
        my_penguin_amount = my_iceberg.penguin_amount  # type: int
        neturalSorted = sorted(game.get_neutral_icebergs(), key=lambda x: my_iceberg.get_turns_till_arrival(x))
        enemySorted = sorted(game.get_enemy_icebergs(), key=lambda x: my_iceberg.get_turns_till_arrival(x))
        if game.get_neutral_icebergs():
            neutral1 = neturalSorted[0]
        if game.get_enemy_icebergs():
            enemy1 = enemySorted[0]

        # closest neutral iceberg target
        """if game.get_neutral_icebergs():
            for ns in neturalSorted:
                if  willStayNeutral(game, ns, my_iceberg):
                    game.get_enemy_icebergs()[0] = ns
                    break"""

        if game.get_neutral_icebergs() and game.get_enemy_icebergs() and my_iceberg.get_turns_till_arrival(
                neutral1) < my_iceberg.get_turns_till_arrival(enemy1):
            if groups(neturalSorted[0], game.get_my_penguin_groups()) >= 11 and game.turn < 37:
                destination = neturalSorted[1]

            else:
                destination = neturalSorted[0]
            # The amount of penguins the target will have.

            if game.turn < 25 or game.turn % 5 == 0:
                destination_penguin_amount = destination.penguin_amount
            else:
                destination_penguin_amount = destination.penguin_amount // 3

        elif game.get_enemy_icebergs():
            destination = enemySorted[0]
            destination_penguin_amount = destination.penguin_amount // 2  # type: int
        else:
            destination = neturalSorted[0]
            destination_penguin_amount = destination.penguin_amount // 2
        if groups(my_iceberg, game.get_enemy_penguin_groups()) > my_iceberg.penguin_amount:
            s = True
        elif my_iceberg.level < 2 and my_iceberg.can_upgrade():  # if it safe, upgrade.
            print(
            my_iceberg, "upgrade to level ", my_iceberg.level)
            my_iceberg.upgrade()

            # If my iceberg has more penguins than the target iceberg.
        else:
            print(
            my_iceberg, "sends", (destination_penguin_amount + 1), "penguins to", destination)
            my_iceberg.send_penguins(destination, destination_penguin_amount + 1)

            """elif len(game.get_enemy_icebergs())>len(game.get_my_icebergs()):
            lst=sorted(game.get_all_icebergs(),key=lambda x: my_iceberg.get_turns_till_arrival(x))
            destination=lst[0]
            destination_penguin_amount=destination.penguin_amount//4"""