"""
This is an example for a bot.
"""
from penguin_game import *


def do_turn(game):
    """
    Makes the bot run a single turn.
    :param game: the current game state.
    :type game: Game
    """

    listhelp = []
    # Go over all of my icebergs.
    for my_iceberg in game.get_my_icebergs():
        flag = False
        distance1 = 300
        # The amount of penguins in my iceberg.
        if my_iceberg.level < 2:
            my_iceberg.upgrade()
        else:
            my_penguin_amount = my_iceberg.penguin_amount  # type: int

            # If there are any neutral icebergs.
            if game.get_neutral_icebergs():
                # Target a neutral iceberg.
                for iceberg in game.get_neutral_icebergs():
                    d = iceberg
                    distance = my_iceberg.get_turns_till_arrival(iceberg)
                    if len(game.get_my_icebergs()) < 3:
                        if game.get_my_penguin_groups():
                            for t in game.get_my_penguin_groups():
                                if t.source.equals(my_iceberg) and t.destination not in game.get_my_icebergs():
                                    d = t.destination
                                    break
                            # s=not(game.get_my_penguin_groups()[0].source.equals(my_iceberg))
                        else:
                            d = my_iceberg
                        if distance < distance1 and not (d.equals(iceberg)):
                            distance1 = distance
                            destination = iceberg
                            flag = True
                            destination_penguin_amount = destination.penguin_amount  # type: int
                    else:
                        flag = True
                        for iceberg in game.get_neutral_icebergs():
                            distance = my_iceberg.get_turns_till_arrival(iceberg)
                            # Will attack the icebergs we can conquer the fastest, according to the distance and amount of penguins on the icebergs.
                            if distance + iceberg.penguin_amount < distance1:
                                distance1 = distance
                                destination = iceberg
                        # The number of penguins in the destination also depends on the growth rate of the penguins and the amount of turns until we reach the destination.
                        destination_penguin_amount = destination.penguin_amount
            else:
                s = True
                # Target an enemy iceberg.
                for iceberg in game.get_enemy_icebergs():
                    distance = my_iceberg.get_turns_till_arrival(iceberg)
                    # Will attack the icebergs we can conquer the fastest, according to the distance and amount of penguins on the icebergs.
                    if distance < distance1:
                        distance1 = distance
                        destination = iceberg
                # The number of penguins in the destination also depends on the growth rate of the penguins and the amount of turns until we reach the destination.
                destination_penguin_amount = destination.penguin_amount + destination.get_turns_till_arrival(
                    my_iceberg) * destination.penguins_per_turn  # type: int
                flag = True

            # The amount of penguins the target has.

            # Send penguins to the ta:
            if flag:
                print(
                my_iceberg, "sends", (destination_penguin_amount + 1), "penguins to", destination)
                my_iceberg.send_penguins(destination, destination_penguin_amount + 1)
            # listhelp.append(destination)