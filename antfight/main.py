import pygame, random, math, tkinter as tk
from tkinter import messagebox
pygame.init()

DEATH_SOUND = pygame.mixer.Sound("death.mp3")

# ------------------ ANT CLASS ------------------
class Ant:
	def __init__(self, team: int, pos: list, role=None):
		global IMAGES, ANT_ID
		ANT_ID += 1
		self.id = ANT_ID
		self.team = team
		self.pos = pos[:]
		self.damage_flicker = 0  # unblit frames after taking damage

		# assign role
		if role:
			self.role = role
		else:
			r = random.random()
			if r < 0.5:
				self.role = "scout"
			elif r < 0.8:
				self.role = "fighter"
			else:
				self.role = "healer"

		# stats by role
		if self.role == "scout":
			self.health = 6
			self.SPEED = random.uniform(1.5, 3.0)
			self.attack_interval = 100
			self.image = IMAGES[f"ANT{team}_SCOUT"]
		elif self.role == "fighter":
			self.health = 12
			self.SPEED = random.uniform(1.2, 1.8)
			self.attack_interval = 20
			self.image = IMAGES[f"ANT{team}_FIGHTER"]
		elif self.role == "healer":
			self.health = 10
			self.SPEED = 2.5
			self.heal_interval = 30
			self.heal_cooldown = 0
			self.image = IMAGES[f"ANT{team}_HEALER"]
		elif self.role == "superman":
			self.health = 40
			self.SPEED = 6.0
			self.attack_interval = 4
			self.image = IMAGES.get(f"ANT{team}_SUPER", None)
			if not self.image:
				self.image = IMAGES[f"ANT{team}_FIGHTER"]  # fallback

		self.base_speed = self.SPEED
		self.adjustment_frame = random.randint(0, 29)
		self.target = None
		self.dir = 0 if team == 1 else 180
		self.damage_cooldown = 0
		self.flee_timer = 0

	def frame(self):
		global FRAME, ants
		if self.damage_flicker > 0:
			self.damage_flicker -= 1

		if self.damage_cooldown > 0:
			self.damage_cooldown -= 1
		if self.role == "healer" and getattr(self, "heal_cooldown", 0) > 0:
			self.heal_cooldown -= 1

		if self.flee_timer > 0 and self.role != "healer":
			self.flee_timer -= 1
			self.target = None
			radians = math.radians(self.dir)
			self.pos[0] += (self.base_speed * 1.5) * math.cos(radians)
			self.pos[1] += (self.base_speed * 1.5) * math.sin(radians)
			self.dir += random.uniform(-10, 10)
			self.speed_boost()
			return

		if self.role == "superman":
			enemies = [e for e in ants if e.team != self.team]
			if enemies:
				self.target = max(enemies, key=lambda e: e.health)
		elif self.role in ["scout", "fighter"]:
			aggro_radius = 50 if self.role=="scout" else 100
			nearby_enemies = [e for e in ants if e.team != self.team and self.distance_to(e) < aggro_radius]
			if nearby_enemies:
				if self.role == "scout":
					self.target = min(nearby_enemies, key=lambda e: e.health)
				elif self.role == "fighter":
					self.target = max(nearby_enemies, key=lambda e: self.enemy_cluster_score(e))
				elif self.role == "healer":
					for e in nearby_enemies:
						if e.role == "fighter":
							self.take_damage(1)

		if FRAME % 30 == self.adjustment_frame:
			if self.role == "healer":
				self.target = self.pick_ally_to_follow()
			elif not self.target or self.target not in ants:
				if self.role == "scout":
					self.target = self.pick_weak_enemy()
				else:
					self.target = self.pick_target()

		if self.target:
			dx = self.target.pos[0] - self.pos[0]
			dy = self.target.pos[1] - self.pos[1]
			self.dir = math.degrees(math.atan2(dy, dx))
		elif self.role == "healer":
			self.dir += random.uniform(-5, 5)

		radians = math.radians(self.dir)
		self.pos[0] += self.SPEED * math.cos(radians)
		self.pos[1] += self.SPEED * math.sin(radians)
		self.speed_boost()

		if self.pos[0] > 436:
			self.dir = math.degrees(math.atan2(math.sin(math.radians(self.dir)), -1))
		elif self.pos[0] < 40:
			self.dir = math.degrees(math.atan2(math.sin(math.radians(self.dir)), 1))
		if self.pos[1] > 356:
			self.dir = math.degrees(math.atan2(-1, math.cos(math.radians(self.dir))))
		elif self.pos[1] < 0:
			self.dir = math.degrees(math.atan2(1, math.cos(math.radians(self.dir))))

		# attack/heal
		if self.role == "scout" and self.target and self.is_touching(self.target):
			if self.damage_cooldown <= 0:
				self.target.take_damage(2)
				self.damage_cooldown = self.attack_interval
				self.flee_timer = 20
				self.target = None

		elif self.role == "fighter" and self.target and self.is_touching(self.target):
			if self.damage_cooldown <= 0:
				self.target.take_damage(1)
				self.damage_cooldown = self.attack_interval
				self.flee_timer = 10
				for a in ants:
					if a.team != self.team and a.role in ["scout", "healer"] and self.is_touching(a):
						a.take_damage(1)


		elif self.role == "healer" and self.target and self.is_touching(self.target):
			if self.heal_cooldown <= 0:
				self.target.receive_heal(1)
				self.heal_cooldown = self.heal_interval

		elif self.role == "superman" and self.target and self.is_touching(self.target):
			if self.damage_cooldown <= 0:
				self.target.take_damage(3)
				self.damage_cooldown = self.attack_interval
				self.flee_timer = 0
				self.target = None

	def enemy_cluster_score(self, e):
		return sum(1 for other in ants if other.team != self.team and self.distance_between(e, other) < 30)

	def distance_to(self, other):
		dx = self.pos[0] - other.pos[0]
		dy = self.pos[1] - other.pos[1]
		return math.sqrt(dx*dx + dy*dy)

	def distance_between(self, a, b):
		dx = a.pos[0] - b.pos[0]
		dy = a.pos[1] - b.pos[1]
		return math.sqrt(dx*dx + dy*dy)

	def speed_boost(self):
		if self.team == 1 and self.pos[0] < 240:
			self.SPEED = self.base_speed * 1.1
		elif self.team == 2 and self.pos[0] > 240:
			self.SPEED = self.base_speed * 1.1
		else:
			self.SPEED = self.base_speed

	def pick_weak_enemy(self):
		global ants
		enemies = [a for a in ants if a.team != self.team]
		if not enemies: return None
		enemies.sort(key=lambda e: ((self.pos[0]-e.pos[0])**2 + (self.pos[1]-e.pos[1])**2))
		closest = enemies[:min(3, len(enemies))]
		closest.sort(key=lambda e: e.health)
		return closest[0]

	def pick_target(self):
		global ants
		enemies = [a for a in ants if a.team != self.team]
		if not enemies: return None
		enemies.sort(key=lambda e: (self.pos[0]-e.pos[0])**2 + (self.pos[1]-e.pos[1])**2)
		return random.choice(enemies[:min(3, len(enemies))])

	def pick_ally_to_follow(self):
		global ants
		allies = [a for a in ants if a.team == self.team and a.role == "fighter"]
		if not allies: return None
		allies.sort(key=lambda a: self.distance_to(a))
		wounded = [a for a in allies if a.health < getattr(a, "health", 100)]
		if wounded:
			wounded.sort(key=lambda a: self.distance_to(a))
			return wounded[0]
		return allies[0]

	def is_touching(self, other):
		dx = self.pos[0] - other.pos[0]
		dy = self.pos[1] - other.pos[1]
		if self.role == "superman":
			return dx*dx + dy*dy < 20*20
		else:
			return dx*dx + dy*dy < 6*6

	def take_damage(self, amount):
		self.health -= amount
		self.damage_flicker = 2
		if self.health <= 0:
			DEATH_SOUND.play()
			if self in ants:
				ants.remove(self)
			return
		if self.role != "healer":
			self.flee_timer = 30
			self.target = None

	def receive_heal(self, amount):
		self.health += amount

# ------------------ IMAGE LOADING ------------------
IMAGE_PATH = "images/"
IMAGE_PATHS = {
	"BG": IMAGE_PATH + "bg.png",
	"ANT1_SCOUT": IMAGE_PATH + "ant1_scout.png",
	"ANT1_FIGHTER": IMAGE_PATH + "ant1_fighter.png",
	"ANT2_SCOUT": IMAGE_PATH + "ant2_scout.png",
	"ANT2_FIGHTER": IMAGE_PATH + "ant2_fighter.png",
	"ANT1_HEALER": IMAGE_PATH + "ant1_healer.png",
	"ANT2_HEALER": IMAGE_PATH + "ant2_healer.png",
	"ANT1_SUPER": IMAGE_PATH + "ant1_super.png",
	"ANT2_SUPER": IMAGE_PATH + "ant2_super.png",
}
IMAGES = {key: pygame.image.load(path) for key, path in IMAGE_PATHS.items()}
ANT_ID = 0

# ------------------ TKINTER SETUP ------------------
root = tk.Tk()
root.title("Antfight Settings")

title_label = tk.Label(root, text="🐜 ANTFIGHT 🐜", font=("Impact", 28), fg="#d22", pady=10)
title_label.pack()

fps_choice = tk.IntVar(value=30)
tk.Label(root, text="Select Game Speed (FPS):", font=("Arial", 14)).pack(pady=5)
tk.Radiobutton(root, text="12 FPS (Slow)", variable=fps_choice, value=12).pack()
tk.Radiobutton(root, text="30 FPS (Normal)", variable=fps_choice, value=30).pack()
tk.Radiobutton(root, text="60 FPS (Fast)", variable=fps_choice, value=60).pack()

money_choice = tk.IntVar(value=160)
tk.Label(root, text="Select Maximum Money:", font=("Arial", 14)).pack(pady=10)
tk.Radiobutton(root, text="$80 (Short Game)", variable=money_choice, value=80).pack()
tk.Radiobutton(root, text="$160 (Standard Game)", variable=money_choice, value=160).pack()
tk.Radiobutton(root, text="$240 (Long Game)", variable=money_choice, value=240).pack()

mode_selected = None
def choose_ai():
	global mode_selected
	mode_selected = "AI"
	root.destroy()

def choose_pvp():
	global mode_selected
	mode_selected = "PVP"
	root.destroy()

tk.Label(root, text="Select Game Mode:", font=("Arial", 14)).pack(pady=10)
tk.Button(root, text="Random AI Battle", width=20, command=choose_ai).pack(pady=5)
tk.Button(root, text="2-Player Placement Battle", width=25, command=choose_pvp).pack(pady=5)

root.mainloop()

SELECTED_FPS = fps_choice.get()
MAX_MONEY = money_choice.get()

# ------------------ GAME OVER FUNCTION ------------------
def check_game_over():
	global ants
	teams = {a.team for a in ants}
	if len(teams) <= 1:
		if teams:
			winner = list(teams)[0]
			pygame.display.flip()
			messagebox.showinfo("Game Over", f"Team {winner} wins!")
		else:
			pygame.display.flip()
			messagebox.showinfo("Game Over", "It's a draw! No ants remain.")
		pygame.quit()
		exit()

# ------------------ GAME FUNCTIONS ------------------
def run_ai_battle():
	global ants, FRAME
	screen = pygame.display.set_mode((480, 360), pygame.SCALED)
	pygame.display.set_caption("Antfight - AI Battle")
	clock = pygame.time.Clock()
	bg = IMAGES["BG"]
	ants = []

	ant_count = int(MAX_MONEY * 0.8)
	for _ in range(ant_count):
		team = random.randint(1, 2)
		y = random.randint(0, 356)
		if team == 1:
			x = random.randint(0, 160)
		else:
			x = random.randint(316, 476)
		ants.append(Ant(team, [x, y]))

	FRAME = 1
	running = True
	while running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
		screen.blit(bg, (0, 0))
		for ant in ants[:]:
			ant.frame()
			if ant.damage_flicker == 0:
				screen.blit(ant.image, ant.pos)
		check_game_over()
		pygame.display.flip()
		clock.tick(SELECTED_FPS)
		FRAME += 1

# ------------------ PVP PLACEMENT ------------------
def run_pvp_placement():
	global ants
	ants = []
	player_money = [20, 20]
	player_turn = 0
	player_ants = [[], []]
	unit_cost = {"scout": 2, "healer": 4, "fighter": 6, "superman": 40}
	total_spent = 0
	total_spent_max = MAX_MONEY  # use the max money selected on main menu


	placement_root = tk.Tk()
	placement_root.title("Placement Phase")
	canvas = tk.Canvas(placement_root, width=480, height=360, bg="white")
	canvas.pack()

	selected_unit = tk.StringVar(value="scout")
	status_label = tk.Label(placement_root, text=f"Player 1 turn | $20 available | Selected: scout | Total spent: {total_spent}", font=("Arial", 12))
	status_label.pack(pady=5)

	def update_status():
		status_label.config(
			text=f"Player {player_turn+1} turn | ${player_money[player_turn]} available | Selected: {selected_unit.get()} | Total spent: {total_spent}"
		)

	def select_unit(role):
		selected_unit.set(role)
		update_status()

	tk.Button(placement_root, text="Scout ($2)", command=lambda: select_unit("scout")).pack(side="left")
	tk.Button(placement_root, text="Healer ($4)", command=lambda: select_unit("healer")).pack(side="left")
	tk.Button(placement_root, text="Fighter ($6)", command=lambda: select_unit("fighter")).pack(side="left")
	superman_btn = tk.Button(placement_root, text="Superman ($40)", command=lambda: select_unit("superman"))
	superman_btn.pack(side="left")

	def forego_turn():
		switch_turn()

	def switch_turn():
		nonlocal player_turn
		player_money[player_turn] += 20
		player_turn = 1 - player_turn
		update_status()

	tk.Button(placement_root, text="Forego turn", command=forego_turn).pack(side="left")

	def draw_ants():
		canvas.delete("all")
		canvas.create_line(240,0,240,360, fill="gray", dash=(2,2))
		canvas.create_line(180,0,180,360, fill="lightgray", dash=(2,2))
		canvas.create_line(300,0,300,360, fill="lightgray", dash=(2,2))
		for a in ants:
			if a.role == "scout":
				color = "#bbb" if a.team==1 else "#99bfff"
			elif a.role == "fighter":
				color = "#f55" if a.team==1 else "#5577ff"
			elif a.role == "healer":
				color = "#ff0" if a.team==1 else "#00ff00"
			else:
				color = "#ff00ff" if a.team==1 else "#ff77ff"
			canvas.create_oval(a.pos[0]-5, a.pos[1]-5, a.pos[0]+5, a.pos[1]+5, fill=color)

	def place_unit(event):
		nonlocal player_turn, total_spent
		role = selected_unit.get()
		cost = unit_cost[role]

		if cost > player_money[player_turn]:
			messagebox.showinfo("Info", "Not enough money for this unit!")
			return

		if player_turn == 0 and not (0 <= event.x <= 180):
			messagebox.showinfo("Info", "Place units on your side (left)!")
			return
		if player_turn == 1 and not (300 <= event.x <= 480):
			messagebox.showinfo("Info", "Place units on your side (right)!")
			return

		ant = Ant(player_turn + 1, [event.x, event.y], role)
		ants.append(ant)
		player_ants[player_turn].append(ant)
		player_money[player_turn] -= cost
		total_spent += cost

		update_status()
		draw_ants()

		if total_spent >= total_spent_max:
			placement_root.destroy()  # close placement and start game

		if player_money[player_turn] <= 0:
			switch_turn()

	canvas.bind("<Button-1>", place_unit)
	draw_ants()
	update_status()
	placement_root.mainloop()

	# --- BATTLE PHASE ---
	screen = pygame.display.set_mode((480, 360), pygame.SCALED)
	pygame.display.set_caption("Antfight - PvP Battle")
	clock = pygame.time.Clock()
	bg = IMAGES["BG"]

	global FRAME
	FRAME = 1
	running = True
	while running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
		screen.blit(bg, (0, 0))
		for ant in ants[:]:
			ant.frame()
			if ant.damage_flicker == 0:
				screen.blit(ant.image, ant.pos)
		check_game_over()
		pygame.display.flip()
		clock.tick(SELECTED_FPS)
		FRAME += 1


# ------------------ START ------------------
if mode_selected == "AI":
	run_ai_battle()
elif mode_selected == "PVP":
	run_pvp_placement()
