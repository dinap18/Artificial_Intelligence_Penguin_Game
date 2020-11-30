"""
This is an example for a bot.
"""
from penguin_game import *

# keren or hadad
"""
The current bot wins all the first five stages.
"""


def do_turn(game):
    """
    Makes the bot run a single turn.
    :param game: the current game state.
    :type game: Game
    """

    """
    We'll get to the point where our first iceberg has a Level 2 upgrade
    """
    if game.get_my_icebergs()[0].level < 2:
        game.get_my_icebergs()[0].upgrade()
        return

    # Go over all of my icebergs.
    for my_iceberg in game.get_my_icebergs():

        """
        We will initialize our flag to "True".
        Every time an iceberg in the game comes under our control - 
        we will make sure it is upgraded to level 2.
        """

        flag = True

        if my_iceberg.level < 2:
            my_iceberg.upgrade()
            flag = False

        if flag == True:
            # The amount of penguins in my iceberg.
            my_penguin_amount = my_iceberg.penguin_amount  # type: int

            destination = my_iceberg

            # a very big number

            amount = 9999

            # saves in a list the iceberg that its the most effective to capture
            lst = []

            """
            We go through all the icebergs there are and we want to know which iceberg is best for us to reach. 
            So we check out how many penguins there are already on the iceberg we're going to conquer. 
            We add to that how many turns it will take us and how effective it is for us.We consider the number of turns,
            the number of penguins and the level to decide what is the best step to take.
            """
            for ke in game.get_neutral_icebergs():
                lst += [(ke, ke.penguin_amount, my_iceberg.get_turns_till_arrival(ke), ke.level)]

            for ke in game.get_enemy_icebergs():
                lst += [(ke, ke.penguin_amount, my_iceberg.get_turns_till_arrival(ke), ke.level)]

            for i in lst:
                temp = i[1] + i[2] * i[3]
                if temp < amount:
                    amount = temp
                    destination = i[0]

            destination_penguin_amount = amount

            # checks if my iceberg needs to be saved and not to send pengiuns out to other icebergs
            for group in game.get_enemy_penguin_groups():
                if group.destination == my_iceberg:
                    if group.penguin_amount > my_iceberg.penguin_amount + my_iceberg.level * group.turns_till_arrival - amount:
                        flag = False

            if flag == True:
                # If my iceberg has more penguins than the target iceberg.
                if my_penguin_amount > destination_penguin_amount:
                    # Send penguins to the target.
                    print(
                    my_iceberg, "sends", (destination_penguin_amount + 1), "penguins to", destination)
                    my_iceberg.send_penguins(destination, destination_penguin_amount + 1)