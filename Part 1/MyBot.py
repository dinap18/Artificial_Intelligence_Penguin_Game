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

    # upgrade

    if game.get_my_icebergs()[0].level < 4 and not (game.turn > 8 and len(game.get_enemy_penguin_groups()) > 0):
        game.get_my_icebergs()[0].upgrade()
        return
    weight = 0.5
    # Go over all of my icebergs.
    for my_iceberg in game.get_my_icebergs():
        if my_iceberg.level < 2 and len(game.get_neutral_icebergs()) > len(game.get_enemy_icebergs()):
            my_iceberg.upgrade()
            return
        # The amount of penguins in my iceberg.
        my_penguin_amount = my_iceberg.penguin_amount  # type: int

        # If there are any neutral icebergs.
        if game.get_neutral_icebergs():
            # Target a neutral iceberg.
            distance1 = 300
            for iceberg in game.get_neutral_icebergs():
                distance = my_iceberg.get_turns_till_arrival(iceberg)
                if distance < distance1:
                    distance1 = distance
                    destination = iceberg
            destination_penguin_amount = destination.penguin_amount + 1  # type: int
        # destination = game.get_neutral_icebergs()[0]  # type: Iceberg
        else:
            # Target an enemy iceberg.
            distance1 = 300
            for iceberg in game.get_enemy_icebergs():
                distance = my_iceberg.get_turns_till_arrival(iceberg)
                if weight * distance + (1 - weight) * iceberg.penguin_amount < distance1:
                    distance1 = distance
                    destination = iceberg
            destination_penguin_amount = destination.penguin_amount + destination.get_turns_till_arrival(
                my_iceberg) * destination.penguins_per_turn  # type: int
            # destination = game.get_enemy_icebergs()[0]  # type: Iceberg

        # If my iceberg has more penguins than the target iceberg.
        if my_penguin_amount > destination_penguin_amount:
            # Send penguins to the target.
            print (my_iceberg, "sends", (destination_penguin_amount + 1), "penguins to", destination)
        my_iceberg.send_penguins(destination, destination_penguin_amount + 1)
        # If my iceberg has less penguins than the target iceberg.
        """elif my_penguin_amount*2 > destination_penguin_amount:
            counter=0
            sortedIceberg=sorted(game.get_my_icebergs(),key= lambda x: x.get_turns_till_arrival(destination) )
            for my_iceberg1 in sortedIceberg:
                if counter > destination_penguin_amount:
                    break
                counter+= my_iceberg1.penguin_amount
                print my_iceberg1, "sends", (my_iceberg1.penguin_amount+1 ), "penguins to", destination
                my_iceberg1.send_penguins(destination, my_iceberg1.penguin_amount +1)  """