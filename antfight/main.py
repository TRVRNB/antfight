import pygame, random, math
pygame.init()

class Ant:
	def __init__(self, team: int, pos: list):
		global IMAGES, ANT_ID
		ANT_ID += 1
		self.id = ANT_ID
		self.team = team
		self.pos = pos
		self.image = IMAGES["ANT" + str(team)]
		self.SPEED = random.uniform(1.0, 3.0)
		if team == 1:
			self.dir = 0
		else:
			self.dir = 180
	def frame(self):
		# very elaborate! this changes the direction in just 1 axis. it lags a bit when there are a few... thousand ants
		if self.pos[0] > 436:
			self.dir = math.degrees(math.atan2(math.sin(math.radians(self.dir)), -1))
		elif self.pos[0] < 40:
			self.dir = math.degrees(math.atan2(math.sin(math.radians(self.dir)), 1))
		elif self.pos[1] > 356: # x is prioritized over y
			self.dir = math.degrees(math.atan2(-1, math.cos(math.radians(self.dir))))
		elif self.pos[1] < 0:
			self.dir = math.degrees(math.atan2(1, math.cos(math.radians(self.dir))))
		radians = math.radians(self.dir)
		self.dir += random.uniform(-5.0, 5.0)
		self.pos[0] += self.SPEED * math.cos(radians)
		self.pos[1] += self.SPEED * math.sin(radians)

IMAGE_PATH = "images/"
IMAGE_PATHS = {
"BG": IMAGE_PATH + "bg.png",
"ANT1": IMAGE_PATH + "ant1.png",
"ANT2": IMAGE_PATH + "ant2.png",
}

IMAGES = {}

for key in IMAGE_PATHS.keys():
	IMAGES[key] = pygame.image.load(IMAGE_PATHS[key])

ANT_ID = 0

screen = pygame.display.set_mode((480, 360), pygame.SCALED)
pygame.display.set_caption("Antfight")
clock = pygame.time.Clock()

bg = IMAGES["BG"]

ants = []
for _ in range(random.randint(100, 500)):
	team = random.randint(1, 2)
	y = random.randint(0, 356)
	if team == 1:
		x = random.randint(0, 160)
	else:
		x = random.randint(316, 476)
	pos = [x, y]
	ant = Ant(team, pos)
	ants.append(ant)



running = True
while running:	
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			running = False
	screen.blit(bg, (0, 0))
	for ant in ants:
		ant.frame()
		screen.blit(ant.image, ant.pos)
	
	pygame.display.flip()
	clock.tick(120) # this should range from 10-20-30-60-120 depending on the speed setting
