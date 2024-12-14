import tkinter as tk
from PIL import Image, ImageTk
import pygame
import sys
import time
import math
import random
import os

WIDTH = 1024
HEIGHT = 768

def clear_():
    print("게임 클리어 화면 표시...")
    pygame.init()

    # 화면 설정
    SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Game Clear")

    # 색상
    BLACK = (0, 0, 0)

    # 성공 이미지 로드
    try:
        success_image = pygame.image.load("success.png")
        success_image = pygame.transform.scale(success_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except FileNotFoundError:
        print("success.png 파일을 찾을 수 없습니다.")
        pygame.quit()
        sys.exit()

    # 화면에 이미지 표시
    screen.fill(BLACK)
    screen.blit(success_image, (0, 0))
    pygame.display.flip()

    # 10초 대기
    pygame.time.wait(10000)

    # 게임 종료
    pygame.quit()
    print("게임 종료")
    sys.exit()


def run_cctv_game():
    # Pygame 초기화
    pygame.init()

    # 화면 크기 설정
    SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
    MAP_WIDTH, MAP_HEIGHT = 4096, 768  # 가로로 긴 맵
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("CCTV 감시망 피하기 게임 - 동서남북 캐릭터 및 랜덤 CCTV")

    def initialize_bgm():
        """BGM을 초기화하고 재생"""
        pygame.mixer.init()  # Pygame의 오디오 시스템 초기화
        try:
            pygame.mixer.music.load("cctvbgm.ogg")  # BGM 파일 경로 (ogg 형식)
            pygame.mixer.music.set_volume(0.1)  # 음량을 1.0으로 설정 (최대)
            pygame.mixer.music.play(-1)  # 무한 반복 재생
        except pygame.error as e:
            print(f"BGM을 불러오는 데 실패했습니다: {e}")

    # BGM 초기화
    initialize_bgm()

    # FPS 설정
    clock = pygame.time.Clock()
    FPS = 60

    # 색상 정의
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)

    background_image = pygame.image.load("badak2.png")  # 배경 이미지 경로
    background_image = pygame.transform.scale(background_image, (MAP_WIDTH, MAP_HEIGHT))  # 맵 크기로 조정

    # 캐릭터 이미지 로드
    character_images = {
        "left": pygame.image.load("prof_left.png"),
        "right": pygame.image.load("prof_right.png"),
        "up": pygame.image.load("prof_up.png"),
        "down": pygame.image.load("prof_down.png"),
    }

    # 이미지 크기 조정
    character_images = {key: pygame.transform.scale(img, (50, 50)) for key, img in character_images.items()}

    # 캐릭터 설정
    player_pos = [50, SCREEN_HEIGHT // 2]
    player_speed = 5
    player_size = 50
    current_direction = "right"  # 초기 방향

    # 스크롤 설정
    camera_offset = [0, 0]

    cctv_image = pygame.image.load("cctv.png")  # CCTV 이미지 경로
    cctv_image = pygame.transform.scale(cctv_image, (40, 40))  # 크기 조정

    def generate_random_cctvs(num_cctvs, min_distance, max_attempts=100000):
        cctvs = []
        attempts = 0  # 시도 횟수 카운트

        while len(cctvs) < num_cctvs and attempts < max_attempts:
            attempts += 1
            x = random.randint(100, MAP_WIDTH - 200)
            y = random.randint(100, MAP_HEIGHT - 200)

            # 다른 CCTV들과의 거리 검사
            valid = True
            for cctv in cctvs:
                existing_x, existing_y = cctv["pos"]
                distance = math.hypot(x - existing_x, y - existing_y)
                if distance < min_distance:
                    valid = False
                    break

            if valid:
                angle = random.randint(0, 360)  # 랜덤 각도
                fov = random.randint(45, 120)  # 랜덤 시야각
                view_range = random.randint(150, 300)  # 랜덤 감시 거리
                rotation_speed = random.uniform(0.5, 2)  # 회전 속도
                cctvs.append({
                    "pos": [x, y],
                    "angle": angle,
                    "fov": fov,
                    "view_range": view_range,
                    "rotation_speed": rotation_speed,
                })

        # CCTV 개수 부족 경고
        if len(cctvs) < num_cctvs:
            print(f"경고: {len(cctvs)}개의 CCTV만 배치되었습니다. (요청: {num_cctvs}, 최대 시도: {max_attempts})")

        return cctvs

    # CCTV 설정
    cctvs = generate_random_cctvs(5, 300)  # CCTV 20개, 최소 간격 300

    # 안전한 플레이어 시작 위치 생성
    def generate_safe_start(cctvs, safe_distance):
        while True:
            x = random.randint(50, 300)  # 맵의 시작 지점에서만 위치 선택
            y = random.randint(50, SCREEN_HEIGHT - 50)
            safe = True
            for cctv in cctvs:
                cctv_x, cctv_y = cctv["pos"]
                distance = math.hypot(x - cctv_x, y - cctv_y)
                if distance < safe_distance:  # 감시 범위와 안전 거리 확인
                    safe = False
                    break
            if safe:
                return [x, y]

    player_pos = generate_safe_start(cctvs, 350)  # 플레이어와 CCTV 간 최소 안전 거리 350

    # 목적지 설정
    goal_rect = pygame.Rect(MAP_WIDTH - 100, SCREEN_HEIGHT // 2 - 25, 50, 50)

    # 게임 상태
    game_over = False
    win = False

    def draw_background():
        original_width = background_image.get_width()
        original_height = background_image.get_height()

        target_width = int(SCREEN_WIDTH / 2)
        target_height = SCREEN_HEIGHT
        scaled_background = pygame.transform.scale(background_image, (target_width, target_height))

        bg_width = scaled_background.get_width()
        bg_height = scaled_background.get_height()

        for x in range(0, MAP_WIDTH, bg_width):
            for y in range(0, MAP_HEIGHT, bg_height):
                screen.blit(scaled_background, (x - camera_offset[0], y - camera_offset[1]))

    def draw_player():
        screen.blit(
            character_images[current_direction],
            (player_pos[0] - camera_offset[0], player_pos[1] - camera_offset[1])
        )

    def draw_cctv():
        for cctv in cctvs:
            x, y = cctv["pos"]
            screen.blit(cctv_image, (x - camera_offset[0] - 20, y - camera_offset[1] - 20))

            fov = math.radians(cctv["fov"])
            half_fov = fov / 2
            angle = math.radians(cctv["angle"])
            range_length = cctv["view_range"]

            apex = (x - camera_offset[0], y - camera_offset[1])
            left_point = (
                x + range_length * math.cos(angle - half_fov) - camera_offset[0],
                y - range_length * math.sin(angle - half_fov) - camera_offset[1],
            )
            right_point = (
                x + range_length * math.cos(angle + half_fov) - camera_offset[0],
                y - range_length * math.sin(angle + half_fov) - camera_offset[1],
            )

            pygame.draw.polygon(screen, (255, 200, 200, 128), [apex, left_point, right_point], 0)

    def rotate_cctv():
        for cctv in cctvs:
            cctv["angle"] = (cctv["angle"] + cctv["rotation_speed"]) % 360

    def check_collision():
        player_rect = pygame.Rect(player_pos[0], player_pos[1], player_size, player_size)
        for cctv in cctvs:
            x, y = cctv["pos"]
            distance = math.hypot(player_pos[0] - x, player_pos[1] - y)
            if distance <= cctv["view_range"]:
                dx = player_pos[0] - x
                dy = y - player_pos[1]
                angle_to_player = math.degrees(math.atan2(dy, dx)) % 360
                start_angle = (cctv["angle"] - cctv["fov"] / 2) % 360
                end_angle = (cctv["angle"] + cctv["fov"] / 2) % 360
                if start_angle < end_angle:
                    if start_angle <= angle_to_player <= end_angle:
                        return True
                else:
                    if angle_to_player >= start_angle or angle_to_player <= end_angle:
                        return True
        return False

    def draw_goal():
        pygame.draw.rect(screen, GREEN, (
            goal_rect.x - camera_offset[0],
            goal_rect.y - camera_offset[1],
            goal_rect.width,
            goal_rect.height
        ))

    while True:
        draw_background()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player_pos[0] > 0:
            player_pos[0] -= player_speed
            current_direction = "left"
        if keys[pygame.K_RIGHT] and player_pos[0] < MAP_WIDTH - player_size:
            player_pos[0] += player_speed
            current_direction = "right"
        if keys[pygame.K_UP] and player_pos[1] > 0:
            player_pos[1] -= player_speed
            current_direction = "up"
        if keys[pygame.K_DOWN] and player_pos[1] < SCREEN_HEIGHT - player_size:
            player_pos[1] += player_speed
            current_direction = "down"

        rotate_cctv()

        camera_offset[0] = max(0, min(player_pos[0] - SCREEN_WIDTH // 2, MAP_WIDTH - SCREEN_WIDTH))
        camera_offset[1] = max(0, min(player_pos[1] - SCREEN_HEIGHT // 2, MAP_HEIGHT - SCREEN_HEIGHT))

        if check_collision():
            game_over = True

        player_rect = pygame.Rect(player_pos[0], player_pos[1], player_size, player_size)
        if player_rect.colliderect(goal_rect):
            win = True

        if game_over:
            font = pygame.font.SysFont(None, 75)
            game_over_text = font.render("GAME OVER", True, RED)
            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 50))
            pygame.display.flip()
            continue

        if win:
            font = pygame.font.SysFont(None, 75)
            win_text = font.render("YOU WIN!", True, GREEN)
            screen.blit(win_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 50))
            pygame.display.flip()
            clear_()
            continue

        draw_player()
        draw_cctv()
        draw_goal()

        pygame.display.flip()
        clock.tick(FPS)

def show_black_screen(duration=2):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    screen.fill((0, 0, 0))  # 검은색으로 채우기
    pygame.display.flip()
    time.sleep(duration)  # duration 초 동안 대기
    pygame.quit()

def run_1f_floor():
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption("1st Floor")

    # 배경 및 캐릭터 이미지 로드
    try:
        hallway_bg = pygame.image.load("hallway.png")
        hallway_bg = pygame.transform.scale(hallway_bg, (1024, 768))
        character_up = pygame.image.load("prof_up.png")
        character_down = pygame.image.load("prof_down.png")
        character_left = pygame.image.load("prof_left.png")
        character_right = pygame.image.load("prof_right.png")
        character = pygame.transform.scale(character_down, (100, 200))
        cctv_image = pygame.image.load("professor_cctv.png")
        cctv_image = pygame.transform.scale(cctv_image, (1024, 768))  # 화면 크기에 맞게 조정
    except FileNotFoundError as e:
        print(f"파일을 찾을 수 없습니다: {e}")
        pygame.quit()
        sys.exit()

    # 캐릭터 초기 위치 및 속성
    character_x, character_y = 500, 500
    character_speed = 5

    # 빨간색 박스 설정
    red_box = pygame.Rect(300, 300, 50, 50)  # 박스 위치와 크기 설정

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 키 입력 처리
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            character_y -= character_speed
            character = pygame.transform.scale(character_up, (100, 200))
        if keys[pygame.K_DOWN]:
            character_y += character_speed
            character = pygame.transform.scale(character_down, (100, 200))
        if keys[pygame.K_LEFT]:
            character_x -= character_speed
            character = pygame.transform.scale(character_left, (100, 200))
        if keys[pygame.K_RIGHT]:
            character_x += character_speed
            character = pygame.transform.scale(character_right, (100, 200))

        # 화면 경계 제한
        character_x = max(0, min(character_x, 1024 - 100))
        character_y = max(0, min(character_y, 768 - 200))

        # 캐릭터와 빨간 박스 충돌 감지
        character_rect = pygame.Rect(character_x, character_y, 100, 200)
        if character_rect.colliderect(red_box):
            print("충돌 감지! CCTV 화면 출력 중...")
            # professor_cctv.png 출력
            screen.blit(cctv_image, (0, 0))
            pygame.display.flip()
            pygame.time.wait(5000)  # 5초 대기
            run_cctv_game()  # CCTV 게임 실행
            running = False  # 현재 게임 루프 종료

        # 화면 업데이트
        screen.blit(hallway_bg, (0, 0))
        pygame.draw.rect(screen, (255, 0, 0), red_box)  # 빨간 박스 그리기
        screen.blit(character, (character_x, character_y))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

def show_falling_professor():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Falling Professor")
    
    try:
        # 이미지 로드 및 크기 조정
        falling_image = pygame.image.load("falling_professor.png")
        falling_image = pygame.transform.scale(falling_image, (WIDTH, HEIGHT))
    except FileNotFoundError as e:
        print(f"falling_professor.png 파일을 찾을 수 없습니다: {e}")
        pygame.quit()
        sys.exit()

    # 화면에 이미지 출력
    screen.blit(falling_image, (0, 0))
    pygame.display.flip()

    # 5초 대기
    time.sleep(5)
    pygame.quit()

def run_2nd_floor():
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption("2nd Floor")

    # 배경 및 캐릭터 이미지 로드
    try:
        hallway_bg = pygame.image.load("hallway.png")
        hallway_bg = pygame.transform.scale(hallway_bg, (1024, 768))
        character_up = pygame.image.load("prof_up.png")
        character_down = pygame.image.load("prof_down.png")
        character_left = pygame.image.load("prof_left.png")
        character_right = pygame.image.load("prof_right.png")
        character = pygame.transform.scale(character_down, (100, 200))
    except FileNotFoundError as e:
        print(f"파일을 찾을 수 없습니다: {e}")
        pygame.quit()
        sys.exit()

    # 캐릭터 초기 위치 및 속성
    character_x, character_y = 500, 500
    character_speed = 5

    # 빨간 네모 설정
    red_box = pygame.Rect(300, 300, 50, 50)  # 빨간 네모의 위치와 크기

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 키 입력 처리
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            character_y -= character_speed
            character = pygame.transform.scale(character_up, (100, 200))
        if keys[pygame.K_DOWN]:
            character_y += character_speed
            character = pygame.transform.scale(character_down, (100, 200))
        if keys[pygame.K_LEFT]:
            character_x -= character_speed
            character = pygame.transform.scale(character_left, (100, 200))
        if keys[pygame.K_RIGHT]:
            character_x += character_speed
            character = pygame.transform.scale(character_right, (100, 200))

        # 화면 경계 제한
        character_x = max(0, min(character_x, 1024 - 100))
        character_y = max(0, min(character_y, 768 - 200))

        # 충돌 체크
        character_rect = pygame.Rect(character_x, character_y, 100, 200)
        if character_rect.colliderect(red_box):
            print("Collision with red box! Showing falling professor...")
            show_falling_professor()  # Falling Professor 이미지 표시
            run_lost_game()  # 빨간 네모와 충돌 시 Lost Item Game 실행
            running = False

        # 화면 업데이트
        screen.blit(hallway_bg, (0, 0))
        screen.blit(character, (character_x, character_y))
        pygame.draw.rect(screen, (255, 0, 0), red_box)  # 빨간 네모 그리기
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

def run_2f():
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption("2nd Floor")

    # 배경 및 캐릭터 이미지 로드
    try:
        hallway_bg = pygame.image.load("hallway.png")
        hallway_bg = pygame.transform.scale(hallway_bg, (1024, 768))
        character_up = pygame.image.load("prof_up.png")
        character_down = pygame.image.load("prof_down.png")
        character_left = pygame.image.load("prof_left.png")
        character_right = pygame.image.load("prof_right.png")
        talk_bubble = pygame.image.load("talk4.png")  # 말풍선 이미지 로드
        talk_bubble = pygame.transform.scale(talk_bubble, (480, 320))  # 말풍선 크기
        character = pygame.transform.scale(character_down, (100, 200))
    except FileNotFoundError as e:
        print(f"파일을 찾을 수 없습니다: {e}")
        pygame.quit()
        sys.exit()

    # 캐릭터 초기 위치 및 속성
    character_x, character_y = 500, 500
    character_speed = 5

    # 파란색 네모 설정
    blue_box = pygame.Rect(500, 200, 50, 50)

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 키 입력 처리
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            character_y -= character_speed
            character = pygame.transform.scale(character_up, (100, 200))
        if keys[pygame.K_DOWN]:
            character_y += character_speed
            character = pygame.transform.scale(character_down, (100, 200))
        if keys[pygame.K_LEFT]:
            character_x -= character_speed
            character = pygame.transform.scale(character_left, (100, 200))
        if keys[pygame.K_RIGHT]:
            character_x += character_speed
            character = pygame.transform.scale(character_right, (100, 200))

        # 화면 경계 제한
        character_x = max(0, min(character_x, 1024 - 100))
        character_y = max(0, min(character_y, 768 - 200))

        # 충돌 체크
        character_rect = pygame.Rect(character_x, character_y, 100, 200)
        if character_rect.colliderect(blue_box):
            run_1f_floor()  # 파란 박스와 충돌 시 1층으로 이동
            running = False

        # 화면 업데이트
        screen.blit(hallway_bg, (0, 0))
        screen.blit(character, (character_x, character_y))
        pygame.draw.rect(screen, (0, 0, 255), blue_box)  # 파란 네모 그리기

        # 말풍선 그리기 (캐릭터 머리 위에 위치)
        talk_bubble_x = character_x - 190  # 말풍선이 캐릭터 중앙에 맞도록 조정
        talk_bubble_y = character_y - 330  # 말풍선이 캐릭터 머리 위로 이동
        screen.blit(talk_bubble, (talk_bubble_x, talk_bubble_y))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

def run_3f():
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption("3rd Floor")

    # 배경 및 캐릭터 이미지 로드
    try:
        hallway_bg = pygame.image.load("hallway.png")
        hallway_bg = pygame.transform.scale(hallway_bg, (1024, 768))
        character_up = pygame.image.load("prof_up.png")
        character_down = pygame.image.load("prof_down.png")
        character_left = pygame.image.load("prof_left.png")
        character_right = pygame.image.load("prof_right.png")
        talk_bubble = pygame.image.load("talk3.png")  # 말풍선 이미지 로드
        talk_bubble = pygame.transform.scale(talk_bubble, (480, 320))  # 말풍선 크기
        character = pygame.transform.scale(character_down, (100, 200))
    except FileNotFoundError as e:
        print(f"파일을 찾을 수 없습니다: {e}")
        pygame.quit()
        sys.exit()

    # 캐릭터 초기 위치 및 속성
    character_x, character_y = 500, 500
    character_speed = 5

    # 파란색 네모 설정
    blue_box = pygame.Rect(300, 300, 50, 50)

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 키 입력 처리
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            character_y -= character_speed
            character = pygame.transform.scale(character_up, (100, 200))
        if keys[pygame.K_DOWN]:
            character_y += character_speed
            character = pygame.transform.scale(character_down, (100, 200))
        if keys[pygame.K_LEFT]:
            character_x -= character_speed
            character = pygame.transform.scale(character_left, (100, 200))
        if keys[pygame.K_RIGHT]:
            character_x += character_speed
            character = pygame.transform.scale(character_right, (100, 200))

        # 화면 경계 제한
        character_x = max(0, min(character_x, 1024 - 100))
        character_y = max(0, min(character_y, 768 - 200))

        # 충돌 체크
        character_rect = pygame.Rect(character_x, character_y, 100, 200)
        if character_rect.colliderect(blue_box):
            run_2nd_floor()  # 파란 네모와 충돌 시 2층으로 이동
            running = False

        # 화면 업데이트
        screen.blit(hallway_bg, (0, 0))
        screen.blit(character, (character_x, character_y))
        pygame.draw.rect(screen, (0, 0, 255), blue_box)  # 파란 네모 그리기

        # 말풍선 그리기 (캐릭터 머리 위에 위치)
        talk_bubble_x = character_x - 190  # 말풍선이 캐릭터 중앙에 맞도록 조정
        talk_bubble_y = character_y - 330  # 말풍선이 캐릭터 머리 위로 이동
        screen.blit(talk_bubble, (talk_bubble_x, talk_bubble_y))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

def run_3th_floor():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("3rd Floor")

    pygame.mixer.music.stop()
    
    try:
        hallway_bg = pygame.image.load("hallway.png")
        hallway_bg = pygame.transform.scale(hallway_bg, (WIDTH, HEIGHT))
        professor_up = pygame.image.load("prof_up.png")
        professor_up = pygame.transform.scale(professor_up, (100, 200))
        professor_down = pygame.image.load("prof_down.png")
        professor_down = pygame.transform.scale(professor_down, (100, 200))
        professor_left = pygame.image.load("prof_left.png")
        professor_left = pygame.transform.scale(professor_left, (100, 200))
        professor_right = pygame.image.load("prof_right.png")
        professor_right = pygame.transform.scale(professor_right, (100, 200))
        earthquake_bg = pygame.image.load("earthquake_classroom.png")
        earthquake_bg = pygame.transform.scale(earthquake_bg, (WIDTH, HEIGHT))
    except FileNotFoundError as e:
        print(f"파일을 찾을 수 없습니다: {e}")
        pygame.quit()
        sys.exit()

    professor_x, professor_y = 512, 500
    professor_image = professor_down

    red_box = pygame.Rect(400, 300, 50, 50)  # 빨간 네모 위치와 크기

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            professor_y -= 1
            professor_image = professor_up
        if keys[pygame.K_DOWN]:
            professor_y += 1
            professor_image = professor_down
        if keys[pygame.K_LEFT]:
            professor_x -= 1
            professor_image = professor_left
        if keys[pygame.K_RIGHT]:
            professor_x += 1
            professor_image = professor_right

        professor_x = max(0, min(professor_x, WIDTH - 100))
        professor_y = max(0, min(professor_y, HEIGHT - 200))

        professor_rect = pygame.Rect(professor_x, professor_y, 100, 200)
        if professor_rect.colliderect(red_box):
            # 지진 배경 화면 출력
            screen.blit(earthquake_bg, (0, 0))
            pygame.display.flip()
            pygame.time.wait(5000)  # 5초 대기
            run_maze_game()  # 미로 게임 실행
            running = False

        screen.blit(hallway_bg, (0, 0))
        screen.blit(professor_image, (professor_x, professor_y))
        pygame.draw.rect(screen, (255, 0, 0), red_box)  # 빨간 네모 그리기

        pygame.display.flip()

def run_4th_floor():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("4th Floor")
    
    pygame.mixer.music.stop()

    try:
        hallway_bg = pygame.image.load("hallway.png")
        hallway_bg = pygame.transform.scale(hallway_bg, (WIDTH, HEIGHT))
        professor_up = pygame.image.load("prof_up.png")
        professor_up = pygame.transform.scale(professor_up, (100, 200))
        professor_down = pygame.image.load("prof_down.png")
        professor_down = pygame.transform.scale(professor_down, (100, 200))
        professor_left = pygame.image.load("prof_left.png")
        professor_left = pygame.transform.scale(professor_left, (100, 200))
        professor_right = pygame.image.load("prof_right.png")
        professor_right = pygame.transform.scale(professor_right, (100, 200))
        talk_box = pygame.image.load("talk2.png")
        talk_box = pygame.transform.scale(talk_box, (1200, 600))
    except FileNotFoundError as e:
        print(f"파일을 찾을 수 없습니다: {e}")
        pygame.quit()
        sys.exit()

    professor_x, professor_y = 512, 500
    professor_image = professor_down
    show_talk_box = True

    blue_box = pygame.Rect(400, 600, 100, 50)  # 파란 네모 위치와 크기

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            professor_y -= 1
            professor_image = professor_up
        if keys[pygame.K_DOWN]:
            professor_y += 1
            professor_image = professor_down
        if keys[pygame.K_LEFT]:
            professor_x -= 1
            professor_image = professor_left
        if keys[pygame.K_RIGHT]:
            professor_x += 1
            professor_image = professor_right
        if keys[pygame.K_RETURN]:
            show_talk_box = not show_talk_box

        professor_x = max(0, min(professor_x, WIDTH - 100))
        professor_y = max(0, min(professor_y, HEIGHT - 200))

        professor_rect = pygame.Rect(professor_x, professor_y, 100, 200)
        if professor_rect.colliderect(blue_box):
            run_3th_floor()
            running = False

        screen.blit(hallway_bg, (0, 0))
        screen.blit(professor_image, (professor_x, professor_y))
        pygame.draw.rect(screen, (0, 0, 255), blue_box)  # 파란 네모 그리기

        if show_talk_box:
            talk_box_x = professor_x - 550
            talk_box_y = professor_y - 450
            screen.blit(talk_box, (talk_box_x, talk_box_y))

        pygame.display.flip()

def run_snowstorm_game():
    SCREEN_WIDTH = WIDTH
    SCREEN_HEIGHT = HEIGHT
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Snowstorm Escape")

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    BROWN = (139, 69, 19)
    LIGHT_BLUE = (173, 216, 230)

    player_image_right = pygame.image.load("prof_right.png")
    player_image_left = pygame.image.load("prof_left.png")
    player_width = 120
    player_height = 120
    player_image_right = pygame.transform.scale(player_image_right, (player_width, player_height))
    player_image_left = pygame.transform.scale(player_image_left, (player_width, player_height))
    player_image = player_image_right

    player_x = 100
    player_y = SCREEN_HEIGHT - 200
    player_speed = 5
    player_jump = False
    jump_height = 22
    jump_count = 0

    floor_y = SCREEN_HEIGHT - 100
    obstacle_types = ["snow_pile", "snowman"]
    obstacles = []
    obstacle_speed = 5

    snowflakes = []
    snowflake_radius = 10
    snowflake_speed = 5

    score = 0
    font = pygame.font.Font(None, 36)

    clock = pygame.time.Clock()
    FPS = 60

    def add_obstacle():
        obstacle_type = random.choice(obstacle_types)
        obstacle_width = random.randint(50, 100)
        obstacle_height = random.randint(30, 60)
        obstacle_x = SCREEN_WIDTH
        obstacle_y = floor_y - obstacle_height
        obstacles.append({
            "type": obstacle_type,
            "x": obstacle_x,
            "y": obstacle_y,
            "width": obstacle_width,
            "height": obstacle_height
        })

    def add_snowflake():
        snowflake_x = random.randint(0, SCREEN_WIDTH)
        snowflake_y = 0
        snowflakes.append([snowflake_x, snowflake_y])

    def draw_text(text, x, y, color=WHITE):
        render = font.render(text, True, color)
        screen.blit(render, (x, y))

    def stage_clear():
        screen.fill(BLACK)
        draw_text("Stage Clear!", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2, WHITE)
        pygame.display.flip()
        pygame.time.wait(2000)
        run_4th_floor()
        pygame.quit()
        sys.exit()

    running = True
    frame_count = 0

    while running:
        screen.fill(BLACK)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player_x > 0:
            player_x -= player_speed
            player_image = player_image_left
        if keys[pygame.K_RIGHT] and player_x < SCREEN_WIDTH - player_width:
            player_x += player_speed
            player_image = player_image_right
        if not player_jump and keys[pygame.K_SPACE]:
            player_jump = True
            jump_count = jump_height

        if player_jump:
            player_y -= jump_count
            jump_count -= 1
            if jump_count < -jump_height:
                player_jump = False

        if frame_count % 120 == 0:
            add_obstacle()
        if frame_count % 30 == 0:
            add_snowflake()

        for obstacle in obstacles[:]:
            obstacle["x"] -= obstacle_speed
            if obstacle["x"] < -obstacle["width"]:
                obstacles.remove(obstacle)
                score += 1

            obstacle_rect = pygame.Rect(obstacle["x"], obstacle["y"], obstacle["width"], obstacle["height"])
            player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
            if player_rect.colliderect(obstacle_rect):
                running = False

        for snowflake in snowflakes[:]:
            snowflake[1] += snowflake_speed
            if snowflake[1] > SCREEN_HEIGHT:
                snowflakes.remove(snowflake)

            snowflake_rect = pygame.Rect(snowflake[0] - snowflake_radius, snowflake[1] - snowflake_radius,
                                         snowflake_radius * 2, snowflake_radius * 2)
            player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
            if player_rect.colliderect(snowflake_rect):
                running = False

        pygame.draw.rect(screen, BROWN, (0, floor_y, SCREEN_WIDTH, SCREEN_HEIGHT - floor_y))
        screen.blit(player_image, (player_x, player_y))

        for obstacle in obstacles:
            if obstacle["type"] == "snow_pile":
                pygame.draw.rect(screen, LIGHT_BLUE, (obstacle["x"], obstacle["y"], obstacle["width"], obstacle["height"]))
            elif obstacle["type"] == "snowman":
                pygame.draw.circle(screen, WHITE, (obstacle["x"] + obstacle["width"] // 2, obstacle["y"] + obstacle["height"] // 3), obstacle["width"] // 3)
                pygame.draw.circle(screen, WHITE, (obstacle["x"] + obstacle["width"] // 2, obstacle["y"] + 2 * obstacle["height"] // 3), obstacle["width"] // 2)

        for snowflake in snowflakes:
            pygame.draw.circle(screen, WHITE, (snowflake[0], snowflake[1]), snowflake_radius)

        draw_text(f"Score: {score}", 10, 10)

        if score >= 1: # 5
            stage_clear()

        pygame.display.flip()
        clock.tick(FPS)
        frame_count += 1

    pygame.quit()
    sys.exit()

def run_maze_game():
    global character, character_x, character_y

    # 초기화
    pygame.init()

    # 화면 설정
    screen_width, screen_height = 1024, 768
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("미로 탐험 & 카드 뒤집기 게임")

    # 색상
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    # 셀 크기 설정
    cell_width = 40
    cell_height = 40
    maze_rows = screen_height // cell_height
    maze_cols = screen_width // cell_width

    # 캐릭터 이미지 로드 함수
    def load_image(file_name, scale=None):
        try:
            image = pygame.image.load(file_name)
            if scale:
                image = pygame.transform.scale(image, scale)
            return image
        except FileNotFoundError:
            print(f"이미지 파일 {file_name}을 찾을 수 없습니다.")
            surface = pygame.Surface((cell_width, cell_height))
            surface.fill(BLACK)
            return surface

    # 캐릭터 이미지
    character_front = load_image("prof_down.png", (cell_width, cell_height))
    character_back = load_image("prof_down.png", (cell_width, cell_height))
    character_left = load_image("prof_left.png", (cell_width, cell_height))
    character_right = load_image("prof_right.png", (cell_width, cell_height))

    # 캐릭터 초기 설정
    character = character_front
    character_x, character_y = cell_width, cell_height
    character_speed = cell_width

    # 카드 게임 배경 및 이미지
    card_game_background = load_image("card_background.png", (screen_width, screen_height))
    card_back_image = load_image("card_back.png", (100, 150))
    card_front_images = [load_image(f"card_{i}.png", (100, 150)) for i in range(6)]

    # 미로 생성 (DFS 알고리즘 사용)
    def generate_maze(rows, cols):
        maze = [["#" for _ in range(cols)] for _ in range(rows)]
        stack = [(1, 1)]
        maze[1][1] = " "

        directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]
        while stack:
            current_row, current_col = stack[-1]
            random.shuffle(directions)
            for dr, dc in directions:
                new_row, new_col = current_row + dr, current_col + dc
                if 1 <= new_row < rows - 1 and 1 <= new_col < cols - 1 and maze[new_row][new_col] == "#":
                    maze[current_row + dr // 2][current_col + dc // 2] = " "
                    maze[new_row][new_col] = " "
                    stack.append((new_row, new_col))
                    break
            else:
                stack.pop()
        maze[1][1] = "S"
        maze[rows - 2][cols - 2] = "E"
        return maze

    # 미로 그리기
    def draw_maze(maze):
        for row in range(maze_rows):
            for col in range(maze_cols):
                if maze[row][col] == "#":
                    pygame.draw.rect(screen, BLACK, (col * cell_width, row * cell_height, cell_width, cell_height))
                elif maze[row][col] == "E":
                    pygame.draw.rect(screen, (255, 0, 0), (col * cell_width, row * cell_height, cell_width, cell_height))

    # 검은 화면 출력 함수
    def show_black_screen(duration=1):
        screen.fill(BLACK)
        pygame.display.flip()
        time.sleep(duration)

    # 카드 게임
    def card_game():
        card_width, card_height = 100, 150
        card_spacing = 20
        rows, cols = 3, 4
        cards = [i // 2 for i in range(rows * cols)]
        random.shuffle(cards)

        flipped_cards = []
        matched_cards = []

        total_width = cols * card_width + (cols - 1) * card_spacing
        start_x = (screen_width - total_width) // 2
        start_y = (screen_height - (rows * card_height + (rows - 1) * card_spacing)) // 2

        card_positions = [
            (start_x + col * (card_width + card_spacing), start_y + row * (card_height + card_spacing))
            for row in range(rows)
            for col in range(cols)
        ]

        font = pygame.font.Font(None, 36)
        start_time = time.time()
        time_limit = 60

        while True:
            elapsed_time = time.time() - start_time
            remaining_time = max(0, int(time_limit - elapsed_time))

            if remaining_time == 0:
                return False

            screen.blit(card_game_background, (0, 0))
            timer_text = font.render(f"Time: {remaining_time}s", True, BLACK)
            screen.blit(timer_text, (20, 20))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    for i, (x, y) in enumerate(card_positions):
                        if x <= mx <= x + card_width and y <= my <= y + card_height:
                            if i not in flipped_cards and i not in matched_cards:
                                flipped_cards.append(i)
                            if len(flipped_cards) == 2:
                                pygame.time.delay(500)
                                if cards[flipped_cards[0]] == cards[flipped_cards[1]]:
                                    matched_cards.extend(flipped_cards)
                                flipped_cards = []

            for i, (x, y) in enumerate(card_positions):
                if i in flipped_cards or i in matched_cards:
                    screen.blit(card_front_images[cards[i]], (x, y))
                else:
                    screen.blit(card_back_image, (x, y))

            if len(matched_cards) == len(cards):
                return True

            pygame.display.flip()

    # 미로 게임 메인 루프
    def maze_game():
        global character, character_x, character_y
        maze = generate_maze(maze_rows, maze_cols)
        clock = pygame.time.Clock()

        while True:
            screen.fill(WHITE)
            draw_maze(maze)
            screen.blit(character, (character_x, character_y))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            keys = pygame.key.get_pressed()
            new_x, new_y = character_x, character_y

            if keys[pygame.K_LEFT]:
                new_x -= character_speed
                character = character_left
            if keys[pygame.K_RIGHT]:
                new_x += character_speed
                character = character_right
            if keys[pygame.K_UP]:
                new_y -= character_speed
                character = character_back
            if keys[pygame.K_DOWN]:
                new_y += character_speed
                character = character_front

            col, row = new_x // cell_width, new_y // cell_height
            if maze[row][col] == " " or maze[row][col] == "E":
                character_x, character_y = new_x, new_y

            if maze[row][col] == "E":
                return True

            pygame.display.flip()
            clock.tick(30)

    # 실행 흐름
    if maze_game():
        if card_game():
            show_black_screen(1)
            run_3f()

def run_lost_game():
    # Initialize pygame
    pygame.init()

    # Screen dimensions
    SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Lost Item Game")

    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    BLUE = (0, 0, 255)

    # Function to safely load images
    def safe_load_image(path, size):
        try:
            image = pygame.image.load(path)
            return pygame.transform.scale(image, size)
        except pygame.error as e:
            print(f"Error loading image {path}: {e}")
            sys.exit()

    # Load assets
    character_images = {
        "up": safe_load_image("prof_up.png", (100, 100)),
        "down": safe_load_image("prof_down.png", (100, 100)),
        "left": safe_load_image("prof_left.png", (100, 100)),
        "right": safe_load_image("prof_right.png", (100, 100))
    }
    # 초기 캐릭터 방향 설정
    character = character_images["down"]

    backgrounds = {
        "classroom": safe_load_image("classroom.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
    }

    item_images = {
        "flashlight": safe_load_image("flashlight.png", (50, 50)),
        "glasses": safe_load_image("glasses.png", (50, 50)),
        "laptop": safe_load_image("laptop.png", (50, 50)),
        "tablet": safe_load_image("tablet.png", (50, 50)),
        "medicine": safe_load_image("medicine.png", (50, 50)),
        "book": safe_load_image("book.png", (50, 50))
    }

    # Game variables
    character_pos = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]  # x, y 위치
    character_speed = 5
    items = []
    found_items = []
    time_limit = 30
    font = pygame.font.Font(None, 36)
    clock = pygame.time.Clock()

    # Spawn items
    def spawn_items():
        nonlocal items
        items = []
        for name, image in item_images.items():
            items.append({
                "name": name,
                "image": image,
                "rect": image.get_rect(topleft=(
                    random.randint(50, SCREEN_WIDTH - 100),
                    random.randint(50, SCREEN_HEIGHT - 100)
                ))
            })

    # Draw items
    def draw_items():
        for item in items:
            screen.blit(item["image"], item["rect"])

    # Draw found items
    def draw_found_items():
        y_offset = 10
        for found_item in found_items:
            text_surface = font.render(found_item, True, BLACK)
            screen.blit(text_surface, (10, y_offset))
            y_offset += 30

    # Check collision
    def check_collision():
        nonlocal items, found_items
        character_rect = pygame.Rect(character_pos[0], character_pos[1], 100, 100)
        for item in items[:]:
            if character_rect.colliderect(item["rect"]):
                found_items.append(item["name"])
                items.remove(item)

    # Game loop
    def game_loop():
        nonlocal character_pos, items, character

        running = True
        spawn_items()
        start_ticks = pygame.time.get_ticks()

        while running:
            screen.fill(WHITE)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP]:
                character_pos[1] = max(0, character_pos[1] - character_speed)
                character = character_images["up"]
            if keys[pygame.K_DOWN]:
                character_pos[1] = min(SCREEN_HEIGHT - 100, character_pos[1] + character_speed)
                character = character_images["down"]
            if keys[pygame.K_LEFT]:
                character_pos[0] = max(0, character_pos[0] - character_speed)
                character = character_images["left"]
            if keys[pygame.K_RIGHT]:
                character_pos[0] = min(SCREEN_WIDTH - 100, character_pos[0] + character_speed)
                character = character_images["right"]

            # Draw classroom background
            screen.blit(backgrounds["classroom"], (0, 0))
            draw_items()
            draw_found_items()
            check_collision()

            # Check if all items are collected
            if len(items) == 0:
                screen.fill(BLACK)
                clear_text = font.render("Clear!", True, BLUE)
                screen.blit(clear_text, (SCREEN_WIDTH // 2 - clear_text.get_width() // 2, SCREEN_HEIGHT // 2))
                pygame.display.flip()
                pygame.time.wait(2000)
                running = False
                return True  # 게임 클리어

            # Check time limit
            elapsed_time = (pygame.time.get_ticks() - start_ticks) / 1000
            if elapsed_time > time_limit:
                running = False

            screen.blit(character, character_pos)
            pygame.display.flip()
            clock.tick(30)

        screen.fill(WHITE)
        game_over_text = font.render("Game Over!", True, BLACK)
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        pygame.time.wait(3000)
        return False  # 게임 실패

    # Start the game loop
    if game_loop():
        run_2f()  # 게임 클리어 시 2층으로 이동
    else:
        pygame.quit()  # 게임 종료

def run_pygame_game():
    # Pygame 초기화
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Professor's School Escape")
    
    # 배경 이미지 로드
    try:
        hallway_bg = pygame.image.load("hallway.png")
        hallway_bg = pygame.transform.scale(hallway_bg, (WIDTH, HEIGHT))
        snowy_bg = pygame.image.load("snowy_classroom.png")
        snowy_bg = pygame.transform.scale(snowy_bg, (WIDTH, HEIGHT))
    except FileNotFoundError:
        print("hallway.png 또는 snowy_classroom.png 파일을 찾을 수 없습니다.")
        pygame.quit()
        sys.exit()
    
    # 교수님 캐릭터 이미지 로드
    try:
        professor_up = pygame.image.load("prof_up.png")
        professor_up = pygame.transform.scale(professor_up, (100, 200))
        professor_down = pygame.image.load("prof_down.png")
        professor_down = pygame.transform.scale(professor_down, (100, 200))
        professor_left = pygame.image.load("prof_left.png")
        professor_left = pygame.transform.scale(professor_left, (100, 200))
        professor_right = pygame.image.load("prof_right.png")
        professor_right = pygame.transform.scale(professor_right, (100, 200))
    except FileNotFoundError:
        print("교수님 캐릭터 이미지 파일을 찾을 수 없습니다.")
        pygame.quit()
        sys.exit()

    # 대사 박스 이미지 로드
    try:
        talk_box = pygame.image.load("talk1.png")
        talk_box = pygame.transform.scale(talk_box, (600, 300))  # 말풍선 크기
    except FileNotFoundError:
        print("talk1.png 파일을 찾을 수 없습니다.")
        pygame.quit()
        sys.exit()

    # 초기 설정
    professor_x, professor_y = 512, 500  # 캐릭터 초기 위치
    professor_image = professor_down  # 초기 방향
    show_talk_box = True  # 말풍선 표시 여부
    collision = False  # 충돌 여부
    speed = 0.5  # 이동 속도

    # 빨간 네모 설정
    red_box = pygame.Rect(320, 400, 50, 50)  # 빨간 네모의 위치와 크기

    # 방향키 상태 추적
    key_states = {"up": False, "down": False, "left": False, "right": False}

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # 키 입력 처리
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:  # Enter 키로 말풍선 숨기기/표시 전환
                    show_talk_box = not show_talk_box
                elif event.key == pygame.K_UP:
                    professor_image = professor_up
                    key_states["up"] = True
                elif event.key == pygame.K_DOWN:
                    professor_image = professor_down
                    key_states["down"] = True
                elif event.key == pygame.K_LEFT:
                    professor_image = professor_left
                    key_states["left"] = True
                elif event.key == pygame.K_RIGHT:
                    professor_image = professor_right
                    key_states["right"] = True

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_UP:
                    key_states["up"] = False
                elif event.key == pygame.K_DOWN:
                    key_states["down"] = False
                elif event.key == pygame.K_LEFT:
                    key_states["left"] = False
                elif event.key == pygame.K_RIGHT:
                    key_states["right"] = False

        # 캐릭터 이동 처리
        if key_states["up"]:
            professor_y -= speed
        if key_states["down"]:
            professor_y += speed
        if key_states["left"]:
            professor_x -= speed
        if key_states["right"]:
            professor_x += speed

        # 화면 경계 제한
        professor_x = max(0, min(professor_x, WIDTH - 100))
        professor_y = max(0, min(professor_y, HEIGHT - 200))

        # 충돌 감지
        professor_rect = pygame.Rect(professor_x, professor_y, 100, 200)
        if professor_rect.colliderect(red_box):
            collision = True

        # 화면 그리기
        if collision:
            screen.fill((0, 0, 0))  # 검은 화면 출력
            pygame.display.flip()
            time.sleep(1)  # 1초 대기
            screen.blit(snowy_bg, (0, 0))  # snowy_classroom 배경으로 변경
            pygame.display.flip()
            pygame.display.flip()
            pygame.mixer.music.load("snow.ogg")
            pygame.mixer.music.play(-1)  # BGM 실행
            time.sleep(5)  # snowy_classroom 유지
            run_snowstorm_game()
            time.sleep(5)  # 5초 대기
            running = False  # 게임 종료
        else:
            screen.blit(hallway_bg, (0, 0))  # 기본 배경
            pygame.draw.rect(screen, (255, 0, 0), red_box)  # 빨간 네모 그리기
            screen.blit(professor_image, (professor_x, professor_y))  # 캐릭터 그리기

            # 대사 박스 표시
            if show_talk_box:
                talk_box_x = professor_x - 300
                talk_box_y = professor_y - 350
                screen.blit(talk_box, (talk_box_x, talk_box_y))  # 말풍선 표시

        pygame.display.flip()  # 화면 업데이트
    run_snowstorm_game()

def start_game():
    root.destroy()
    show_black_screen()
    run_pygame_game()

root = tk.Tk()
root.title("Game Start Screen")
root.geometry(f"{WIDTH}x{HEIGHT}")

canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT)
canvas.pack()

try:
    image = Image.open("game_main.png")
    image = image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
    bg_image = ImageTk.PhotoImage(image)
    canvas.create_image(0, 0, anchor=tk.NW, image=bg_image)
except FileNotFoundError:
    print("game_main.png 파일을 찾을 수 없습니다.")

start_button = tk.Button(root, text="Start Game", font=("Arial", 16), command=start_game)
start_button_window = canvas.create_window(WIDTH // 2, HEIGHT - 100, anchor=tk.CENTER, window=start_button)

root.mainloop()
