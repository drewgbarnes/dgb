import random
import itertools
from tqdm import *


def printt(content):
    if TEST:
        print(content)


def check(guess, psswrd, pl):
    # returns (# in correct position, #in incorrect position)
    if guess == psswrd:
        return pl, 0
    position = 0
    number = 0
    for i in range(pl):
        if guess[i] == psswrd[i]:
            position += 1
    for g in guess:
        if g in psswrd:
            number += 1
    return position, number - position


def manual_check(guess):
    print('current guess:')
    print(guess)
    while True:
        vals = raw_input(
            'enter format as `correct_position,incorrect_position`: ').split(',')
        try:
            x, y = int(vals[0]), int(vals[1])
            return x, y
        except:
            print('try again:')
            pass


def replaceone(guess, possible, correct, incorrect, pl):
    ind = 0
    other = False
    guy = possible[ind]
    while guy in guess:
        ind += 1
        try:
            guy = possible[ind]
        except:
            ind = 0
            guy = correct[ind]
            while guy in guess:
                ind += 1
                guy = correct[ind]

    guess.append(guy)
    for i in range(pl):
        if guess[i] in incorrect:
            return guess.pop(i)

    return guess.pop(0)


def keepcorrect_replaceone(guess, possible, correct, incorrect, pl):
    guess_copy = list(guess)

    for i in guess_copy:
        if i in correct:
            guess.remove(i)

    for i in guess_copy:
        if i in incorrect:
            guess.remove(i)

    for i in possible:
        if i not in guess:
            guess.append(i)
            break

    for i in guess:
        if i not in correct:
            guy = i
            break

    guess.remove(guy)

    guess = list(correct) + guess

    glen = pl-len(guess)

    while glen > 0:
        for i in possible:
            if i not in guess:
                guess.append(i)
                glen -= 1
                break

    return guy, guess

# high score 4416 4728

def remove_poss(poss_ans, guess, correct, incorrect, pairs):

    items = list(poss_ans)
    for an in items:
        if set(guess) == set(an):
            poss_ans.remove(an)
        for i in correct:
            if i not in an and an in poss_ans:
                poss_ans.remove(an)

        for i in incorrect:
            if i in an and an in poss_ans:
                 poss_ans.remove(an)

    poss_ans = reduce_possibilities(guess, pairs, poss_ans)

    printt('# poss: ' + str(len(poss_ans)))
    if len(poss_ans) < 10:
        printt(poss_ans)

    return poss_ans


def find_numbers2(psswrd, game_length, psswrd_length, poss_ans):
    possible_numbers = list(range(game_length))
    guess = possible_numbers[:psswrd_length]
    possible_numbers.reverse()  # only increases winrate for this one 3%
    correct_numbers = []
    incorrect_numbers = []
    popped = []
    pairs = {}
    position_pairs = {}

    guesses = 0

    if not INTERACTIVE:
        printt('current guess: ' + str(guess))
        printt('psswrd: ' + str(psswrd))

    while guesses < (game_length - 1):
        if INTERACTIVE:
            position, number = manual_check(guess)
        else:
            position, number = check(guess, psswrd, psswrd_length)
        if position == psswrd_length:
            return 1, guesses, position_pairs, correct_numbers
        total = position + number
        guesses += 1

        if (position, number) in position_pairs:
            position_pairs[(position, number)] = position_pairs[
                (position, number)] + [str(guess)]
        else:
            position_pairs[(position, number)] = [str(guess)]

        if total in pairs:
            pairs[total] = pairs[total] + [str(guess)]
        else:
            pairs[total] = [str(guess)]

        correct_numbers, possible_numbers = check_pairs(
            pairs, correct_numbers, incorrect_numbers, possible_numbers, guess, total, psswrd_length)

        flag = False

        if total == psswrd_length:
            correct_numbers = guess
            printt('current correct: ' + str(correct_numbers))
            if set(correct_numbers) != set(psswrd) and not INTERACTIVE:
                print('BADBADBADBADBADBADBADBADBADBAD')
                print('psswrd: ' + str(psswrd))
            return 1, guesses, position_pairs, correct_numbers

        elif guesses != 1 and special:
            if len(correct_numbers) > psswrd_length-1:
                printt('current correct: ' + str(correct_numbers))
                if set(correct_numbers) != set(psswrd) and not INTERACTIVE:
                    print('BADBADBADBADBADBADBADBADBADBAD')
                    print('psswrd: ' + str(psswrd))
                return 1, guesses, position_pairs, correct_numbers

            if last_total != total:
                if last_total > total:
                    if popped not in correct_numbers:
                        correct_numbers.append(popped)

                    if guess[-1] not in incorrect_numbers:
                        incorrect_numbers.append(guess[-1])
                    flag = True
                else:
                    if popped not in incorrect_numbers:
                        incorrect_numbers.append(popped)

                    if guess[-1] not in correct_numbers:
                        correct_numbers.append(guess[-1])

                if popped in possible_numbers:
                    possible_numbers.remove(popped)
                if guess[-1] in possible_numbers:
                    possible_numbers.remove(guess[-1])
            else:
                if popped in correct_numbers:
                    # this brings the winrate up 6%
                    if guess[-1] not in correct_numbers:
                        correct_numbers.append(guess[-1])
                        flag = True
                    if guess[-1] in possible_numbers:
                        possible_numbers.remove(guess[-1])
                elif popped in incorrect_numbers:
                    # this brings the winrate up 2.5%
                    if guess[-1] not in incorrect_numbers:
                        incorrect_numbers.append(guess[-1])
                    if guess[-1] in possible_numbers:
                        possible_numbers.remove(guess[-1])
                elif len(correct_numbers) == psswrd_length - 1 and total == psswrd_length - 1:
                    if guess[-1] not in incorrect_numbers:
                        incorrect_numbers.append(guess[-1])
                    if guess[-1] in possible_numbers:
                        possible_numbers.remove(guess[-1])
                    if popped not in incorrect_numbers:
                        incorrect_numbers.append(popped)
                    if popped in possible_numbers:
                        possible_numbers.remove(popped)

            # this appears to bring the winrate up 4%
            if total == 0:
                special = False
                for i in guess:
                    if i in possible_numbers:
                        possible_numbers.remove(i)
                    if i not in incorrect_numbers:
                        incorrect_numbers.append(i)

            popped, guess = keepcorrect_replaceone(
                guess, possible_numbers, correct_numbers, incorrect_numbers, psswrd_length)

        else:
            # first guess contained no correct answers
            if total == 0:
                for i in range(psswrd_length):
                    possible_numbers.remove(guess[i])
                    incorrect_numbers.append(guess[i])
                for i in range(psswrd_length):
                    guess[i] = possible_numbers[i]
                special = False
            else:
                popped, guess = keepcorrect_replaceone(
                    guess, possible_numbers, correct_numbers, incorrect_numbers, psswrd_length)
                special = True

        last_position = position
        last_number = number
        last_total = last_position + last_number
        if flag:
            last_total += 1

        #this is very weird
        if psswrd_length == 5:
            possible_numbers.append(possible_numbers.pop(0))

        if not INTERACTIVE:
            for i in incorrect_numbers:
                if i in psswrd:
                    print('BADBADBADBADBADBADBADBADBADBAD')

            for i in correct_numbers:
                if i not in psswrd:
                    print('BADBADBADBADBADBADBADBADBADBAD')

        if len(possible_numbers) + len(correct_numbers) == psswrd_length:
            correct_numbers = correct_numbers + possible_numbers
            printt('current correct: ' + str(correct_numbers))
            if set(correct_numbers) != set(psswrd) and not INTERACTIVE:
                print('BADBADBADBADBADBADBADBADBADBAD')
            return 1, guesses, position_pairs, correct_numbers

        if len(correct_numbers) > psswrd_length - 1:
            printt('current correct: ' + str(correct_numbers))
            if set(correct_numbers) != set(psswrd) and not INTERACTIVE:
                print('BADBADBADBADBADBADBADBADBADBAD')
            return 1, guesses, position_pairs, correct_numbers

        printt(
            '--------------------------------------\nguesses made: ' + str(guesses))
        printt('current position: ' + str(position) +
               ' current number: ' + str(number))
        printt('possible_numbers: ' + str(possible_numbers))
        printt('incorrect_numbers: ' + str(incorrect_numbers))
        printt('current correct: ' + str(correct_numbers))

        if not INTERACTIVE:
            printt('current guess: ' + str(guess))
            printt('psswrd: ' + str(psswrd))
        else:
            ans, not_ans = find_positions(correct_numbers, position_pairs)
            print('ans:' + str(ans))
            print('not_ans: ' + str(not_ans))

        # poss_ans = remove_poss(poss_ans, guess, correct_numbers, incorrect_numbers, position_pairs)

    return 0, guesses, position_pairs, correct_numbers


def check_pairs(pairs, correct, incorrect, possible, guess, total, pl):

    if pl == 4:
        # this brings the winrate up 5%
        if 2 in pairs:
            if len(pairs[2]) > 1:
                for pair in itertools.combinations(pairs[2], r=2):
                    first = eval(pair[0])
                    second = eval(pair[1])
                    if len(set(first).union(set(second))) == 8:
                        for p in possible:
                            if p not in first and p not in second:
                                possible.remove(p)
            for f in pairs[2]:
                second = eval(f)
                barfcount = 0
                for ok in correct:
                    if ok in second:
                        barfcount += 1
                if barfcount == 2:
                    for no in second:
                        if no not in correct and no in possible:
                            possible.remove(no)

        # this brings the winrate up 4%
        if 3 in pairs:
            if 1 in pairs:
                for f in pairs[1]:
                    for s in pairs[3]:
                        first = eval(f)
                        second = eval(s)
                        if len(set(first).union(set(second))) == 8:
                            for p in possible:
                                if p not in first and p not in second:
                                    possible.remove(p)
                    # brings up winrate and reduces avg guesses
                    first = eval(f)
                    barf = False
                    for ok in correct:
                        if ok in first:
                            barf = True
                    if barf:
                        for no in first:
                            if no not in correct and no in possible:
                                possible.remove(no)

            if len(correct) == 3:
                # very slightly decreases avg guesses
                for f in pairs[3]:
                    g = eval(f)
                    if set(correct) < set(g):
                        for i in g:
                            if i not in correct:
                                if i in possible:
                                    possible.remove(i)

        # this brings the winrate up 5%
        for t in pairs:
            for g in pairs[t]:
                bad_count = 0
                items = list(eval(g))
                for i in items:
                    if i in incorrect:
                        bad_count += 1
                        items.remove(i)
                if bad_count == pl-t:
                    for c in items:
                        if c not in correct:
                            correct.append(c)

        if len(correct) == pl-1 and total == pl-1:
            cor_num = 0
            for i in guess:
                if i in correct:
                    cor_num += 1
            if cor_num < pl-1:
                possible_numbers_copy = list(possible)
                for i in possible_numbers_copy:
                    if i not in guess:
                        possible.remove(i)

    elif pl == 5:
        if 3 in pairs:
            if 2 in pairs:
                for f in pairs[2]:
                    for s in pairs[3]:
                        first = eval(f)
                        second = eval(s)
                        if len(set(first).union(set(second))) == 10:
                            for p in possible:
                                if p not in first and p not in second:
                                    possible.remove(p)

        if 4 in pairs:
            if 1 in pairs:
                for f in pairs[1]:
                    for s in pairs[4]:
                        first = eval(f)
                        second = eval(s)
                        if len(set(first).union(set(second))) == 10:
                            for p in possible:
                                if p not in first and p not in second:
                                    possible.remove(p)

        if 1 in pairs:
            for f in pairs[1]:
                first = eval(f)
                barf = False
                for ok in correct:
                    if ok in first:
                        barf = True
                if barf:
                    for no in first:
                        if no not in correct and no in possible:
                            possible.remove(no)

        if 4 in pairs:
            if len(correct) == pl-1:
                for f in pairs[4]:
                    g = eval(f)
                    if set(correct) < set(g):
                        for i in g:
                            if i not in correct:
                                if i in possible:
                                    possible.remove(i)

        # if total == len(correct):
        #     if set(correct) < set(guess):
        #         for i in guess:
        #             if i not in correct:
        #                 if i in possible:
        #                     possible.remove(i)

    return correct, possible

# high score 4968


def find_numbers(psswrd, game_length, psswrd_length, poss_ans):
    possible_numbers = list(range(game_length))
    guess = possible_numbers[:psswrd_length]
    correct_numbers = []
    incorrect_numbers = []
    popped = []
    pairs = {}
    position_pairs = {}

    guesses = 0

    if not INTERACTIVE:
        printt('current guess: ' + str(guess))
        printt('psswrd: ' + str(psswrd))

    while guesses < (game_length - 1):
        if INTERACTIVE:
            position, number = manual_check(guess)
        else:
            position, number = check(guess, psswrd, psswrd_length)
        if position == psswrd_length:
            return 1, guesses, position_pairs, guess
        total = position + number
        guesses += 1

        if total == 3 and len(possible_numbers) == 2:
            if set(correct_numbers) < set(guess):
                for g in guess:
                    if g in possible_numbers:
                        possible_numbers.remove(g)

        if len(possible_numbers) + len(correct_numbers) == psswrd_length:
            correct_numbers = correct_numbers + possible_numbers
            printt('current correct: ' + str(correct_numbers))
            if set(correct_numbers) != set(psswrd) and not INTERACTIVE:
                print('BADBADBADBADBADBADBADBADBADBAD')
                print('psswrd: ' + str(psswrd))
            return 1, guesses, position_pairs, correct_numbers

        if (position, number) in position_pairs:
            position_pairs[(position, number)] = position_pairs[
                (position, number)] + [str(guess)]
        else:
            position_pairs[(position, number)] = [str(guess)]

        if total in pairs:
            pairs[total] = pairs[total] + [str(guess)]
        else:
            pairs[total] = [str(guess)]

        if total == psswrd_length:
            correct_numbers = guess
            printt('current correct: ' + str(correct_numbers))
            if set(correct_numbers) != set(psswrd) and not INTERACTIVE:
                print('BADBADBADBADBADBADBADBADBADBAD')
                print('psswrd: ' + str(psswrd))
            return 1, guesses, position_pairs, correct_numbers

        elif guesses != 1 and special:
            if len(possible_numbers) + len(correct_numbers) == psswrd_length:
                correct_numbers = possible_numbers + correct_numbers
                printt('current correct: ' + str(correct_numbers))
                if set(correct_numbers) != set(psswrd) and not INTERACTIVE:
                    print('BADBADBADBADBADBADBADBADBADBAD')
                    print('psswrd: ' + str(psswrd))
                return 1, guesses, position_pairs, correct_numbers

            if last_total != total:
                if last_total > total:
                    if popped not in correct_numbers:
                        correct_numbers.append(popped)

                    if guess[-1] not in incorrect_numbers:
                        incorrect_numbers.append(guess[-1])
                else:
                    if popped not in incorrect_numbers:
                        incorrect_numbers.append(popped)

                    if guess[-1] not in correct_numbers:
                        correct_numbers.append(guess[-1])

                if popped in possible_numbers:
                    possible_numbers.remove(popped)
                if guess[-1] in possible_numbers:
                    possible_numbers.remove(guess[-1])
            else:
                if popped in correct_numbers:
                    # this brings the winrate up 6%
                    if guess[-1] not in correct_numbers:
                        correct_numbers.append(guess[-1])
                    if guess[-1] in possible_numbers:
                        possible_numbers.remove(guess[-1])
                elif popped in incorrect_numbers:
                    # this brings the winrate up 2.5%
                    if guess[-1] not in incorrect_numbers:
                        incorrect_numbers.append(guess[-1])
                    if guess[-1] in possible_numbers:
                        possible_numbers.remove(guess[-1])
                elif len(correct_numbers) == psswrd_length - 1 and total == psswrd_length - 1:
                    if guess[-1] not in incorrect_numbers:
                        incorrect_numbers.append(guess[-1])
                    if guess[-1] in possible_numbers:
                        possible_numbers.remove(guess[-1])
                    if popped not in incorrect_numbers:
                        incorrect_numbers.append(popped)
                    if popped in possible_numbers:
                        possible_numbers.remove(popped)

            # this appears to bring the winrate up 4%
            if total == 0:
                for i in guess:
                    if i in possible_numbers:
                        possible_numbers.remove(i)
                    if i not in incorrect_numbers:
                        incorrect_numbers.append(i)

            correct_numbers, possible_numbers = check_pairs(
                pairs, correct_numbers, incorrect_numbers, possible_numbers, guess, total, psswrd_length)

            if len(possible_numbers) + len(correct_numbers) == psswrd_length:
                correct_numbers = correct_numbers + possible_numbers
                printt('current correct: ' + str(correct_numbers))
                if set(correct_numbers) != set(psswrd) and not INTERACTIVE:
                    print('BADBADBADBADBADBADBADBADBADBAD')
                    print('psswrd: ' + str(psswrd))
                return 1, guesses, position_pairs, correct_numbers

            popped = replaceone(
                guess, possible_numbers, correct_numbers, incorrect_numbers, psswrd_length)

        else:
            # first guess contained no correct answers
            if total == 0:
                for i in range(psswrd_length):
                    possible_numbers.remove(guess[i])
                    incorrect_numbers.append(guess[i])
                for i in range(psswrd_length):
                    guess[i] = possible_numbers[i]
                special = False
            else:
                popped = replaceone(
                    guess, possible_numbers, correct_numbers, incorrect_numbers, psswrd_length)
                special = True

        last_position = position
        last_number = number
        last_total = last_position + last_number

        if not INTERACTIVE:
            for i in incorrect_numbers:
                if i in psswrd:
                    print('BADBADBADBADBADBADBADBADBADBAD')
                    print('psswrd: ' + str(psswrd))

            for i in correct_numbers:
                if i not in psswrd:
                    print('BADBADBADBADBADBADBADBADBADBAD')
                    print('psswrd: ' + str(psswrd))

        if len(possible_numbers) + len(correct_numbers) == 4:
            correct_numbers = correct_numbers + possible_numbers
            printt('current correct: ' + str(correct_numbers))
            if set(correct_numbers) != set(psswrd) and not INTERACTIVE:
                print('BADBADBADBADBADBADBADBADBADBAD')
                print('psswrd: ' + str(psswrd))
            return 1, guesses, position_pairs, correct_numbers

        if len(correct_numbers) > psswrd_length - 1:
            printt('current correct: ' + str(correct_numbers))
            if set(correct_numbers) != set(psswrd) and not INTERACTIVE:
                print('BADBADBADBADBADBADBADBADBADBAD')
                print('psswrd: ' + str(psswrd))
            return 1, guesses, position_pairs, correct_numbers

        printt(
            '--------------------------------------\nguesses made: ' + str(guesses))
        printt('current position: ' + str(position) +
               ' current number: ' + str(number))
        printt('possible_numbers: ' + str(possible_numbers))
        printt('incorrect_numbers: ' + str(incorrect_numbers))
        printt('current correct: ' + str(correct_numbers))

        if not INTERACTIVE:
            printt('current guess: ' + str(guess))
            printt('psswrd: ' + str(psswrd))
        else:
            ans, not_ans = find_positions(correct_numbers, position_pairs)
            print('ans:' + str(ans))
            print('not_ans: ' + str(not_ans))

    return 0, guesses, position_pairs, correct_numbers



def diff(first, second):
    d = len(first)

    for i in range(d):
        if first[i] == second[i]:
            d -= 1

    return d


def check_ans(ans, not_ans, guess, g, position, number):

    if position > 0 and number == 0:
        for i in range(len(g)):
            if g[i] in guess and position > 0:
                if g[i] in ans:
                    pass
                else:
                    if g[i] in not_ans and i in not_ans[g[i]]:
                        pass
                    else:
                        ans[g[i]] = [i]
                        position -= 1
    elif position == 0 and number > 0:
        for i in range(len(g)):
            if g[i] in guess and g[i] not in ans:
                if g[i] in not_ans:
                    if i not in not_ans[g[i]]:
                        not_ans[g[i]] = not_ans[g[i]] + [i]
                else:
                    not_ans[g[i]] = [i]

    return ans, not_ans


def find_positions(guess, pairs):
    # determine exact positions for each number, if any
    ans = {}
    not_ans = {}
    for tup in pairs:
        for g in pairs[tup]:
            g = eval(g)

            position = tup[0]
            number = tup[1]

            ans, not_ans = check_ans(ans, not_ans, guess, g, position, number)

    oldlen = len(ans) - 1
    notoldlen = len(not_ans) - 1


    if len(pairs):
        while len(ans) != oldlen or len(not_ans) != notoldlen:
            for tup in pairs:
                for g in pairs[tup]:
                    g = eval(g)

                    position = tup[0]
                    number = tup[1]

                    if position > 0 and number > 0:
                        if len(ans) > 0:
                            for i in range(len(g)):
                                if g[i] in ans:
                                    if i in ans[g[i]]:
                                        position -= 1
                                    else:
                                        number -= 1

                        # if len(not_ans) > 0:
                        #     for i in range(len(g)):
                        #         if g[i] in not_ans:
                        #             if i in not_ans[g[i]]:
                        #                 number -= 1

                    oldlen = len(ans)
                    notoldlen = len(not_ans)

                    ans, not_ans = check_ans(
                        ans, not_ans, guess, g, position, number)

    return ans, not_ans


def reduce_possibilities(guess, pairs, all_ans):

    ans, not_ans = find_positions(guess, pairs)

    # remove incorrect guesses because we know position of certain number,
    # or because we know number CANNOT be in certain position

    for key in ans:
        for pos in ans[key]:
            items = list(all_ans)
            for an in items:
                try:
                    if an.index(key) != pos:
                        all_ans.remove(an)
                except:
                    all_ans.remove(an)
    for key in not_ans:
        for pos in not_ans[key]:
            items = list(all_ans)
            for an in items:
                try:
                    if an.index(key) == pos:
                        all_ans.remove(an)
                except:
                    pass

    for tup in pairs:
        for g in pairs[tup]:
            g = eval(g)

            position = tup[0]
            number = tup[1]

            if position == 1 and (number == (len(guess)-1)):
                items = list(all_ans)
                for an in items:
                     if diff(an, g) == 2:
                        all_ans.remove(an)

            if len(guess) == 4 and position == 2 and number == 2:
                items = list(all_ans)
                for an in items:
                     if diff(an, g) != 2:
                        all_ans.remove(an)

            if len(guess) == 5 and position == 2 and number == 3:
                items = list(all_ans)
                for an in items:
                     if diff(an, g) == 2:
                        all_ans.remove(an)

            if len(guess) == 5 and position == 3 and number == 2:
                items = list(all_ans)
                for an in items:
                     if diff(an, g) != 2:
                        all_ans.remove(an)


    return all_ans


def find_final(guess, pairs, guesses, pl, psswrd):

    all_ans = []
    for i in itertools.permutations(guess, r=pl):
        all_ans.append(list(i))

    random.shuffle(all_ans)

    all_ans = reduce_possibilities(guess, pairs, all_ans)

    while len(all_ans) > 1 and guesses > 0:
        print('all_ans')
        print(all_ans)
        guess = all_ans.pop()

        if INTERACTIVE:
            position, number = manual_check(guess)
        else:
            position, number = check(guess, psswrd, pl)

        if (position, number) in pairs:
            pairs[(position, number)] = pairs[
                (position, number)] + [str(guess)]
        else:
            pairs[(position, number)] = [str(guess)]

        if (pl, 0) in pairs:
            return pairs[(pl, 0)]

        guesses -= 1
        all_ans = reduce_possibilities(guess, pairs, all_ans)

    return all_ans


def play(game_length, pl, all_psswrds, poss_ans):
    index = random.randint(0, len(all_psswrds) - 1)
    psswrd = all_psswrds.pop(index)

    # psswrd = [1, 8, 0, 3]

    # 8574 very weird for positions

    # psswrd = [0,6,3,4,13]

    win, guesses, pos_pairs, correct = find_numbers2(psswrd, game_length, pl, poss_ans)
    if win and (INTERACTIVE or TEST):
        print('NUMBERS FOUND')
        ans = find_final(correct, pos_pairs, game_length-guesses, pl, psswrd)
        printt('THE CORRECT ORDER IS:')
        printt(ans)
    return win, guesses, psswrd

TEST = True
INTERACTIVE = True

gs = 0
wins = 0
losses = []

gl = 10
pl = 4 #5@14

all_psswrds = []
for i in itertools.permutations(range(gl), r=pl):
    all_psswrds.append(list(i))

poss_ans = all_psswrds[:]

plays = len(all_psswrds)
if TEST:
    plays = 1

for i in tqdm(range(plays)):
    guesses = 0

    win, guess, pwd = play(gl, pl, all_psswrds, poss_ans)
    wins += win
    if win:
        gs += guess
    else:
        losses.append(pwd)

# print(poss_ans)
if plays > 1:
    print('wins: ' + str(wins)+'/'+str(plays))
    print('winrate: ' + str(wins / (plays * 1.0)))
    print('avg guesses to win: ' + str(gs / (wins * 1.0)))
