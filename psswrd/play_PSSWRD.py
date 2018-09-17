import itertools
import random


def tell_positions(psswrd, guess, place_limit):
    # returns (# in correct position, #in incorrect position)
    position = 0
    number = 0
    for i in range(place_limit):
        if guess[i] == psswrd[i]:
            position += 1
    for g in guess:
        if g in psswrd:
            number += 1
    print("{},{}".format(position, number - position))

def get_guess():
  while True:
    user_input = raw_input('enter format as `0123`: ')
    try:
      guess = [int(i) for i in user_input]
      return guess
    except:
      print('try again:')
      pass

def gen_psswrd(character_limit, place_limit):
  all_psswrds = []
  for i in itertools.permutations(range(character_limit), r=place_limit):
      all_psswrds.append(list(i))

  random_index = random.randint(0, len(all_psswrds) - 1)
  psswrd = all_psswrds.pop(random_index)
  return psswrd

def play():
  guess_limit = 10 # gl
  place_limit = 4 # pl
  psswrd = gen_psswrd(guess_limit, place_limit)
  for i in range(guess_limit):
    guess = get_guess()
    if guess == psswrd:
      print('YOU WIN')
      return

    tell_positions(psswrd, guess, place_limit)
    print('guesses remaining: {}'.format(guess_limit-i-1))
  print('YOU LOSE')
  print('PSSWRD: {}'.format(psswrd))

play()
