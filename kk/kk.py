import random, itertools, time, copy

HELP_CMD = 'h'
CAGES_CMD = 'c'
UNDO_CMD = 'z'
REDO_CMD = 'x'
QUIT_CMD = 'q'
RESET_CMD = 'r'
REPLAY_CMD = 'a'
SAVE = False

def show_help_message():
	print('************************************')
	print('welcome to kk. this is the help menu')
	print('{}: show this menu'.format(HELP_CMD))
	print('{}: show cages (useful when adjacent cages share same values)'.format(CAGES_CMD))
	print('{}: undo (can undo repeatedly)'.format(UNDO_CMD))
	print('{}: redo (can redo repeatedly)'.format(REDO_CMD))
	print('{}: quit the game'.format(QUIT_CMD))
	print('{}: reset the current game with the same board'.format(RESET_CMD))
	print('{}: play again, re-entering your board size and difficulty'.format(REPLAY_CMD))
	print('************************************')

class ListBoard:
	def __init__(self, b):
		self.b = b
	def __str__(self):
		max_res = 0
		for i in self.b:
			for j in i:
				if len(str(j)) > max_res:
					max_res = len(str(j))
		s = '   '
		for i in range(len(self.b[0])):
			s += str(i) + '  ' * max_res
		s += '\n'
		x = 0
		for i in self.b:
			s += str(x) + ' ' + str(i) + '\n'
			x += 1
		return s

class Board:
	def __init__(self, b):
		self.b = b
	def __str__(self):
		s = ''
		for i in self.b:
			for j in i:
				s += str(j)
			s += '\n'
		return s

def build_cb(cages, n):
	max_res = 0
	cage_board = [['#' for x in range(n)] for i in range(n)]
	for cage in cages:
		for cell in cage:
			if len(str(cages[cage][0])) + 1 > max_res:
				max_res = len(str(cages[cage][0])) + 1
			cage_board[cell[0]][cell[1]] = str(cages[cage][0]) + cages[cage][1]

	#normalize cell lengths so board always appears same visually (easier to play)
	for row in range(len(cage_board)):
		for col in range(len(cage_board[row])):
			if len(cage_board[row][col]) < max_res:
				cage_board[row][col] = cage_board[row][col] + ' ' * (max_res - len(cage_board[row][col]))
			
	return cage_board

def check_valid(board):
	n = len(board)

	filled_ind = -1
	for i in range(n):
		if len(board[i]):
			filled_ind += 1

	for col in range(n):
		col_set = []
		for row in range(filled_ind + 1):
			if board[row][col] not in col_set:
				col_set.append(board[row][col])
			else:
				return False, row

	if filled_ind == n-1:
		return True, 0
	else:
		return False, filled_ind + 1

# ~10s where n=10
# ~130s where n=11
def build_b(n):
	choices = set(x for x in itertools.permutations(list(range(1, n + 1, 1))))
	board = [[] for i in range(n)]
	board[0] = list(random.sample(choices, 1)[0])

	is_valid, bad_ind = check_valid(board)
	last_bad_ind = 0
	while not is_valid:
		if last_bad_ind != bad_ind:
			last_bad_ind = bad_ind

			for choice in list(choices):
				last_good_ind = bad_ind - 1
				guy = board[last_good_ind]
				bad_choice = False
				for col in range(n):
					if choice[col] == guy[col]:
						choices.remove(tuple(choice))
						bad_choice = True
						break

		candidate = random.sample(choices, 1)[0]
		choices.remove(candidate)
		board[bad_ind] = list(candidate)
		is_valid, bad_ind = check_valid(board)

	return board

def build_c(board, d):
	n = len(board)
	# ops = ['*']*d + ['+']*d + ['-']*d + ['/']*d + ['.']
	ops = ('*', '+', '-', '/')
	max_cage_size = len(board)/2 if len(board)/2 != 1 else 2
	cages = {}

	temp = list(x for x in itertools.permutations(list(range(n) + list(range(n))), r=2))
	choices = []
	for choice in temp:
		if choice not in choices:
			choices.append(choice)

	choice = random.choice(choices)
	choices.remove(choice)
	cages[(choice,)] = (board[choice[0]][choice[1]], '.')

	while len(choices):
		if random.randint(0, 2*d) == d:
			op = '.'
		else:
			op = random.choice(ops)
		if op in ['-', '/']:
			cage_len = 2
		elif len(choices) == 1 or op == '.':
			cage_len = 1
			op = '.'
		else:
			cage_len = random.randint(2, min(max_cage_size, len(choices)))

		#grab at least one cell for the cage
		cage = []
		first_choice = random.choice(choices)
		cage.append(first_choice)
		choices.remove(first_choice)

		cage_choices = choices[:]

		#grab remaining cells to fill cage
		while len(cage) < cage_len:
			try:
				choice = random.choice(cage_choices)
			except:
				cage = []
				break
			cage_choices.remove(choice)
			is_compat = False
			for c in cage:
				row_diff = abs(c[0] - choice[0])
				col_diff = abs(c[1] - choice[1])
				if row_diff + col_diff == 1:
					if op == '/' and board[c[0]][c[1]] != board[choice[0]][choice[1]]:
						division = max(board[c[0]][c[1]], board[choice[0]][choice[1]]) / (min(board[c[0]][c[1]], board[choice[0]][choice[1]]) * 1.0)
						if not division.is_integer():
							break
					is_compat = True
					break
			if is_compat:
				cage.append(choice)

		#calculate the value for the cage
		if len(cage):
			vals = []
			for i in range(len(cage)):
				c = cage[i]
				if c in choices:
					choices.remove(c)
				vals.append(board[c[0]][c[1]])

			vals.sort()
			vals.reverse()
			eval_str = ''
			for i in range(len(vals)):
				val = vals[i]
				eval_str += str(val * 1.0)
				if i != len(cage) - 1:
					eval_str += op
			cage_result = eval(eval_str)
			cage_result = abs(cage_result)

			cages[tuple(cage)] = (int(cage_result), op)
		else:
			choices.append(first_choice)

	return cages

def is_win(user_board, answer_board):
	for i in range(len(user_board)):
		for j in range(len(user_board[i])):
			if user_board[i][j] != answer_board[i][j]:
				return False
	return True

def init_userboard(board, cage_board):
	userboard = copy.deepcopy(board)
	for j in range(len(userboard)):
		for i in range(len(userboard[j])):
			if cage_board[i][j].count('.') != 1:
				userboard[i][j] = 0
	return userboard

def init_cages(board, difficulty):
	cages = build_c(board, difficulty)
	cage_board = build_cb(cages, len(board))
	return cages, cage_board

def start():
	show_help_message()
	done = False
	while not done:
		try:
			size = raw_input('enter board size: ')
			diff = int(raw_input('enter difficulty between 1 and ' + size + ': '))
			size = int(size)
			done = True
		except:
			print('try again: ')
			pass

	board = build_b(size)
	return board, diff

def main():
	board, d = start()
	cages, cage_board = init_cages(board, d)
	userboard = init_userboard(board, cage_board)
	undo = []
	redo = []

	start_time = time.time()
	while not is_win(userboard, board):
		print(ListBoard(cage_board))
		print(ListBoard(userboard))
		try:
			vals = raw_input('enter value as `row,col,val`: ').split(',')
			if vals[0].lower() == CAGES_CMD:
				print('cages:')
				print(cages)
			elif vals[0].lower() == QUIT_CMD:
				print('quitting! here is the answer:')
				print(ListBoard(board))
				exit()
			elif vals[0].lower() == RESET_CMD:
				print('restarting game with current board')
				userboard = init_userboard(board, cage_board)
			elif vals[0].lower() == UNDO_CMD:
				if len(undo):
					last = undo.pop()
					redo.append((last[0], userboard[last[0][0]][last[0][1]]))
					userboard[last[0][0]][last[0][1]] = last[1]
			elif vals[0].lower() == REDO_CMD:
				if len(redo):
					last = redo.pop()
					undo.append((last[0], userboard[last[0][0]][last[0][1]]))
					userboard[last[0][0]][last[0][1]] = last[1]
			elif vals[0].lower() == REPLAY_CMD:
				main()
			elif vals[0].lower() == HELP_CMD:
				show_help_message()
			else:
				row, col, val = int(vals[0]), int(vals[1]), int(vals[2])
				try:
					oldval = userboard[row][col]
					userboard[row][col] = val
					undo.append(((row, col), oldval))
				except:
					print('bad row or col!')
					pass
		except (ValueError, IndexError) as e:
			print('try again: ')
			pass

	end_time = time.time()
	total_time = int(end_time - start_time)
	print('************************************')
	print('you won!')
	print(ListBoard(userboard))
	print('it took you {}:{} to beat this {}x{} board on difficulty {}'.format(total_time / 60, total_time % 60, len(board), len(board), d))
	print('************************************')

	again = 'y'
	if not SAVE:
		again = raw_input('do you want to save this board?: \'y\' for yes, anything else no: ')
	if again == 'y':
		save_playthrough_to_file(board, cages, d, total_time)

	again = raw_input('want to play again? \'a\' for again, anything else to quit: ')
	if again == 'a':
		main()

def read_playthroughs_from_file():
	pass

def save_playthrough_to_file(board, cages, difficulty, time):
	file = open('kk{}.txt'.format(len(board)), 'a')
	file.write(str(board) + '\n')
	file.write(str(cages) + '\n')
	file.write(str(difficulty) + '\n')
	file.write(str(time) + '\n')

def test_time(board_size, difficulty):
	print('testing time it takes to generate a board of size {} with difficulty {}'.format(board_size, difficulty))

	print('building board')
	start_time = time.time()
	board = build_b(board_size)
	end_time = time.time()
	print('board time: {}'.format(end_time - start_time))

	print('building cages')
	start_time = time.time()
	cages = build_c(board, difficulty)
	end_time = time.time()
	print('cages time: {}'.format(end_time - start_time))

	cage_board = build_cb(cages, len(board))

	print(ListBoard(cage_board))
	print(ListBoard(board))

def test_difficulty(board_size=5, boards_to_test=100):
	#number of squares filled ~= difficulty
	max_difficulty_to_check = 2 * board_size
	print('testing average number of squares for a board of size {} with max difficulty {} and number of boards to test {}'.format(board_size, max_difficulty_to_check, boards_to_test))

	print('board size: ' + str(board_size))
	for diff in range(1, max_difficulty_to_check + 1, 1):
		s = 0
		for j in range(boards_to_test):

			board = build_b(board_size)
			cages = build_c(board, diff)
			cage_board = build_cb(cages, len(board))

			for j in range(len(cage_board)):
				for i in range(len(cage_board[j])):
					if cage_board[i][j].count('.') == 1:
						s += 1
		print('average # of filled in squares for difficulty ' + str(diff) + ': ' + str(float(s) / boards_to_test))

# test_time(board_size=8, difficulty=3)
# test_difficulty(board_size=8)
main()