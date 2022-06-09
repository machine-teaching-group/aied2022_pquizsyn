from stanfordkarel import *


def main():
    """ Karel code goes here! """
    def turn_right():
        turn_left()
        turn_left()
        turn_left()

    turn_right()
    move()
    turn_left()

if __name__ == "__main__":
    run_karel_program()