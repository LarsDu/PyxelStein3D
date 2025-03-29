import pyxel

SCREEN_HEIGHT = 256
SCREEN_WIDTH = 256
TILE_SIZE = 8

COL_TRANSPARENT_BLACK = 0
COL_TRANSPARENT_PURP = 2

# MARKERS
EMPTY = (0, 0)
WALL = (1, 0)
PLAYER_SPAWN_MARKER = (0, 1)
PLAYER_MARKER = (1, 1)


# Textures
WALL_BRICK_TEX = (4, 0, 4, 4)  # x,y, width, height


# Singleton Metaclass
# NOTE: See https://stackoverflow.com/questions/6760685/
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


# Functions
def get_tile_from_world(x: float, y: float, tilemap_idx: int) -> tuple[int]:
    """
    Get tile ID tuple from world coords
    """
    return pyxel.tilemaps[tilemap_idx].pget(x // TILE_SIZE, y // TILE_SIZE)


def is_wall_tile(x: float, y: float, tilemap_idx: int) -> bool:
    """
    Check if world coords is a wall
    """
    return get_tile_from_world(x, y, tilemap_idx) == WALL


def collide_aabb(
    xa: float,
    ya: float,
    wa: float,
    ha: float,
    xb: float,
    yb: float,
    wb: float,
    hb: float,
) -> bool:
    """
    Return true if axis-aligned rects are overlapping, false if not overlapping.
    """
    return xa < xb + wb and xa + wa > xb and ya < yb + hb and ya + ha > yb


def cast_ray(x: float, y: float, angle_deg: float) -> tuple[int]:
    pass


def cast_ray_visualized(x: float, y: float, angle_deg: float) -> tuple[int]:
    pass


class OverheadCamera(metaclass=Singleton):
    def __init__(self) -> None:
        self.x = 0
        self.y = 0
        self.target: None | "Player" = None
        self.w = SCREEN_WIDTH
        self.h = SCREEN_HEIGHT

    def update(self) -> None:
        if self.target is None:
            print("No target set for camera")
            return
        self.x = self.target.x - SCREEN_WIDTH // 2
        self.y = self.target.y - SCREEN_HEIGHT // 2


class Camera3d:
    def __init__(self) -> None:
        self.x = 0
        self.y = 0

    def update(self) -> None:
        pass


class Entity:
    @property
    def sx(self) -> float:
        return self.x - self.overhead_camera.x

    @property
    def sy(self) -> float:
        return self.y - self.overhead_camera.y

    def __init__(self, x: float, y: float, angle_deg: float) -> None:
        self.x = x
        self.y = y
        self.angle_deg = angle_deg
        self.overhead_camera = OverheadCamera()
        self.game_manager = GameManager()

    def update(self) -> None:
        raise NotImplementedError("Entity subclass must implement update method")

    def draw(self) -> None:
        raise NotImplementedError("Entity subclass must implement draw method")


class Actor(Entity):
    def __init__(
        self, x: float, y: float, angle_deg: float, speed: float, rot_speed: float
    ) -> None:
        super().__init__(x, y, angle_deg)
        self.speed = speed
        self.rot_speed = rot_speed

    def move_forward(self):
        self.x += self.speed * pyxel.cos(self.angle_deg)
        self.y += self.speed * pyxel.sin(self.angle_deg)

    def move_backward(self):
        self.x -= self.speed * pyxel.cos(self.angle_deg)
        self.y -= self.speed * pyxel.sin(self.angle_deg)

    def rotate_left(self):
        self.angle_deg -= self.rot_speed

    def rotate_right(self):
        self.angle_deg += self.rot_speed


class DamageableActor(Actor):
    def __init__(
        self,
        x: float,
        y: float,
        angle_deg: float,
        speed: float,
        rot_speed: float,
        hp: int,
    ) -> None:
        super().__init__(x, y, angle_deg, speed, rot_speed)
        self.hp = hp

    def take_damage(self, damage: int) -> None:
        self.hp -= damage
        if self.hp <= 0:
            self.on_death()

    def on_death(self) -> None:
        pass


class Player(DamageableActor):
    def __init__(
        self,
        x: float,
        y: float,
        angle_deg: float,
        speed: float = 1,
        rot_speed: float = 0.5,
        hp: int = 100,
    ) -> None:
        super().__init__(x, y, angle_deg, speed, rot_speed, hp)

    def update(self):
        self.handle_input()

    def handle_input(self):
        if pyxel.btn(pyxel.KEY_W):
            self.move_forward()
        if pyxel.btn(pyxel.KEY_S):
            self.move_backward()
        if pyxel.btn(pyxel.KEY_A):
            self.rotate_left()
        if pyxel.btn(pyxel.KEY_D):
            self.rotate_right()

    def draw(self):
        u, v = PLAYER_MARKER
        u *= TILE_SIZE
        v *= TILE_SIZE
        pyxel.blt(
            self.sx,
            self.sy,
            0,
            u,
            v,
            TILE_SIZE,
            TILE_SIZE,
            COL_TRANSPARENT_BLACK,
            rotate=self.angle_deg,
        )


class Brownshirt(DamageableActor):
    def __init__(
        self, x: float, y: float, angle_deg: float, speed: float = 1, hp: int = 20
    ) -> None:
        super().__init__(x, y, angle_deg, speed, hp)

    def update(self):
        pass

    def draw(self):
        pass


class Powerup(Entity):
    def __init__(self, x: float, y: float, angle_deg: float) -> None:
        super().__init__(x, y, angle_deg)


class HealthPowerup(Powerup):
    def __init__(self, x: float, y: float, angle_deg: float, heal_amount: int) -> None:
        super().__init__(x, y, angle_deg)
        self.heal_amount = heal_amount


class Weapon:
    def __init__(self, damage: int, fire_rate: float, ammo: int) -> None:
        self.damage = damage
        self.fire_rate = fire_rate
        self.ammo = ammo


class GameManager(metaclass=Singleton):
    def __init__(self) -> None:
        self.score = 0


class App:
    def __init__(self) -> None:
        pyxel.init(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            title="PyxelStein3D",
            fps=60,
            display_scale=2,
            quit_key=pyxel.KEY_ESCAPE,
        )
        pyxel.load("assets/pyxelstein.pyxres")
        self.overhead_camera = OverheadCamera()
        self.player = Player(
            11 * TILE_SIZE, 6 * TILE_SIZE, 270, speed=1, rot_speed=5, hp=100
        )
        self.overhead_camera.target = self.player
        self.manager = GameManager()
        pyxel.run(self.update, self.draw)

    def update(self):
        self.player.update()
        self.overhead_camera.update()

    def draw(self):
        pyxel.cls(COL_TRANSPARENT_BLACK)
        # Draw the overhead tilemap
        pyxel.bltm(
            0,
            0,
            0,
            self.overhead_camera.x,
            self.overhead_camera.y,
            self.overhead_camera.w,
            self.overhead_camera.h,
            COL_TRANSPARENT_BLACK,
        )
        self.player.draw()


App()
