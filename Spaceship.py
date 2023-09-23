import pygame
from random import random, randint, choice
from pathlib import Path

# Gracz gra do śmierci, zabijając tyle przeciwników ile może
pygame.mixer.init()
pygame.font.init()
# inicjacja dźwięku i napisów

FONT1 = pygame.font.SysFont("comicsans", 40)
# taka fajna czcionka

WIDTH, HEIGHT = 500, 800
SPACESHIP_WIDTH, SPACESHIP_HEIGHT = 55, 35
BUFF_WIDTH, BUFF_HEIGHT = 50, 50
# wymiary hitboxów wszystkiego

VEL = 5
BULLET_VEL = 8
ENEMY_VEL = 1
# wszystkie prędkości w grze

PLAYER_BULLET_COLOR = (255, 255, 0)
ENEMY_BULLET_COLOR = (255, 0, 255)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
# kolory, których używam
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Spaceship")
# Okno o nazwie Spaceship


class Files:  # wszystkie pliki potrzebne do uruchomienia gry
    def __init__(self):
        ROOT_DIR = Path("Spaceship").parent  # utworzenie ścieżki do głównego folderu
        SOUND_FILES = ROOT_DIR / "audio"  # folder z audio
        IMAGES = ROOT_DIR / "images"  # folder ze zdjęciami
        self.BACKGROUND = pygame.transform.scale(
            pygame.transform.rotate(pygame.image.load(str(IMAGES / "space.png")), 90),
            (WIDTH, HEIGHT),
        )  # tło
        self.ENEMY_SPACESHIP_IMAGE = pygame.transform.scale(
            pygame.image.load(str(IMAGES / "enemy1_spaceship.png")),
            (SPACESHIP_WIDTH + 10, SPACESHIP_HEIGHT + 10),
        )  # obraz przeciwnika
        self.PLAYER_SPACESHIP_IMAGE = pygame.transform.rotate(
            pygame.transform.scale(
                pygame.image.load(str(IMAGES / "player_spaceship.png")),
                (SPACESHIP_WIDTH, SPACESHIP_HEIGHT),
            ),
            180,
        )  # obraz gracza

        self.BULLET_BUFF_IMAGE = pygame.transform.scale(
            pygame.image.load(str(IMAGES / "buff_bullet.png")),
            (BUFF_WIDTH, BUFF_HEIGHT),
        )
        self.SHOOTING_BUFF_IMAGE = pygame.transform.scale(
            pygame.image.load(str(IMAGES / "buff_shooting.png")),
            (BUFF_WIDTH, BUFF_HEIGHT),
        )
        self.HEALTH_BUFF_IMAGE = pygame.transform.scale(
            pygame.image.load(str(IMAGES / "buff_health.png")),
            (BUFF_WIDTH, BUFF_HEIGHT),
        )
        # obrazy buffów

        self.BULLET_FIRE_SOUND = pygame.mixer.Sound(
            str(SOUND_FILES / "enemy_dies.mp3")
        )  # dźwięk trafienia w przeciwnika
        self.PLAYER_HIT_SOUND = pygame.mixer.Sound(
            str(SOUND_FILES / "player_hit.mp3")
        )  # dźwięk trafienia w gracza


class Player:  # wszystkie dane gracza
    def __init__(self):
        self.x = WIDTH // 2 - SPACESHIP_WIDTH // 2
        self.y = HEIGHT * 3 // 4
        # koordynaty początkowe gracza
        self.rect = pygame.Rect(
            self.x, self.y, SPACESHIP_WIDTH, SPACESHIP_HEIGHT
        )  # hitbox gracza

        self.shooting_interval = (
            1  # tyle będzie dodawane do shooting_timer 60 razy na sekundę
        )
        self.shooting_timer = 0  # czas od ostatniego strzału
        self.shots = 1  # ilość strzałów jaką gracz może wystrzelić za jednym razem

        self.health = 10  # zdrowie gracza

    def movement(self, keys_pressed):
        if keys_pressed[pygame.K_w] and self.y + 5 > HEIGHT // 2:  # góra
            self.y -= VEL
        if keys_pressed[pygame.K_s] and self.y + SPACESHIP_HEIGHT + 5 < HEIGHT:  # dół
            self.y += VEL
        if keys_pressed[pygame.K_a] and self.x - 5 > 0:  # lewo
            self.x -= VEL
        if keys_pressed[pygame.K_d] and self.x + SPACESHIP_WIDTH + 5 < WIDTH:  # prawo
            self.x += VEL
        self.rect = pygame.Rect(self.x, self.y, SPACESHIP_WIDTH, SPACESHIP_HEIGHT)

    def shoot(self, gamestate):
        if self.shooting_timer >= 60:
            for shot in range(1, self.shots + 1):
                player_bullet = pygame.Rect(
                    self.x + SPACESHIP_WIDTH // (self.shots + 1) * (shot),
                    self.y - 10,
                    2,
                    10,
                )
                gamestate.player_bullets.append(player_bullet)
            self.shooting_timer = 0
        self.shooting_timer += self.shooting_interval
        # po osiągnięciu przez timer wartości 60, do listy z pociskami gracza dodawane są strzały, które pojawiają się równo ułożone przed graczem. Licznik się wtedy zeruje.


class Enemy:  # dane i funkcje przeciwników
    def __init__(self, row, col, gamestate):
        self.x = row * WIDTH // (gamestate.enemy_rows + 1)
        self.y = col * (SPACESHIP_HEIGHT + 10)
        # te wartości są podawane przy tworzeniu przeciwnika
        self.rect = pygame.Rect(
            self.x, self.y, SPACESHIP_WIDTH, SPACESHIP_HEIGHT
        )  # hitbox
        self.at_target = False  # czy doleciał do celu
        self.target_x = randint(0, WIDTH - SPACESHIP_WIDTH)  # cel x
        self.target_y = randint(
            0, HEIGHT - SPACESHIP_HEIGHT - HEIGHT // 2
        )  # cel y. Górna połowa okna

        self.shooting_timer = 0  # licznik czasu czy przeciwnik może strzelić

        self.health = (
            gamestate.level
        )  # zdrowie przeciwników jest uzależnione od poziomu gry

    def change_position(self):
        if self.at_target:  # cel przeciwników zmienia się po doleceniu do celu
            self.target_x = randint(0, WIDTH - SPACESHIP_WIDTH)
            self.target_y = randint(0, HEIGHT - SPACESHIP_HEIGHT - HEIGHT // 2)
            self.at_target = False
        else:  # sprawdza w którą stronę ma lecieć przeciwnik i przesuwa go w stronę celu
            if self.x < self.target_x:
                self.x += ENEMY_VEL
            elif self.x > self.target_x:
                self.x -= ENEMY_VEL
            if self.y < self.target_y:
                self.y += ENEMY_VEL
            elif self.y > self.target_y:
                self.y -= ENEMY_VEL
            if (
                abs(self.x - self.target_x) <= ENEMY_VEL
                and abs(self.y - self.target_y) <= ENEMY_VEL
            ):
                # sprawdza czy odległość od celu jest mniejsza od prędkości przeciwnika, bo gdyby odległość była mniejsza od prędkości, to statek nie mógłby dolecieć do celu
                self.at_target = True
            self.rect = pygame.Rect(
                self.x, self.y, SPACESHIP_WIDTH, SPACESHIP_HEIGHT
            )  # aktualizacja koordynatów przeciwnika


class GameLogic:  # Logika gry i inne funkcje na które nie mogłem znaleźć miejsca, bo lubię porządek:)
    def __init__(self):
        self.level = 0

        self.enemy_bullets = (
            []
        )  # lista na pociski przeciwników jest tutaj, bo inaczej musiałbym iterować przez każdego z nich
        self.enemy_shooting_interval = 1  # ta wartość będzie dodawana do licznika, też tu bo nie chcę iterować przez każdego przeciwnika

        self.player_bullets = (
            []
        )  # pewnie powinno być w klasie player, ale tu mi bardziej pasuje

        self.score = 0  # ilość zabitych przeciwników

        self.enemy_rows = 3  # wiersze przeciwników
        self.enemy_cols = 4  # kolumny przeciwników

        self.next_level_timer = 0  # czas między kolejnymi poziomami

    def handle_enemy_bullets(self, player, enemy_list, files):
        for index, enemy in enumerate(enemy_list):
            try:  # gdy się trafia dwóch przeciwników na raz jest szansa na błąd, bo po usunięciu pierwszego z listy może nie być indeksu dla drugiego
                if enemy.shooting_timer >= randint(
                    100, 2000
                ):  # losuje wartość, żeby przeciwnik strzelał w różnych odstępach czasowych
                    enemy_bullet = pygame.Rect(
                        enemy_list[index].x + SPACESHIP_WIDTH // 2,
                        enemy_list[index].y + SPACESHIP_HEIGHT,
                        2,
                        10,
                    )  # pociski pojawiają się po środku statku przeciwnika
                    self.enemy_bullets.append(
                        enemy_bullet
                    )  # dodanie pocisku do listy pocisków
                    enemy_list[
                        index
                    ].shooting_timer = (
                        0  # wyzerowanie czasu potrzebnego do następnego strzału
                    )
                enemy_list[
                    index
                ].shooting_timer += (
                    self.enemy_shooting_interval
                )  # dodanie czasu do licznika. Używam zmiennej, bo chcę potem wprowadzić możliwaoś szybszego strzelania przeciwników dla balansu
            except IndexError:
                continue  # jak wyskoczy błąd to nic nie rób

        for bullet in self.enemy_bullets:  # iteruje przez wszystkie pociski z listy
            bullet.y += BULLET_VEL  # pociski lecą w dół
            if (
                bullet.y < 0
            ):  # jeżeli pocisk wyleci poza mapę, to zostaje usunięty, by nie marnować pamięci
                self.enemy_bullets.remove(bullet)
            if player.rect.colliderect(bullet):  # jeżeli gracz jest trafiony
                self.enemy_bullets.remove(bullet)  # to pocisk jest usunięty
                player.health -= 1  # zdrowie zmniejszone
                files.PLAYER_HIT_SOUND.play()  # dźwięk zagrany

    def handle_player_bullets(self, enemy_list, buff, files):
        for bullet in self.player_bullets:  # iteruje przez wszystkie pociski gracza
            bullet.y -= BULLET_VEL  # pociski lecą do góry
            if (
                bullet.y < 0
            ):  # gdy pocisk wyleci poza okno, jest usuwany by nie marnować pamięci
                self.player_bullets.remove(bullet)
            for index, enemy in enumerate(
                enemy_list
            ):  # iteruje przez listę przeciwników, aby sprawdzić, czy nie są trafieni
                if enemy.rect.colliderect(bullet):  # jeśli przciwnik został trafiony
                    try:  # jakby dwoje przeciwników zostało trafionych w tym samym czasie
                        self.player_bullets.remove(bullet)  # usuwa pocisk z listy
                        enemy.health -= 1  # zabranie życia przeciwnikowi
                        if (
                            enemy.health == 0
                        ):  # gdy życie przeciwnika wynosi 0, jest usuwany z listy
                            if random() < 0.1:
                                choice(buff.buffs_list).append(
                                    pygame.Rect(
                                        enemy.x, enemy.y, BUFF_WIDTH, BUFF_HEIGHT
                                    )
                                )  # 10% szans na to, że wypadnie losowy buff

                            enemy_list.pop(index)
                            self.score += 1  # dodaje 1 do licznika zabitych przeciwników. Nie wiem jak jest score po polsku:/

                        files.BULLET_FIRE_SOUND.play()  # odtworzenie dźwięku trafienia przeciwnika
                    except ValueError:
                        continue

    def next_level(self, enemy_list):  # przejście na kolejny poziom
        if (
            len(enemy_list) == 0
        ):  # jeżeli nie ma już przeciwników, przechodzi na kolejny poziom
            if self.next_level_timer == 200:  # czeka 3 1/3 sekundy.
                self.level += 1  # zwiększa
                if self.level % 3 == 1:  # co 3 poziomy zwiększa się liczba przeciwników
                    self.enemy_rows += 1
                    self.enemy_cols += 1
                    # muszę zwiększać obydwie wartości na raz, bo inaczej przeciwnicy wychodzą poza okno lub wchodzą na siebie
                if self.level % 5 == 1:  # co 5 poziomów przeciwnicy strzelają szybciej
                    self.enemy_shooting_interval += 1
                self.spawn_enemies(enemy_list)  # spawanowanie przeciwników
                self.next_level_timer = 0  # wyzerowanie czasomierza
            else:
                self.next_level_timer += (
                    1  # zwiększenie licznika do następsdzego poziomu
                )

    def spawn_enemies(self, enemy_list):  # spawnuje przeciwników
        for row in range(self.enemy_cols):
            for col in range(
                self.enemy_rows
            ):  # przeciwnicy pojawiają się we wzorze prostokąta, czy coś takiego. Nie wiem jak to nazwać
                enemy = Enemy(
                    row, col, self
                )  # zdefiniowanie koordynatów przeciwnika przeciwnika
                enemy.target_x = randint(0, WIDTH - SPACESHIP_WIDTH)
                enemy.target_y = randint(0, HEIGHT - SPACESHIP_HEIGHT - HEIGHT // 2)
                # nadanie przeciwnikowi indywidualnego celu x i y
                enemy_list.append(enemy)  # dodanie przeciwnika do listy


class Buff:
    def __init__(self):
        self.bullet_buff_list = []  # lista buffów do ilości pocisków
        self.shooting_buff_list = []  # lista buffów do szybkości strzelania
        self.health_buff_list = []  # lista buffów do zdrowia

        self.buffs_list = [
            self.bullet_buff_list,
            self.shooting_buff_list,
            self.health_buff_list,
        ]
        # zrobiłem osobne listy na każdy rodzaj buffa. Wiem, że można to zrobić lepiej i teraz nad tym pracuję

    def handle(self, player, gamestate):
        for buff in self.bullet_buff_list:  # iteruje przez listę
            buff.y += 2  # buff leci w dół 2 piksele na klatkę
            if buff.y > HEIGHT:  # usuwa buffa jeśli wyleci poza okno
                self.bullet_buff_list.remove(buff)
            if (
                player.rect.colliderect(buff) and player.shots < gamestate.level
            ):  # zebranie buffa. Maksymalna ilość pocisków odpowiada aktualnemu poziomowi, żeby nie było zbyt OP
                self.bullet_buff_list.remove(
                    buff
                )  # usunięcie buffa z listy po zebraniu
                player.shots += 1  # zwiększenie liczby strzałów na raz
        # reszta pętl działa tak samo, więc nie będę ich opisywał. Zmieniają się tylko wartości i typy buffa. Powinienem użyć jednej pętli, nad czym teraz pracuję
        for buff in self.shooting_buff_list:
            buff.y += 2
            if buff.y > HEIGHT:
                self.shooting_buff_list.remove(buff)
            if player.rect.colliderect(buff) and player.shooting_interval < 6:
                self.shooting_buff_list.remove(buff)
                player.shooting_interval += 1

        for buff in self.health_buff_list:
            buff.y += 2
            if buff.y > HEIGHT:
                self.health_buff_list.remove(buff)
            if player.rect.colliderect(buff) and player.health < 20:
                self.health_buff_list.remove(buff)
                player.health += 1


def update_window(player, enemy_list, gamestate, buffs, files):
    WIN.blit(files.BACKGROUND, (0, 0))  # rysuje tło

    text_score = FONT1.render("SCORE: " + str(gamestate.score), 1, WHITE)
    WIN.blit(text_score, (5, 0))  # rysuje 'score'

    text_level = FONT1.render("LEVEL: " + str(gamestate.level), 1, WHITE)
    WIN.blit(
        text_level, (WIDTH - text_level.get_width() - 3, 0)
    )  # rysuje aktualny poziom

    text_health = FONT1.render("HEALTH: " + str(player.health), 1, RED)
    WIN.blit(
        text_health, (0, HEIGHT - text_health.get_height())
    )  # rysuje aktualne zdrowie

    WIN.blit(files.PLAYER_SPACESHIP_IMAGE, (player.x, player.y))  # rysuje gracza

    for buff in buffs.shooting_buff_list:
        WIN.blit(files.SHOOTING_BUFF_IMAGE, (buff.x, buff.y))
    for buff in buffs.bullet_buff_list:
        WIN.blit(files.BULLET_BUFF_IMAGE, (buff.x, buff.y))
    for buff in buffs.health_buff_list:
        WIN.blit(files.HEALTH_BUFF_IMAGE, (buff.x, buff.y))
    # rysuje wszystki buffy

    for enemy in enemy_list:
        WIN.blit(files.ENEMY_SPACESHIP_IMAGE, (enemy.x, enemy.y))
    # rysuje przeciwników
    for player_bullet in gamestate.player_bullets:
        pygame.draw.rect(WIN, PLAYER_BULLET_COLOR, player_bullet)
    for enemy_bullet in gamestate.enemy_bullets:
        pygame.draw.rect(WIN, ENEMY_BULLET_COLOR, enemy_bullet)
    # rysuje wszystkie pociski

    pygame.display.update()  # odświeżenie okna


def death_screen(
    gamestate,
):  # ekran po przegranej. Po prostu linie, które same się tłumaczą
    WIN.fill((0, 0, 0))
    line1 = FONT1.render("YOU LOST", 1, RED)
    line2 = FONT1.render(f"Your score: {gamestate.score}", 1, WHITE)
    line3 = FONT1.render(f"Levels passed: {gamestate.level}", 1, WHITE)
    line4 = FONT1.render("Press space to play again", 1, WHITE)
    line5 = FONT1.render("Press escape to exit", 1, WHITE)

    WIN.blit(
        line1,
        ((WIDTH - line1.get_width()) // 2, (HEIGHT - line1.get_height()) // 5 * 0.5),
    )
    WIN.blit(
        line2,
        ((WIDTH - line2.get_width()) // 2, (HEIGHT - line2.get_height()) // 5 * 1),
    )
    WIN.blit(
        line3,
        ((WIDTH - line3.get_width()) // 2, (HEIGHT - line3.get_height()) // 5 * 2),
    )
    WIN.blit(
        line4,
        ((WIDTH - line4.get_width()) // 2, (HEIGHT - line4.get_height()) // 5 * 3),
    )
    WIN.blit(
        line5,
        ((WIDTH - line5.get_width()) // 2, (HEIGHT - line5.get_height()) // 5 * 4),
    )
    pygame.display.update()


def main():  # głowna funkcja gry. Pozwala też na restart
    playing = True  # zmienna, która podtrzymuje pętlę
    clock = pygame.time.Clock()  # inicjuje funkcję, odpowiadającą za fps

    files = Files()
    player = Player()
    buffs = Buff()
    gamestate = GameLogic()
    # inicjacja klas
    enemy_list = []
    # lista przeciwników
    gamestate.next_level(enemy_list)
    # używam tego zamiast spawn_enemies(), żeby była chwila na zorientowanie się
    while playing:
        clock.tick(60)  # odświeżanie 60 razy na sekundę
        keys_pressed = pygame.key.get_pressed()
        # zbiera wszystkie naciśnięte klawisze
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # żeby okno się zamykało po kliknięciu 'X'
                playing = False  # przerwanie pętli

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LCTRL:
                    player.shots += 1  # +liczba pocisków
                if event.key == pygame.K_LSHIFT and player.shots > 1:
                    player.shots -= 1  # - liczba pocisków
                if event.key == pygame.K_q:
                    gamestate.enemy_shooting_interval += (
                        1  # przyspieszenie strzelania przecisników
                    )
                if event.key == pygame.K_t:
                    gamestate.enemy_shooting_interval = (
                        1  # zwolnienie strzelania przeciwników do 1
                    )
                if event.key == pygame.K_f:
                    player.shooting_interval += 1  # zwolnienie strzelania gracza do 1
                if event.key == pygame.K_g:
                    player.shooting_interval = 1  # zwolnienie strzelania gracza do 1
                if event.key == pygame.K_r:
                    gamestate.spawn_enemies(enemy_list)  # respawn przeciwników
                if event.key == pygame.K_h:
                    player.health += 100  # dodanie zdrowia przeciwnikowi
                if event.key == pygame.K_ESCAPE:
                    playing = (
                        False  # wyjście z gry po kliknięciu esc, bo mi się nudziło
                    )
            # te klawisze są przypisane wyłącznie w celach testowania i nie służą rozgrywce
        if player.health == 0:  # jeśli zdrowie gracza wynosi 0, gra jest przerwana
            death_screen(gamestate)  # wyskakuje ekran przegranej
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:  # zagranie jeszcze raz
                            main()
                        if event.key == pygame.K_ESCAPE:  # wyjście
                            pygame.quit()
                            break

        for enemy in enemy_list:  # zmiana położenia przeciwników
            enemy.change_position()

        player.movement(keys_pressed)
        player.shoot(gamestate)

        gamestate.handle_player_bullets(enemy_list, buffs, files)
        gamestate.handle_enemy_bullets(player, enemy_list, files)

        buffs.handle(player, gamestate)

        gamestate.next_level(enemy_list)
        update_window(player, enemy_list, gamestate, buffs, files)
        # te funkcje opisałem wcześcniej, teraz są tylko wywoływane


if (
    __name__ == "__main__"
):  # na wypadek, gdybym chciał korzystać z funkcji w innym programie. Przeczytałem też, że jest to dobry nawyk, więc się przyzwyczajam
    main()
