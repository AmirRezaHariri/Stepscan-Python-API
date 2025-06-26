# **Stepscan Live**

# Pressure data. Serial ID of the tile can be identified from the API. 
# Install stepscanlive.msi
# DAQ.exe can be interfaced to the UI (C++ based) in Example Apps folder. 

# DAQ.exe has two configutation files 
# 1)DAQ.confiq is autogrenerated by stepscan live. 
# 2)Tilelookup -> serialnumbers.dat (the API will need the 12 tile associated lookup files). 
# So you would use the API in a loop. 

# E.g.: 
# while(TRUE) 
# api.read(data)

# titleReader.read()

# Colours:
# Red, Green and Blue

# split the two tile array to 3 colours. 720x240 dimensional block. 
# 1 player only. Get from point A to point B. 


import pygame
import sys
import random
import numpy as np

LIMBS = ["h_l", "h_r", "f_l", "f_r"]
LIMBS_TEXT = ["Left Hand", "Right Hand", "Left Foot", "Right Foot"]

COLORS = ["r", "b", "g"]
COLORS_TEXT = ["Red", "Blue", "Green"]

PHASES = ["set", "move"]
RED = (255, 0, 0)
GREEN = (0, 255, 0)
touched_plates = []
touched_plate_copy = []
g_list = [(0,0), (0,1),(0,2),(0,3),(0,4),(0,5)]
b_list = [(1,0), (1,1),(1,2),(1,3),(1,4),(1,5)]
r_list = [(2,0), (2,1),(2,2),(2,3),(2,4),(2,5)]

ourLimbs = []
target_limb = None
target_pos = None

initialized:bool = False    

def create_rand_limb_pos():
    idx_limb = random.randint(0, len(LIMBS)-1)
    idx_color = random.randint(0, len(COLORS)-1)
    return (LIMBS[idx_limb], COLORS[idx_color]) 

bounds_x = np.arange(0,239,80)
bounds_y = np.arange(0,479,80)

# frame is 480 x 240 
def get_contact(frame, bounds_x = bounds_x, bounds_y = bounds_y, thresh = 10):
    frame_bin = frame > thresh

    # get regions of contact within bounds
    y_contact = np.digitize(np.where(frame_bin)[0], bounds_y)-1
    x_contact = np.digitize(np.where(frame_bin)[1], bounds_x)-1

    contact_lst = np.unique(np.stack((y_contact,x_contact)),axis = 1)

    # convert to list of tuples
    contact_lst = [(contact[0].item(),contact[1].item()) for contact in contact_lst.T]

    return contact_lst 

class Limb:
    def __init__(self, limb:str, initial_pos):
      self.limb = limb
      self.pos = initial_pos
      phase = "set"

# Initialize pygame
pygame.init()

# Set up the display
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Basic Pygame Loop")

# Set up the clock for framerate control
clock = pygame.time.Clock()

# Spins the wheel and returns a random limb and color
def create_rand_limb_pos():

    # Randomly select a limb and color
    idx_limb = random.randint(0, len(LIMBS)-1)
    idx_color = random.randint(0, len(COLORS)-1)
    print(f"Selected Limb: {LIMBS[idx_limb]}, Color: {COLORS[idx_color]}")

    # Starting angle for the spinner
    angle = 15

    # Adjusts angle based on the selected limb and color
    if LIMBS[idx_limb] == "h_l":
        angle += 180
    elif LIMBS[idx_limb] == "f_l":
        angle += 90
    elif LIMBS[idx_limb] == "f_r":
        angle += 270

    if COLORS[idx_color] == "r":
        angle += 45
    elif COLORS[idx_color] == "g":
        angle += 67.5

    # Backs up arrow before spin so that it lands in the right position
    angle -= 118

    # Load and display an image at the center of the screen
    spinner_image = pygame.image.load("Python/assets/spinner.jpg")
    spinner_rect = spinner_image.get_rect(center=(screen_width // 2, screen_height // 2))
    arrow_image = pygame.image.load("Python/assets/arrow.png")

    # Set counter and initial speed for the spinner
    count = 200
    speed = 5

    while count > 0:
        # Re-draw the arrow
        rotated_arrow = pygame.transform.rotate(arrow_image, angle)
        rotated_rect = rotated_arrow.get_rect(center=spinner_rect.center)

        # Draw evreything to secreen
        screen.fill((0, 0, 0))  # Fill screen with black
        screen.blit(spinner_image, spinner_rect)  # Draw the arrow on top of the spinner
        screen.blit(rotated_arrow, rotated_rect)
        pygame.display.flip()

        # Change the angle and speed
        angle -= speed
        speed -= 0.02
        count -= 1
        pygame.time.delay(5)

    pygame.time.delay(1000)  # Delay to show the spinner for a second
    return (LIMBS[idx_limb], COLORS[idx_color]) 

from API import *

bufImSize = 1000 * 1000 * 1000
bufIm = np.zeros(bufImSize, dtype='uint16')
bufMetaData = np.full(int(bufImSize / 1_000_000 * 5 * 100), -1, dtype=float)
dataReceiver = DataReceiverThread("PipeOutput", bufIm, bufMetaData)
dataReceiver.start()

# Main loop
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Game logic goes here
        # Steps:
        # 1)Starting position
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if (initialized == False):
                    print("Start Initialize!")
                    ourLimbs = [Limb(limb=LIMBS[0], initial_pos=(1,2)), 
                                Limb(limb=LIMBS[1], initial_pos=(1,1)),
                                Limb(limb=LIMBS[2], initial_pos=(0,2)),
                                Limb(limb=LIMBS[3], initial_pos=(0,1))]
                    initialized = True
            
            elif(event.key == pygame.K_RETURN):
                # 2)Randomize new action -> instructions displayed on Screen UI. 
                (target_limb, target_col) = create_rand_limb_pos()
                if(target_col == "r"):
                    target_pos = r_list
                elif(target_col == "g"):
                    target_pos = g_list
                elif(target_col == "b"):
                    target_pos = b_list
                
                for limb in ourLimbs:
                    limb.phase = "set"
                    if limb.limb == target_limb:
                        limb.phase = "move"
                
        
        
        
    if(initialized & (target_pos != None)):
        # GET THE CURRENT MEASUREMNTS
        frame = dataReceiver.image_buffer[-1][:480, :] # read data here
        touched_plates = get_contact(frame)
        touched_plate_copy = touched_plates.copy()
        
        # are all limbs were they are supposed to be
        for limb in ourLimbs:
            # if (limb.phase == "set"):
            if(limb.pos in touched_plates):
                print(f"{limb.limb} is correct")
                idx = touched_plates.index(limb.pos)
                touched_plates.pop(idx)
            else:
                print(f"{limb.limb} - ERROR")
            
        if (len(touched_plates) > 1):
            print('ERROR')
            
        elif(len(touched_plates) == 1):
            if(touched_plates[0] in target_pos):
                print('success')
                for limb in ourLimbs:
                    if limb.limb == target_limb:
                        limb.pos = touched_plates[0]
                        limb.phase = "set"
            else:
                print("ERROR")
                
                
                
                
        
            # elif(limb.phase == "move"):
            #     # see if it touches sth, then compare it to new_cmd
                
            #     # is it touching the old one => Fine
            #     if(limb.pos in touched_plates):
            #         print(f"{limb.limb} is correct")
                    
            #     # is it touch ing the new one => Set new position
            #     # elif(target_pos in touched_plates):
            #     #     limb.pos = target_pos
            #     #     limb.phase = "set"
            #     #     print(f"Success - {limb.limb} is in target")
                    
            #     # elif(touched_plates >= 4):
            #     #     print(f"ERROR - {limb.limb} went to wrong target")
                    
            #     # is there a touched plate which was neither a limb.pos nor target pos
                
                
                
            #     unique = [t for t in ok_limb_poses+touched_plates if (t not in ok_limb_poses or t not in touched_plates)]
            #     if len(unique) >= 1:
            #         print(f"ERROR {unique} was touched")
                
                
        if(len(touched_plates) > 4):
            print(f"ERROR: TOO many tiles touched")


    # 4)Limb phase -> contact or no-contact. 10kPa threshold for contact detection. 

    # 5)Allowed to move and not allowed to move and error of action -> Disqualified. 

    # 6)End -> Passed!


    # Drawing code goes here
    screen.fill((0, 0, 0))  # Fill screen with black

    # Draws the rectangles to display the tile state
    if(initialized):
        for i in range(6):
            for j in range(3):

                # Draw instructions at the top
                font = pygame.font.SysFont(None, 36)
                if target_limb is not None:
                    limb_text = LIMBS_TEXT[LIMBS.index(target_limb)]
                    color_text = COLORS_TEXT[COLORS.index(target_col)]
                    text = f"{limb_text} on {color_text}"
                else:
                    text = "Press ENTER to spin!"

                text_surface = font.render(text, True, (255, 255, 255))
                screen.blit(text_surface, (screen_width // 2 - text_surface.get_width() // 2, 50))

                # Draw grid of rectangles
                rect = pygame.Rect(i * 100 + 110, j * 100 + 200, 80, 80)
                # touched_plates = [(0,0),(0,1),(1,1),(2,3)]
                # Color the tiles if they are touched or not
                if (i,j) in touched_plate_copy:
                    pygame.draw.rect(screen, GREEN, rect)
                else:
                    pygame.draw.rect(screen, RED, rect)
    else:
        # Display the initial message
        font = pygame.font.SysFont(None, 36)
        text_surface = font.render("Press SPACE to initialize!", True, (255, 255, 255))
        screen.blit(text_surface, (screen_width // 2 - text_surface.get_width() // 2, screen_height // 2 - 20))


    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

# Clean up
pygame.quit()
sys.exit()
