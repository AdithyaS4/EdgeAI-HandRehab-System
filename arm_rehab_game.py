import cv2
import mediapipe as mp
import pygame
import random
import sqlite3
import datetime
import math

# -------------------------
# Patient Name Input
# -------------------------
patient_name = input("Enter Patient Name: ")

# -------------------------
# Initialize MediaPipe
# -------------------------
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# -------------------------
# Initialize Pygame
# -------------------------
pygame.init()
WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Arm Rehab Game")

font = pygame.font.SysFont(None, 40)

# -------------------------
# Game Variables
# -------------------------
ball_radius = 20
ball_x = random.randint(150, WIDTH - 150)
ball_y = 50
ball_speed = 5

score = 0
missed = 0
total_attempts = 0

grip_ready = True

clock = pygame.time.Clock()
cap = cv2.VideoCapture(0)

running = True
start_time = datetime.datetime.now()

while running:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    hand_closed = False
    hand_x, hand_y = None, None

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:

            # -------- FINGER BEND DETECTION --------
            tips = [8, 12, 16, 20]
            pips = [6, 10, 14, 18]

            bent_fingers = 0

            for tip_id, pip_id in zip(tips, pips):
                tip = hand_landmarks.landmark[tip_id]
                pip = hand_landmarks.landmark[pip_id]

                if tip.y > pip.y:
                    bent_fingers += 1

            if bent_fingers >= 3:
                hand_closed = True

            # Use index tip for collision center
            index_tip = hand_landmarks.landmark[8]
            hand_x = int(index_tip.x * WIDTH)
            hand_y = int(index_tip.y * HEIGHT)

            # -------- Skeleton Color Change --------
            if hand_closed:
                color = (0, 255, 0)  # GREEN when closed
            else:
                color = (0, 0, 255)  # RED when open

            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=color, thickness=3, circle_radius=4),
                mp_drawing.DrawingSpec(color=color, thickness=2)
            )

    # Convert frame to pygame surface
    frame = cv2.resize(frame, (WIDTH, HEIGHT))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame_surface = pygame.surfarray.make_surface(frame.swapaxes(0,1))

    screen.blit(frame_surface, (0,0))

    # Draw Ball
    pygame.draw.circle(screen, (255,0,0), (ball_x, ball_y), ball_radius)

    # Ball movement
    ball_y += ball_speed

    if ball_y > HEIGHT:
        missed += 1
        total_attempts += 1
        ball_y = 50
        ball_x = random.randint(150, WIDTH - 150)

    # -------- Grip Reset Logic --------
    if not hand_closed:
        grip_ready = True

    if hand_x and hand_y and hand_closed and grip_ready:
        distance = math.sqrt((hand_x - ball_x)**2 + (hand_y - ball_y)**2)
        if distance < ball_radius:

            score += 1
            total_attempts += 1

            ball_y = 50
            ball_x = random.randint(150, WIDTH - 150)

            grip_ready = False

    success_rate = (score / total_attempts * 100) if total_attempts > 0 else 0

    # Display Score
    score_text = font.render(f"Score: {score}", True, (255,255,255))
    success_text = font.render(f"Success: {success_rate:.1f}%", True, (255,255,0))
    missed_text = font.render(f"Missed: {missed}", True, (255,0,0))

    screen.blit(score_text, (20,20))
    screen.blit(success_text, (20,60))
    screen.blit(missed_text, (20,100))

    pygame.display.update()
    clock.tick(30)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

# -------------------------
# Save to Database
# -------------------------
end_time = datetime.datetime.now()
duration = int((end_time - start_time).total_seconds() / 60)

conn = sqlite3.connect("rehab.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient TEXT,
    date TEXT,
    start_time TEXT,
    duration INTEGER,
    score INTEGER,
    missed INTEGER,
    success_rate REAL
)
""")

cursor.execute("""
INSERT INTO sessions (patient, date, start_time, duration, score, missed, success_rate)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    patient_name,
    start_time.date(),
    start_time.time().strftime("%H:%M:%S"),
    duration,
    score,
    missed,
    success_rate
))

conn.commit()
conn.close()

cap.release()
pygame.quit()