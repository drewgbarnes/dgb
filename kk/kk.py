import random, itertools, time, copy

HELP_CMD = 'h'
CAGES_CMD = 'c'
UNDO_CMD = 'z'
REDO_CMD = 'x'
QUIT_CMD = 'q'
RESET_CMD = 'r'
REPLAY_CMD = 'a'
ROW_CMD = 'r'
COL_CMD = 'c'
TOTAL_CMD = 't'
SAVE = False
PLACEHOLDER = '*'

COLORS = ['\033[9{}m'.format(x) for x in range(8)]
SOLO_COLOR = COLORS.pop()
BAD_COLOR = '\033[41m'
BAD_CAGE_COLOR = '\033[45m'
COLORS += ['\033[3{}m'.format(x) for x in range(1,7,1)]
ENDC = '\033[0m'


def show_help_message():
	print(COLORS[2] + 'welcome to kk. this is the help menu' + ENDC)
	print('************************************')
	print('{}: show this menu'.format(HELP_CMD))
	print('{}: undo (can undo repeatedly)'.format(UNDO_CMD))
	print('{}: redo (can redo repeatedly)'.format(REDO_CMD))
	print('#{} (0{} for example): show numbers that are still needed in a row'.format(ROW_CMD, ROW_CMD))
	print('#{} (0{} for example): show numbers that are still needed in a col'.format(COL_CMD, COL_CMD))
	print('{}: quit the game'.format(QUIT_CMD))
	print('{}: reset the current game with the same board'.format(RESET_CMD))
	print('{}: play again, re-entering your board size and difficulty'.format(REPLAY_CMD))
	print('{}: show cages (useful when adjacent cages share same values)'.format(CAGES_CMD))
	print(BAD_COLOR + 'color when the same number occurs more than once in a row/col' + ENDC)
	print(BAD_CAGE_COLOR + 'color when a cage does not have correct math' + ENDC)
	print('************************************')


class ListBoard:
	def __init__(self, b, normal=True, color=None, cages=None, mistakes=True):
		self.b = b
		self.normal = normal
		self.color = color
		self.mistakes = mistakes
		self.cages = cages
		self.inverse = copy.deepcopy(self.b)
		for i in range(len(self.inverse)):
			for j in range(len(self.inverse)):
				self.inverse[j][i] = self.b[i][j]
	def __str__(self):
		max_res = 0
		for i in self.b:
			for j in i:
				if len(str(j)) > max_res:
					max_res = len(str(j))
		if not self.normal:
			max_res = max_res - len(COLORS[0]) - len(ENDC)
		s = '    '
		for i in range(len(self.b)):
			s += str(i) + (' ' * max_res)
		s += '\n'
		x = 0
		for i in range(len(self.b)):
			row = ''
			for z in range(len(self.b[i])):
				guy = str(self.b[i][z])
				if self.color:
					the_color = self.color[i][z]
					if self.mistakes:
						if guy != PLACEHOLDER and (self.b[i].count(int(guy)) > 1 or self.inverse[z].count(int(guy)) > 1):
							the_color = BAD_COLOR
					if self.cages:
						for cage in self.cages:
							if len(cage) > 1 and (i,z) in cage:
								expected_result = self.cages[cage][0]
								operator = self.cages[cage][1]
								vals_to_math = []
								finished_cage = True
								for cell in cage:
									if self.b[cell[0]][cell[1]] == PLACEHOLDER:
										finished_cage = False
										break
									vals_to_math.append(self.b[cell[0]][cell[1]])

								if finished_cage:
									vals_to_math.sort()
									vals_to_math.reverse()
									eval_str = ''
									for j in range(len(vals_to_math)):
										val = vals_to_math[j]
										eval_str += str(val * 1.0)
										if j != len(cage) - 1:
											eval_str += operator
									cage_result = eval(eval_str)
									cage_result = abs(cage_result)
									if cage_result != expected_result:
										the_color = BAD_CAGE_COLOR
					guy = the_color + guy + ENDC
				row += guy + ' '
			s += str(x) + ' ' + '[ '+ row + ']' + '\n'
			x += 1
		return s


def build_cb(cages, n):
	max_res = 0
	color_board = {}
	cage_board = [['#' for x in range(n)] for i in range(n)]
	color_cages = {}
	for cage in cages:
		color = random.choice(COLORS)
		if len(cage) == 1:
			color = SOLO_COLOR
		else:
			if str(cages[cage][0]) + cages[cage][1] in color_cages:
				while color in color_cages[str(cages[cage][0]) + cages[cage][1]]:
					color = random.choice(COLORS)
			else:
				color = random.choice(COLORS)
			color_cages[str(cages[cage][0]) + cages[cage][1]] = color
		for cell in cage:
			if len(str(cages[cage][0])) + 1 > max_res:
				max_res = len(str(cages[cage][0])) + 1
			cage_board[cell[0]][cell[1]] = color + str(cages[cage][0]) + cages[cage][1]
			if cell[0] in color_board:
				color_board[cell[0]][cell[1]] = color
			else:
				color_board[cell[0]] = {cell[1]: color}

	# normalize cell lengths so board always appears same visually (easier to play)
	for row in range(len(cage_board)):
		for col in range(len(cage_board[row])):
			cage_board[row][col] = cage_board[row][col] + (' ' * (max_res + len(COLORS[0]) - len(cage_board[row][col]))) + ENDC
			
	return cage_board, color_board


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


def has_ambiguous_cages(cages):
	#TODO: prevent board where cages are ambiguous (2* in one row and 2* in another row but at same columns)
	return False


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
		op = '.' if random.randint(0, 2*d) == d else random.choice(ops)
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
				userboard[i][j] = PLACEHOLDER
	return userboard


def init_cages(board, difficulty):
	cages = build_c(board, difficulty)
	while has_ambiguous_cages(cages):
		cages = build_c(board, difficulty)
	cage_board, color_board = build_cb(cages, len(board))
	return cages, cage_board, color_board


def start(interactive, ai_size=None, ai_diff=None):
	if interactive:
		show_help_message()
	done = False
	size = None
	if not ai_size:
		while not done:
			try:
				size = raw_input('enter board size: ')
				size = int(size)
				diff = int(raw_input('enter difficulty between 1 and ' + str(size) + ': '))
				done = True
			except ValueError:
				if size and size.lower() == QUIT_CMD:
					exit()
				print('try again: ')
				pass
	else:
		size = ai_size
		diff = ai_diff

	board = build_b(size)
	return board, diff


def guess_one_index(userboard, userboard_or_inverse, playable_numbers):
	for i in range(len(userboard)):
		row_or_col = userboard_or_inverse[i]
		other_rows_or_cols  = list(range(len(userboard)))
		other_rows_or_cols.remove(i)
		remaining_ans_for_row_or_col = set(playable_numbers).difference(set(row_or_col))
		for potential in remaining_ans_for_row_or_col:
			potential_indexes = list(range(len(userboard)))
			for r in range(len(row_or_col)):
				#remove filled in rows 
				if row_or_col[r] != PLACEHOLDER and r in potential_indexes:
					potential_indexes.remove(r)
			for other_row_or_col in other_rows_or_cols:
				for r in range(len(userboard)):
					guy = userboard[r][other_row_or_col] if userboard != userboard_or_inverse else userboard[other_row_or_col][r]					
					if guy == potential and r in potential_indexes:
						potential_indexes.remove(r)
			if len(potential_indexes) == 1:
				if userboard != userboard_or_inverse:
					print('all cols other than {} already have {}'.format(i, potential))
					return potential_indexes[0], i, potential
				print('all rows other than {} already have {}'.format(i, potential))
				return i, potential_indexes[0], potential


def guess(userboard, cages):
	inverse = copy.deepcopy(userboard)
	for i in range(len(inverse)):
			for j in range(len(inverse)):
				inverse[j][i] = userboard[i][j]

	playable_numbers = list(range(1, len(userboard) + 1, 1))

	#if only 1 number left to be played in a row or column, fill it in
	for i in range(len(userboard)):
		remaining_ans_for_row = set(playable_numbers).difference(set(userboard[i]))
		remaining_ans_for_col = set(playable_numbers).difference(set(inverse[i]))
		if len(remaining_ans_for_row) == 1:
			guy = remaining_ans_for_row.pop()
			print('row {} needs only {}'.format(i, guy))
			return i, userboard[i].index(PLACEHOLDER), guy
		if len(remaining_ans_for_col) == 1:
			guy = remaining_ans_for_col.pop()
			print('col {} needs only {}'.format(i, guy))
			return inverse[i].index(PLACEHOLDER), i, guy

	#if a row and col's intersection only needs 1 number, fill it in
	for i in range(len(userboard)):
		row = userboard[i]
		for j in range(len(userboard)):
			col = inverse[j]
			remaining_ans_for_row = set(playable_numbers).difference(set(row))
			remaining_ans_for_col = set(playable_numbers).difference(set(col))
			row_col_intersect = set(remaining_ans_for_col).intersection(set(remaining_ans_for_row))
			if len(row_col_intersect) == 1 and userboard[i][j] == PLACEHOLDER:
				guy = row_col_intersect.pop()
				print('{},{} intersection needs only {}'.format(i, j, guy))
				return i, j, guy

	#if we have only 1 possible index in a row that a number can go, fill it in
	g = guess_one_index(userboard, userboard, playable_numbers)
	if g:
		return g
	g = guess_one_index(userboard, inverse, playable_numbers)
	if g:
		return g

	#if a cage has everything filled in except 1 cell, the cage can be filled in
	for cage in cages:
		if cages[cage][1] != '.':
			current_calculation_for_cage = []
			size_of_cage = len(cage)
			op = cages[cage][1]
			ans_for_cage = cages[cage][0]
			for cell in cage:
				guy = userboard[cell[0]][cell[1]]
				if guy != PLACEHOLDER:
					current_calculation_for_cage.append(guy)
				else:
					cell_in_cage_to_finish = cell
			if len(current_calculation_for_cage) == size_of_cage - 1:
				eval_str = ''
				for i in range(len(current_calculation_for_cage)):
					val = current_calculation_for_cage[i]
					eval_str += str(val * 1.0)
					eval_str += op

				potential_answers = set(playable_numbers)
				correct_answers = []
				for potential_answer in potential_answers:
					if op == '/':
						cage_result = max(potential_answer, current_calculation_for_cage[0]) / (min(potential_answer, current_calculation_for_cage[0]) * 1.0)
					else:
						cage_result = eval(eval_str + str(potential_answer * 1.0))
					cage_result = abs(cage_result)
					if cage_result == ans_for_cage:
						correct_answers.append(potential_answer)
				
				#need to check if the correct answers do not already appear in its col/rol
				for correct_answer in copy.deepcopy(correct_answers):
					if correct_answer in userboard[cell_in_cage_to_finish[0]] or correct_answer in inverse[cell_in_cage_to_finish[1]]:
						correct_answers.remove(correct_answer)

				if len(correct_answers) == 1:
					print('all cells in cage filled except {},{} needs {}'.format(cell_in_cage_to_finish[0], cell_in_cage_to_finish[1], correct_answers[0]))
					return cell_in_cage_to_finish[0], cell_in_cage_to_finish[1], correct_answers[0]


def main(ai_size=None, ai_diff=None):
	INTERACTIVE = False
	KEEP_RUNNING_AI = False
	board, d = start(INTERACTIVE, ai_size, ai_diff)
	cages, cage_board, color_board = init_cages(board, d)
	userboard = init_userboard(board, cage_board)
	undo = []
	redo = []

	start_time = time.time()
	while not is_win(userboard, board):
		print(ListBoard(b=cage_board, normal=False))
		print(ListBoard(b=userboard, normal=True, color=color_board, cages=cages, mistakes=True))
		try:
			if INTERACTIVE:
				vals = raw_input('enter value as `row,col,val`: ').split(',')
			else:
				print('making move:')
				vals = guess(userboard, cages)
				if vals is None:
					print('ai not smart enough to guess, answer for it or quit')
					vals = raw_input('enter value as `row,col,val`: ').split(',')
					# if KEEP_RUNNING_AI:
					# 	main(len(board), d)
					# else:
					# 	main()
				else:
					vals = str(vals[0]), str(vals[1]), str(vals[2])
					enter = raw_input('enter to continue')
			if vals[0].lower() == CAGES_CMD:
				print('cages:')
				print(cages)
			elif vals[0].lower() == TOTAL_CMD:
				number_totals = {}
				for row in userboard:
					for guy in row:
						if guy != PLACEHOLDER:
							if guy not in number_totals:
								number_totals[guy] = 1
							else:
								number_totals[guy] += 1

				print('Total of each number played: {}'.format(number_totals))
			elif vals[0].lower() == QUIT_CMD:
				print('quitting! here is the answer:')
				print(ListBoard(b=board, normal=True, color=color_board))
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
			elif len(vals[0]) > 1:
				if vals[0][0].isdigit() and vals[0][1].lower() == COL_CMD:
					playable_numbers = list(range(1, len(userboard) + 1, 1))
					inverse = copy.deepcopy(userboard)
					for i in range(len(inverse)):
							for j in range(len(inverse)):
								inverse[j][i] = userboard[i][j]
					remaining_ans_for_col = set(playable_numbers).difference(set(inverse[int(vals[0][0])]))
					print('Numbers remaining in column {}: {}'.format(vals[0][0], sorted(list(remaining_ans_for_col))))
				elif vals[0][0].isdigit() and vals[0][1].lower() == ROW_CMD:
					playable_numbers = list(range(1, len(userboard) + 1, 1))
					remaining_ans_for_row = set(playable_numbers).difference(set(userboard[int(vals[0][0])]))
					print('Numbers remaining in row {}: {}'.format(vals[0][0], sorted(list(remaining_ans_for_row))))
			else:
				row, col, val = int(vals[0]), int(vals[1]), int(vals[2])
				try:
					if val > len(board) or val < 1:
						raise Exception
					oldval = userboard[row][col]
					userboard[row][col] = val
					undo.append(((row, col), oldval))
				except:
					print('bad row, col or val!')
					pass
		except (ValueError, IndexError) as e:
			print('try again: ')
			pass

	end_time = time.time()
	total_time = int(end_time - start_time)
	print('************************************')
	print('you won!')
	print(ListBoard(b=userboard, normal=True, color=color_board))
	print('it took you {}:{} to beat this {}x{} board on difficulty {}'.format(total_time / 60, total_time % 60, len(board), len(board), d))
	print('************************************')

	if INTERACTIVE:
		again = 'y'
		if not SAVE:
			again = raw_input('do you want to save this board?: \'y\' for yes, anything else no: ')
		if again == 'y':
			save_playthrough_to_file(board, cages, d, total_time)

		again = raw_input('want to play again? \'a\' for again, anything else to quit: ')
		#TODO: even if you type Q here it still plays again???
		if again == 'a':
			main()
	else:
		main(ai_size, ai_diff)


def read_playthroughs_from_file():
	pass


def save_playthrough_to_file(board, cages, difficulty, time):
	with open('kk{}.txt'.format(len(board)), 'a') as file:
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

	cage_board, color_board = build_cb(cages, len(board))

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
			cage_board, color_board = build_cb(cages, len(board))

			for j in range(len(cage_board)):
				for i in range(len(cage_board[j])):
					if cage_board[i][j].count('.') == 1:
						s += 1
		percent_filled = ((float(s) / boards_to_test) / board_size ** 2) *100
		print('average # of filled in squares for difficulty {}: {} or {}%'.format(diff, float(s) / boards_to_test, percent_filled))

# test_time(board_size=8, difficulty=3)
# test_difficulty(board_size=7)
main()