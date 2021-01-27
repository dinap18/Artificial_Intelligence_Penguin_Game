"""
This is an example for a bot.
"""
from penguin_game import *


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

        if game.get_neutral_icebergs() and game.get_enemy_icebergs() and my_iceberg.get_turns_till_arrival(
                neutral1) < my_iceberg.get_turns_till_arrival(enemy1):
            if groups(neturalSorted[0], game.get_my_penguin_groups()) >= 11 and game.turn < 25:
                destination = neturalSorted[1]

            else:
                destination = neturalSorted[0]
            # The amount of penguins the target will have.

            if game.turn < 25 or game.turn % 5 == 0:
                destination_penguin_amount = destination.penguin_amount
            else:
                destination_penguin_amount = destination.penguin_amount // 3

        elif game.get_enemy_icebergs() and game.turn % 10 != 0:
            destination = enemySorted[0]
            destination_penguin_amount = destination.penguin_amount // 2  # type: int
        elif game.get_neutral_icebergs():
            destination = neturalSorted[0]
            destination_penguin_amount = destination.penguin_amount // 3
        else:
            destination = enemySorted[0]
            destination_penguin_amount = destination.penguin_amount // 2  # type: int
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
