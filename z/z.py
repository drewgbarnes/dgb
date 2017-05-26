import turtle
import time
import random

MOVE_DISTANCE = 7
EDGE_BUFFER = 15

_turtles = []
t = turtle.Turtle()
t.shapesize(2, 2)
t.shape('square')
t.left(90)
screen = t.screen


def up():
    amount_to_move = t.ycor() + MOVE_DISTANCE
    if is_valid_move('up', amount_to_move):
        t.sety(amount_to_move)


def down():
    amount_to_move = t.ycor() - MOVE_DISTANCE
    if is_valid_move('down', amount_to_move):
        t.sety(amount_to_move)


def left():
    amount_to_move = t.xcor() - MOVE_DISTANCE
    if is_valid_move('left', amount_to_move):
        t.setx(amount_to_move)


def right():
    amount_to_move = t.xcor() + MOVE_DISTANCE
    if is_valid_move('right', amount_to_move):
        t.setx(amount_to_move)


def is_valid_move(direction, amount_to_move):
    if direction == 'right' or direction == 'left':
        boundary = screen.window_width()
    elif direction == 'up' or direction == 'down':
        boundary = screen.window_height()

    print(amount_to_move)
    print(boundary)
    if abs(amount_to_move) >= boundary / 2 - EDGE_BUFFER:
        return False

    return True


def shoot1():
	bullet1 = turtle.Turtle(shape='circle')
	bullet1.penup()
	bullet1.seth(bullet1.towards(screen.))


def init(screen):
    screen.onkey(up, 'w')
    screen.onkey(down, 's')
    screen.onkey(left, 'a')
    screen.onkey(right, 'd')
    screen.onkey(shoot1, 'o')
    screen.listen()


def main(screen):
    init(screen)
    while True:
        screen.update()

main(screen)
