"""
This is an example for a bot.
"""
from penguin_game import *


def groupsize(groups):
    sum = 0
    for x in groups:
        sum += x.penguin_amount
    return sum // len(groups)


def groups(ice, group):
    count = 0
    for x in group:
        if x.destination == ice:
            count += x.penguin_amount
    return count


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
        mySorted=sorted(game.get_my_icebergs(), key=lambda x: my_iceberg.get_turns_till_arrival(x))
        bonusSorted=sorted(game.get_my_icebergs(), key=lambda x: x.get_turns_till_arrival(game.get_bonus_iceberg()))
        y = 1
        if game.get_enemy_penguin_groups():
            g = groupsize(game.get_enemy_penguin_groups())
            y = my_iceberg.penguin_amount // g if 3< g < my_iceberg.penguin_amount else 1

        if game.get_neutral_icebergs():
            neutral = neturalSorted[0]
        if game.get_enemy_icebergs():
            enemy = enemySorted[0]

        bonus = 0
        if game.get_bonus_iceberg().owner == game.get_enemy() and game.get_bonus_iceberg().turns_left_to_bonus == 1:
            bonus = game.get_bonus_iceberg().penguin_bonus

        if game.get_neutral_icebergs() and game.get_enemy_icebergs() and my_iceberg.get_turns_till_arrival(
                neutral) < my_iceberg.get_turns_till_arrival(enemy) and game.turn%14!=0 :
            if groups(neutral, game.get_my_penguin_groups()) and game.turn < 21:
                neutral = neturalSorted[1]

            destination = neutral
            # The amount of penguins the target will have.

            if game.turn < 30 or game.turn % 5 == 0:
                destination_penguin_amount = destination.penguin_amount
            else:
                destination_penguin_amount = destination.penguin_amount //y

        elif game.get_enemy_icebergs() and game.turn % 17 != 0:
            destination = enemySorted[0]
            destination_penguin_amount = destination.penguin_amount // y -2 # + bonus # type: int
        elif game.get_neutral_icebergs():
            destination = neturalSorted[0]
            destination_penguin_amount = destination.penguin_amount // y
        else:
            destination = enemySorted[0]
            if game.turn % 5 != 0:
                destination_penguin_amount = destination.penguin_amount // y -2 # +bonus # type: int
            else:
                destination_penguin_amount = destination.penguin_amount // y #+ bonus


        #if destination_penguin_amount<0:
            #destination_penguin_amount*=-1
        if groups(my_iceberg, game.get_enemy_penguin_groups()) > my_iceberg.penguin_amount - destination_penguin_amount :
            continue
        #game.get_bonus_iceberg().owner == game.get_myself() and
        elif  ( game.get_neutral_bonus_iceberg() and game.turn>= 61 ) or (
        groups(game.get_bonus_iceberg(),game.get_enemy_penguin_groups())>=game.get_bonus_iceberg().penguin_amount) and my_iceberg in bonusSorted[0: len(bonusSorted)//2]:
            my_iceberg.send_penguins(game.get_bonus_iceberg(),destination_penguin_amount+1 )

        elif ( my_iceberg.level < 2 and my_iceberg.can_upgrade() ) or ( my_iceberg.can_upgrade() and game.turn% 10==0) :  # if it safe, upgrade.
            my_iceberg.upgrade()

        elif groups(mySorted[0],game.get_enemy_penguin_groups())>mySorted[0].penguin_amount+groups(mySorted[0],game.get_my_penguin_groups()):
            print(my_iceberg, "sends", (destination_penguin_amount + 1), "penguins to", destination)
            my_iceberg.send_penguins(mySorted[0], destination_penguin_amount + 1)

        else:

            print(
            my_iceberg, "sends", (destination_penguin_amount + 1), "penguins to", destination)
            my_iceberg.send_penguins(destination, destination_penguin_amount + 1)
        
