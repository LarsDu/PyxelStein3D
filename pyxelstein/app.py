import pyxel

SCREEN_HEIGHT = 256
SCREEN_WIDTH = 256
TILE_SIZE = 8
MAX_CAST_DISTANCE = 1024  # in world length, not tile length
RAY_CAST_ARC_DEG: float = 60

COL_TRANSPARENT_BLACK = 0
COL_TRANSPARENT_PURP = 2

# MARKERS
EMPTY = (0, 0)
WALL = (2, 0)
PLAYER_SPAWN_MARKER = (0, 1)
PLAYER_MARKER = (1, 8)


# Textures
# WALL_BRICK_TEX = (4, 0, 4, 4)  # x,y, width, height
# WALL_BRICK_TEX_SHADED = (9, 0, 4, 4)  # x,y, width, height
WALL_BRICK_TEX = (2, 9, 1, 2)
WALL_BRICK_TEX_SHADED = (3, 9, 1, 2)

# Brownshirt
BROWNSHIRT_FRONT_TEX = (0, 11, 2, 4)
BROWNSHIRT_SIDE_TEX_LEFT = (2, 11, 2, 4)
BROWNSHIRT_DYING_TEX = (0, 15, 2, 4)
BROWNSHIRT_CORPSE_TEX = (3, 16, 2, 2)

# Powerups
HEALTH_CHICKEN_LEG_TEX = (0, 20, 2, 1)
HEALTH_POWERUP_TEX = (0, 19, 2, 1)
AMMO_POWERUP_TEX = (4, 14, 4, 4)  ##

# Weapons
PISTOL_TEX = (2, 19, 4, 4)
PISTOL_MUZZLE_FLASH_TEX = (2, 21, 4, 4)
INCOMING_BULLET_TEX = (4, 19, 4, 4)

# MARKERS
HEALTH_CHICKEN_MARKER = (0, 9)
HEALTH_LARGE_MARKER = (1, 8)
AMMO_POWERUP_MARKER = (0, 10)
PATROL_LEFT_MARKER = (0, 22)
PATROL_RIGHT_MARKER = (0, 21)
PATROL_UP_MARKER = (0, 21)
PATROL_DOWN_MARKER = (0, 22)
RUBY_MARKER = (0, 4)


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


def is_solid_tile(x: float, y: float, tilemap_idx: int) -> bool:
    """
    Check if world coords is a wall
    """
    return get_tile_from_world(x, y, tilemap_idx) == WALL


def pushback_solid_tile(
    x: float, y: float, w: float, h: float, dx: float, dy: float, tilemap_idx: int
) -> tuple[float, float, float, float]:
    """Compute new_x, new_y, new_dx, new_dy pushback from solid tile collision"""
    nx, ny = x + dx, y + dy
    ndx, ndy = dx, dy

    # FIXME: Only call function if needed
    top_right = is_solid_tile(nx + w, ny, tilemap_idx)
    top_left = is_solid_tile(nx, ny, tilemap_idx)
    bottom_right = is_solid_tile(nx + w, ny + h, tilemap_idx)
    bottom_left = is_solid_tile(nx, ny + h, tilemap_idx)

    if dx > 0:
        if top_right or bottom_right:
            ndx = 0  # Set velocity to 0
            nx -= dx  # Undo the move
    elif dx < 0:
        if top_left or bottom_left:
            ndx = 0
            nx -= dx

    if dy > 0:
        if bottom_left or bottom_right:
            ndy = 0
            ny -= dy
    elif dy < 0:
        if top_left or top_right:
            ndy = 0
            ny -= dy
    return (nx, ny, ndx, ndy)


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


def cast_ray(
    x: float, y: float, rot: float, tilemap_idx: int = 0
) -> tuple[float, float, bool, int]:
    # Ray direction vector
    dx = pyxel.cos(rot)
    dy = pyxel.sin(rot)

    # Current map position (tile coordinates)
    tx = int(x // TILE_SIZE)
    ty = int(y // TILE_SIZE)

    # Length of ray from one x or y-side to next x or y-side
    delta_dist_x = float("inf") if abs(dx) < 1e-6 else abs(float(TILE_SIZE) / dx)
    delta_dist_y = float("inf") if abs(dy) < 1e-6 else abs(float(TILE_SIZE) / dy)

    # What direction to increment tiles in x or y-direction (either +1 or -1)
    tile_step_x = 1 if dx >= 0 else -1
    tile_step_y = 1 if dy >= 0 else -1

    # CALCULATE THE VERY FIRST INTERCEPT
    # Calculate distance to the next x or y grid line
    x_remainder = x % TILE_SIZE
    y_remainder = y % TILE_SIZE

    # Calculate distance to next grid line
    if dx < 0:
        side_dist_x = x_remainder / abs(dx)  # Distance to previous x gridline
    else:
        side_dist_x = (TILE_SIZE - x_remainder) / dx if dx > 0 else float("inf")

    if dy < 0:
        side_dist_y = y_remainder / abs(dy)  # Distance to previous y gridline
    else:
        side_dist_y = (TILE_SIZE - y_remainder) / dy if dy > 0 else float("inf")

    # DDA algorithm
    is_stepping_x: bool = True
    hit = False
    distance = 0

    # Alternatively step x or y by delta_dist_x or delta_dist_y depending on which is larger
    while distance < MAX_CAST_DISTANCE:
        # Jump to next map square
        if side_dist_x < side_dist_y:
            distance = side_dist_x
            side_dist_x += delta_dist_x
            tx += tile_step_x
            is_stepping_x = True
        else:
            distance = side_dist_y
            side_dist_y += delta_dist_y
            ty += tile_step_y
            is_stepping_x = False

        # Check if ray hit a wall
        if is_solid_tile(
            tx * TILE_SIZE + TILE_SIZE // 2,
            ty * TILE_SIZE + TILE_SIZE // 2,
            tilemap_idx=tilemap_idx,
        ):
            hit = True
            break

    # If no hit, return the maximum distance point
    if not hit:
        return (
            x + dx * MAX_CAST_DISTANCE,
            y + dy * MAX_CAST_DISTANCE,
            is_stepping_x,
            0,
        )

    # Calculate exact hit position
    if is_stepping_x:  # Vertical wall
        hx = tx * TILE_SIZE if tile_step_x > 0 else (tx + 1) * TILE_SIZE
        hy = y + distance * dy
        wall_offset = int(hy) % TILE_SIZE  # Offset relative to the wall's surface
    else:  # Horizontal wall
        hy = ty * TILE_SIZE if tile_step_y > 0 else (ty + 1) * TILE_SIZE
        hx = x + distance * dx
        wall_offset = int(hx) % TILE_SIZE  # Offset relative to the wall's surface

    return hx, hy, is_stepping_x, wall_offset


def calculate_column_height_fisheye(x: float, y: float, hx: float, hy: float) -> int:
    """ """
    dist = pyxel.sqrt((hx - x) ** 2 + (hy - y) ** 2)
    dist = max(1, dist)  # At 0 to 1 distance, fill screen height
    return int(SCREEN_HEIGHT / dist) * 4


def calculate_column_height(
    x: float,
    y: float,
    hx: float,
    hy: float,
    player_rot: float,
    ray_rot_relative_to_player: float,
    dist_scale=0.5,
) -> int:
    ray_angle = (ray_rot_relative_to_player - player_rot) % 360
    corrected_distance = (
        pyxel.sqrt((hx - x) ** 2 + (hy - y) ** 2) * pyxel.cos(ray_angle) * dist_scale
    )
    return int(SCREEN_HEIGHT / max(1, corrected_distance)) * 4


def sample_texture_to_column(
    x: int,
    y: int,
    image_idx: int,
    texture: tuple[int, int, int, int],
    col_height: int,
    uoff: int = 0,
) -> None:
    tex_u, tex_v, tex_w, tex_h = texture
    tex_u *= TILE_SIZE
    tex_v *= TILE_SIZE
    tex_w *= TILE_SIZE
    tex_h *= TILE_SIZE

    # Zero guard
    col_height = max(1, col_height)

    image = pyxel.images[image_idx]

    for yoff in range(col_height // 2 + 1):
        voff = int(tex_h * (2 * yoff / col_height))
        col = image.pget(
            tex_u + uoff,
            tex_v + voff,
        )
        pyxel.pset(
            x,
            y + yoff,
            col,
        )
        # Mirror draw from the bottom
        # pyxel.pset(
        #    x,
        #    y + col_height - yoff,
        #    col,
        # )
        pyxel.pset(
            x,
            y + yoff + col_height // 2,
            col,
        )


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

    def __init__(self, x: float, y: float, w: float, h: float, rot: float) -> None:
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rot = rot
        self.overhead_camera = OverheadCamera()
        self.game_manager = GameManager()

    def update(self) -> None:
        raise NotImplementedError("Entity subclass must implement update method")

    def draw(self) -> None:
        raise NotImplementedError("Entity subclass must implement draw method")


class Actor(Entity):
    def __init__(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        rot: float,
        speed: float,
        rot_speed: float,
    ) -> None:
        super().__init__(x, y, w, h, rot)
        self.speed = speed
        self.rot_speed = rot_speed
        self.dx = 0
        self.dy = 0
        self.drot = 0

    def delta_forward(self):
        self.dx = self.speed * pyxel.cos(self.rot)
        self.dy = self.speed * pyxel.sin(self.rot)

    def delta_backward(self):
        self.dx = -self.speed * pyxel.cos(self.rot)
        self.dy = -self.speed * pyxel.sin(self.rot)

    def rotate_left(self):
        self.drot = -self.rot_speed

    def rotate_right(self):
        self.drot = self.rot_speed

    def move(self):
        self.x += self.dx
        self.y += self.dy
        self.rot = (self.rot + self.drot) % 360


class DamageableActor(Actor):
    def __init__(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        rot: float,
        speed: float,
        rot_speed: float,
        hp: int,
    ) -> None:
        super().__init__(x, y, w, h, rot, speed, rot_speed)
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
        w: float,
        h: float,
        rot: float,
        speed: float = 1,
        rot_speed: float = 0.5,
        hp: int = 100,
    ) -> None:
        super().__init__(x, y, w, h, rot, speed, rot_speed, hp)

    def update(self):
        self.handle_input()
        # Note: Collisions are axis-aligned
        self.x, self.y, self.dx, self.dy = pushback_solid_tile(
            self.x, self.y, self.w, self.h, self.dx, self.dy, 0
        )
        self.move()
        self.reset_movement()

    def reset_movement(self) -> None:
        self.dx = 0
        self.dy = 0
        self.drot = 0

    def handle_input(self):
        if pyxel.btn(pyxel.KEY_W) or pyxel.btn(pyxel.KEY_UP):
            self.delta_forward()
        if pyxel.btn(pyxel.KEY_S) or pyxel.btn(pyxel.KEY_DOWN):
            self.delta_backward()
        if pyxel.btn(pyxel.KEY_A) or pyxel.btn(pyxel.KEY_LEFT):
            self.rotate_left()
        if pyxel.btn(pyxel.KEY_D) or pyxel.btn(pyxel.KEY_RIGHT):
            self.rotate_right()

    def draw(self, scale=1.0):
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
            rotate=(self.rot + 90) % 360,  # Not sure about this +90?
            scale=scale,
        )


class Raycaster:
    def __init__(self, target: Player, num_rays: int = SCREEN_WIDTH) -> None:
        self.target = target
        self.num_rays = num_rays
        self.deg_increment = RAY_CAST_ARC_DEG / float(self.num_rays)
        self.overhead_camera = OverheadCamera()

        # HIT_X, HIT_Y, COL_HEIGHT for every single raycast hit
        self.hit_buffer = [
            [MAX_CAST_DISTANCE, MAX_CAST_DISTANCE] for _ in range(self.num_rays)
        ]

    def draw_floor(self) -> None:
        # Draw floor
        pyxel.rect(
            0, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT, pyxel.COLOR_BROWN
        )

    # '''
    # num_gradients = 10
    # grad_height = SCREEN_HEIGHT // num_gradients
    #
    # for i in range(num_gradients):
    #     pyxel.dither(i/num_gradients)
    #     pyxel.rect(
    #         0, SCREEN_HEIGHT // 2 + i * grad_height, SCREEN_WIDTH, grad_height, pyxel.COLOR_LIGHT_BLUE
    #     )
    # pyxel.dither(1.0)
    # '''

    def draw_ceiling(self) -> None:
        # Draw ceiling
        pyxel.rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT // 2, pyxel.COLOR_GRAY)

    def draw_overhead(self) -> None:
        cx, cy = (
            self.target.x + self.target.w // 2,
            self.target.y + self.target.h // 2,
        )
        sx = cx - self.overhead_camera.x
        sy = cy - self.overhead_camera.y

        self.draw_debug_rays(sx, sy)

    def draw_debug_rays(self, sx: float, sy: float) -> None:
        pyxel.dither(0.5)
        for i in range(self.num_rays):
            hx, hy = self.hit_buffer[i]
            pyxel.line(
                sx,
                sy,
                hx - self.overhead_camera.x,
                hy - self.overhead_camera.y,
                pyxel.COLOR_GREEN,
            )
        pyxel.dither(1.0)

    def draw_3d_view(self) -> None:
        self.draw_floor()
        self.draw_ceiling()
        rot_start = self.target.rot - RAY_CAST_ARC_DEG * 0.5
        cx, cy = (
            self.target.x + self.target.w // 2,
            self.target.y + self.target.h // 2,
        )

        for i in range(self.num_rays):
            ray_rot = (rot_start + i * self.deg_increment) % 360
            hx, hy, is_stepping_x, wall_offset = cast_ray(cx, cy, ray_rot)
            self.hit_buffer[i] = (hx, hy)
            col_height = calculate_column_height(
                cx, cy, hx, hy, self.target.rot, ray_rot
            )

            sample_texture_to_column(
                i,
                SCREEN_HEIGHT // 2 - col_height // 2,
                0,
                WALL_BRICK_TEX if is_stepping_x else WALL_BRICK_TEX_SHADED,
                col_height,
                uoff=wall_offset,  # Still a bug here. Ranges from 0 to 7
            )


class Brownshirt(DamageableActor):
    def __init__(
        self, x: float, y: float, rot: float, speed: float = 1, hp: int = 20
    ) -> None:
        super().__init__(x, y, rot, speed, hp)

    def update(self):
        pass

    def draw(self):
        pass


class Powerup(Entity):
    def __init__(self, x: float, y: float, rot: float) -> None:
        super().__init__(x, y, rot)


class HealthPowerup(Powerup):
    def __init__(self, x: float, y: float, rot: float, heal_amount: int) -> None:
        super().__init__(x, y, rot)
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
            display_scale=4,
            quit_key=pyxel.KEY_ESCAPE,
        )
        pyxel.load("assets/pyxelstein.pyxres")
        self.overhead_camera = OverheadCamera()
        self.player = Player(
            x=11 * TILE_SIZE,
            y=6 * TILE_SIZE,
            w=TILE_SIZE,
            h=TILE_SIZE,
            rot=0,
            speed=1,
            rot_speed=2,
            hp=100,
        )
        self.overhead_camera.target = self.player
        self.raycaster = Raycaster(target=self.player)
        self.manager = GameManager()
        self.show_overhead_view = False
        pyxel.run(self.update, self.draw)

    def update(self):
        self.player.update()

        # Toggle overhead view
        if pyxel.btnp(pyxel.KEY_M):
            self.show_overhead_view = not self.show_overhead_view
        if self.show_overhead_view:
            self.overhead_camera.update()

    def draw(self):
        self.raycaster.draw_3d_view()
        if self.show_overhead_view:
            self.draw_overhead()
            self.raycaster.draw_overhead()

    def draw_overhead(self, scale=1.0):
        # pyxel.cls(COL_TRANSPARENT_BLACK)
        # pyxel.blt(0,0,0,0,0,SCREEN_WIDTH*scale,SCREEN_HEIGHT*scale)
        self.draw_overhead_tilemap(scale)
        self.player.draw(scale)

    def draw_overhead_tilemap(self, scale) -> None:
        pyxel.dither(0.5)
        pyxel.bltm(
            0,
            0,
            0,
            self.overhead_camera.x,
            self.overhead_camera.y,
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            COL_TRANSPARENT_BLACK,
            scale=scale,
        )
        pyxel.dither(1.0)


App()
