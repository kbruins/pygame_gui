import pygame
from collections.abc import Sequence
from pygui.functions import center_text, colored_rect
from math import floor, ceil

pygame.font.init()

DEFAULT_FONT = pygame.font.SysFont("Arial", 30)
LIST_FONT = pygame.font.SysFont("Arial", 24)

K_CENTER = 0
K_LEFT = K_TOP = 1
K_RIGHT = K_BOTTOM = 2

K_ALIGN_CENTER = (K_CENTER, K_CENTER)
K_ALIGN_LEFT = (K_LEFT, K_CENTER)
K_ALIGN_RIGHT = (K_RIGHT, K_CENTER)
K_ALIGN_TOP = (K_CENTER, K_TOP)
K_ALIGN_BOTTOM = (K_CENTER, K_BOTTOM)

K_TOP_LEFT = (K_LEFT, K_TOP)
K_TOP_RIGHT = (K_RIGHT, K_TOP)
K_BOTTOM_LEFT = (K_LEFT, K_BOTTOM)
K_BOTTOM_RIGHT = (K_RIGHT, K_BOTTOM)


class GUISprite(pygame.sprite.Sprite):
    def __init__(self, pos: tuple[int | float, int | float], image: pygame.Surface, priority: int = 5,
                 name: str = "sprite", use_viewport: bool = True, alignment: Sequence[int, int] = K_ALIGN_CENTER,
                 *groups: pygame.sprite.Group):
        super().__init__(*groups)
        self.image = image
        self.pos = pos
        self.rect = pygame.Rect((0, 0), image.get_size())
        self.name = name
        self.priority = priority  # higher numbers are drawn on top.
        self.parent: None | GUISprite | Button | TextBox | Dropdown | GUI = None
        self.uses_viewport = use_viewport
        self.alignment = alignment
        self._update_pos()

    def __str__(self) -> str:
        return self.name

    def _update_pos(self, viewport_size: Sequence[int, int] | None = None) -> None:
        if self.uses_viewport:
            pos = self.pixels_from_viewport(self.pos, viewport_size=viewport_size)
        else:
            pos = self.pos

        if self.alignment[0] == K_CENTER:
            self.rect.centerx = pos[0]
        elif self.alignment[0] == K_LEFT:
            self.rect.left = pos[0]
        elif self.alignment[0] == K_RIGHT:
            self.rect.right = pos[0]

        if self.alignment[1] == K_CENTER:
            self.rect.centery = pos[1]
        elif self.alignment[1] == K_TOP:
            self.rect.top = pos[1]
        elif self.alignment[1] == K_BOTTOM:
            self.rect.bottom = pos[1]

    def set_pos(self, pos: tuple[int | float, int | float], use_viewport: bool | None = None,
                alignment: Sequence[int, int] | None = None, viewport_size: Sequence[int, int] | None = None) -> None:
        self.pos = pos
        if use_viewport is not None:
            self.uses_viewport = use_viewport
        if alignment is not None:
            self.alignment = alignment

        self._update_pos(viewport_size)

    def pixels_from_viewport(self, pos: Sequence[int | float, int | float],
                             viewport_size: Sequence[int, int] | None = None) -> tuple[int, int]:
        """transform viewport coordenates to pixels"""
        if viewport_size is None:
            if self.parent is None:
                viewport_size = pygame.display.get_window_size()
            else:
                viewport_size = self.parent.rect.size
        return int(pos[0]*viewport_size[0]), int(pos[1]*viewport_size[1])

    def get_global_rect(self) -> pygame.rect.Rect:
        """iterates through the parents to find its global position"""
        parent = self.parent
        rect = self.rect.copy()
        while parent is not None:
            rect.move_ip(parent.rect.topleft)
            parent = parent.parent
        return rect

    def set_surface(self, image: pygame.surface.Surface):
        """set a new surface to be displayed"""
        self.image = image
        self.rect.update(self.rect.left, self.rect.top, image.get_width(), image.get_height())
        self._update_pos()

    def filled_surface(self) -> pygame.surface.Surface:
        return self.image

    def viewport_to_pixels(self, pos: Sequence[float, float], viewport: Sequence[int | float, int | float] | None =
                           None, alignment: Sequence[int | None, int | None] | None = None):
        """deprecated! translate viewport coordenates to pixel position for flexible displays."""
        if viewport is None:
            viewport = pygame.display.get_window_size()
        if alignment is None:
            self.rect.center = (viewport[0]*pos[0], viewport[1]*pos[1])
            return
        align = alignment[0]
        position = viewport[0]*pos[0]
        if align == K_CENTER:
            self.rect.centerx = position
        elif align == K_LEFT:
            self.rect.left = position
        elif align == K_RIGHT:
            self.rect.right = position

        align = alignment[1]
        position = viewport[1]*pos[1]
        if align == K_CENTER:
            self.rect.centery = position
        elif align == K_TOP:
            self.rect.top = position
        elif align == K_BOTTOM:
            self.rect.bottom = position

    def fit_to_image(self, threshold=1):
        """crops the sprite to the image bounds. useful for optimizing when blitting a lot."""
        bounds = self.image.get_bounding_rect(threshold)
        self.rect.update(bounds.move(self.rect.topleft))
        self.image = self.image.subsurface(bounds).copy()


class Button(GUISprite):
    def __init__(self, pos: tuple[int | float, int | float], image: pygame.Surface, action, priority=15, name="button",
                 use_viewport: bool = True, alignment: Sequence[int, int] = K_ALIGN_CENTER, hover=None,
                 press=None, unfocused=None, *groups: pygame.sprite.Group):
        super().__init__(pos, image, priority, name, use_viewport, alignment, *groups)
        self.mask = pygame.mask.from_surface(image, 0)

        self.click = action
        self.hover = self.placeholder if hover is None else hover
        self.press = self.placeholder if press is None else press
        self.lost_focus = self.placeholder if unfocused is None else unfocused
        self.active = False

    def is_hit(self, pos: Sequence[int, int]) -> bool:
        """checks if the given position is hovering over the bitmap"""
        hit_point = (pos[0]-self.rect.left, pos[1]-self.rect.top)
        return bool(self.rect.collidepoint(pos) and self.mask.get_at(hit_point))

    @staticmethod
    def placeholder():
        pass

    still_focused = is_hit

    def fit_to_image(self, threshold=1):
        """crops the sprite to the image bounds. useful for optimizing when blitting a lot."""
        bounds = self.image.get_bounding_rect(threshold)
        self.rect.update(bounds.move(self.rect.topleft))
        self.image = self.image.subsurface(bounds).copy()
        self.mask = pygame.mask.from_surface(self.image, 0)


class TextBox(Button):
    """simple textbox object. when added to gui as sprite it can be used as a simpel display for varias values.
    when added as a button it can handle input when clicked."""
    def __init__(self, pos: tuple[int | float, int | float], image: pygame.Surface, action, font=DEFAULT_FONT,
                 priority=15, name="textbox", use_viewport: bool = True, alignment: Sequence[int, int] = K_ALIGN_CENTER,
                 hover=None, text="", color=(255, 255, 255), text_alignment=0, spacing=(5.0, 0.5),
                 whitelist: Sequence[str] | set[str] = (), blacklist: Sequence[str] | set[str] = (), press=None,
                 *groups: pygame.sprite.Group):
        super().__init__(pos, image, self.start_input, priority, name, use_viewport, alignment, hover, self.on_press, None, *groups)
        self.text: str = text
        self.cursor: int = 0  # letter position. before the first letter = 0
        self.cursor_pos: int | float = 0.0  # x sprite position of cursor
        self.cursor_selected: list[int, int] = [0, 0]
        self.blink_speed: int = 500  # ms between flashes
        self.text_alignment: int = text_alignment  # 0=left 1=right 2=mid.
        self.text_pos: tuple[float | int, float | int] = spacing
        self.font: pygame.font.Font = font
        self.color: tuple[int, int, int] = color
        self.last_action: int = 0
        self.whitelist = whitelist
        self.blacklist = blacklist
        self.on_enter = action
        self.selected = press
        self.offset: int = 0

    def on_press(self):
        self.cursor, self.cursor_pos = self.cursor_from_mouse()
        self.cursor_selected[0] = self.cursor

    def start_input(self):
        if self.selected is not None:
            self.selected()
        self.active = True
        self.last_action = pygame.time.get_ticks()
        self.cursor, self.cursor_pos = self.cursor_from_mouse()
        if self.cursor == self.cursor_selected[0]:
            self.cursor_selected = [0, 0]
        elif self.cursor < self.cursor_selected[0]:
            self.cursor_selected = [self.cursor, self.cursor_selected[0]-self.cursor]
        else:
            self.cursor_selected = [self.cursor_selected[0], self.cursor-self.cursor_selected[0]]

        if self.cursor_selected[0] >= len(self.text):
            self.cursor_selected = [len(self.text), 0]
        elif (self.cursor_selected[0]+self.cursor_selected[1]) >= len(self.text):
            self.cursor_selected[1] = len(self.text) - self.cursor_selected[0]

    def cursor_from_mouse(self) -> tuple[int, int | float]:
        rect = self.get_text_rect()
        x, y = pygame.mouse.get_pos()
        global_x, global_y = self.get_global_rect().topleft
        x, y = x-global_x, y-global_y
        width = rect.x
        cursor: int = -1
        cursor_pos: float | int = width
        for i in range(len(self.text)+1):
            prev_width = width
            if self.text:
                width = pygame.font.Font.size(self.font, self.text[0:i])[0]+rect.x
            else:
                width = rect.x
            if width-x < 0:
                continue
            if width-x <= abs(prev_width-x):
                cursor = i
                cursor_pos = width
            else:
                cursor = i-1
                cursor_pos = prev_width
            break

        if cursor == -1:
            cursor = len(self.text)
            cursor_pos = width
        cursor = int(pygame.math.clamp(cursor, 0, len(self.text)))
        return cursor, cursor_pos

    def get_cursor_pos(self, pos: int | None = None) -> int:
        if pos is None:
            pos = self.cursor
        if self.text:
            return self.get_text_rect().x+pygame.font.Font.size(self.font, self.text[0:pos])[0]
        else:
            return self.get_text_rect().x

    def get_text_rect(self) -> pygame.rect.Rect:
        if self.text:
            x, y = pygame.font.Font.size(self.font, self.text)
        else:
            x = y = 0

        rect = pygame.rect.Rect(0, 0, x, y)
        if self.text_alignment == 0:  # left
            rect.x = self.text_pos[0]
            rect.centery = self.rect.h * self.text_pos[1]
            return rect

        elif self.text_alignment == 1:  # right
            rect.right = self.rect.w - self.text_pos[0]
            rect.centery = self.rect.h * self.text_pos[1]
            return rect

        elif self.text_alignment == 2:  # center
            rect.center = [self.rect[i+2]*self.text_pos[i] for i in range(2)]
            return rect

    def handle_input(self, character: str, constant: int):
        if not self.active:
            return

        def scroll():
            if self.cursor_pos > self.rect.width-5:
                self.offset = self.cursor_pos - self.rect.width + 5
            elif self.cursor_pos < 5:
                self.offset = self.cursor_pos - 5
            else:
                self.offset = 0

        if constant == pygame.K_RETURN:  # enter pressed
            self.cursor = 0
            self.cursor_selected = [0, 0]
            self.active = False
            self.offset = 0
            if self.on_enter is not None:
                self.on_enter()
            return
        self.last_action = pygame.time.get_ticks()
        if constant in {pygame.K_LEFT, pygame.K_RIGHT}:
            self.cursor = pygame.math.clamp(self.cursor + (1 if constant == pygame.K_RIGHT else -1), 0, len(self.text))
            self.cursor_pos = self.get_cursor_pos()
            self.cursor_selected = [0, 0]
            scroll()
            return
        if self.cursor_selected[1] > 0:
            self.text = self.text[:self.cursor_selected[0]] + self.text[sum(self.cursor_selected):]
            self.cursor = self.cursor_selected[0]
            self.cursor_selected = [0, 0]
            self.cursor_pos = self.get_cursor_pos()
            scroll()
            if constant in {pygame.K_BACKSPACE, pygame.K_DELETE}:
                return
        if constant == pygame.K_BACKSPACE:
            self.cursor = pygame.math.clamp(self.cursor, 0, len(self.text))
            if self.cursor == 0:
                return
            self.text = self.text[:self.cursor-1]+self.text[self.cursor:]
            self.cursor -= 1
            self.cursor_pos = self.get_cursor_pos()
            scroll()
            return
        if constant == pygame.K_DELETE:
            if self.cursor == len(self.text):
                return
            self.text = self.text[:self.cursor]+self.text[self.cursor+1:]
            self.cursor_pos = self.get_cursor_pos()
            scroll()
            return
        if len(character) == 1:
            if self.whitelist and character not in self.whitelist:
                return
            if self.blacklist and character in self.blacklist:
                return
            self.text = self.text[:self.cursor]+character+self.text[self.cursor:]
            self.cursor += 1
            self.cursor_pos = self.get_cursor_pos()
            scroll()

    def stop(self):
        self.handle_input("", pygame.K_RETURN)

    def filled_surface(self) -> pygame.surface.Surface:
        blit_surface = self.image.copy()
        pos = self.get_text_rect().move(-self.offset, 0).topleft
        if self.text:
            blit_surface.blit(self.font.render(self.text, True, self.color), pos)
        if self.active:
            if self.cursor_selected[1] > 0:
                x = self.get_cursor_pos(self.cursor_selected[0])
                w = self.get_cursor_pos(self.cursor_selected[0]+self.cursor_selected[1])-x
                selection_surface = colored_rect((50, 50, 255), (w, floor(self.rect.h*0.9)))
                selection_surface.set_alpha(150)
                blit_surface.blit(selection_surface, (x, ceil(self.rect.h*0.05)))
            if ((pygame.time.get_ticks()-self.last_action)//500) % 2 == 0:
                # draw cursor
                blit_surface.blit(colored_rect((255, 255, 255), (3, floor(self.rect.h*0.9))),
                                  (self.cursor_pos-1-self.offset, ceil(self.rect.h*0.05)))

        return blit_surface


class Dropdown(Button):
    def __init__(self, pos: tuple[int | float, int | float], image: pygame.Surface, option_image: pygame.Surface,
                 priority=15, name="dropdown", use_viewport: bool = True,
                 alignment: Sequence[int, int] = K_ALIGN_CENTER, hover=None, press=None,
                 options: list[Sequence[str, None]] = (), *groups: pygame.sprite.Group):
        super().__init__(pos, image, self.open, priority, name, use_viewport, alignment, hover, press, None, *groups)
        self.buttons: list[Button] = []
        self.buttons_sprite: GUISprite | None = None
        self.options = options
        self.option_surface = option_image
        self.scroll = 0.0
        self.max_scroll = 0.0
        self.scroll_speed = 1.0

    def open(self):
        """folds out the list"""
        self.scroll = 0.0
        if self.active:
            self.buttons.clear()
        if not len(self.options):
            return
        rect = pygame.rect.Rect((0, 0), self.option_surface.get_size())
        surf = pygame.Surface((rect.width, rect.height*len(self.options)), pygame.SRCALPHA)

        for option in self.options:
            button = Button(rect.topleft, center_text(option[0], self.option_surface, LIST_FONT), option[1],
                            name="option")
            button.parent = self
            self.buttons.append(button)
            surf.blit(button.filled_surface(), rect.topleft)
            rect.topleft = button.rect.bottomleft

        self.buttons_sprite = GUISprite((0, 0), surf)
        self.max_scroll = self.buttons_sprite.rect.height-self.buttons[0].rect.height
        self.scroll_speed = self.buttons[0].rect.height/4.0
        self.active = True

    def close(self):
        self.buttons.clear()
        self.max_scroll = 0.0
        self.scroll_speed = 1.0
        self.buttons_sprite = None
        self.active = False
        self.click = self.open

    stop = close

    def on_scroll(self, event: pygame.event.Event):
        if (not self.active) or self.buttons_sprite is None:
            return
        scroll = event.precise_y if float(event.y) == event.precise_y else -event.precise_y
        self.scroll = pygame.math.clamp(self.scroll + (scroll*self.scroll_speed), 0.0, self.max_scroll)

    def filled_surface(self) -> pygame.surface.Surface:
        if self.active and self.buttons_sprite is not None and self.parent is not None:
            rect = self.buttons_sprite.rect.move(0, int(self.scroll))
            rect.height -= self.scroll
            self.parent.image.blit(self.buttons_sprite.image.subsurface(rect),
                                   self.rect.move(0, self.rect.height).topleft)

        return self.image

    def is_hit(self, pos: tuple[int, int]) -> bool:
        """checks if the given position is hovering over the bitmap"""
        hit_point = [pos[0]-self.rect.left, pos[1]-self.rect.top]
        if self.rect.collidepoint(pos) and self.mask.get_at(hit_point):
            return True
        elif not self.active:
            return False
        hit_point[1] -= self.rect.height-int(self.scroll)
        for button in self.buttons:
            if button.is_hit(hit_point):
                self.click = button.click
                return True
        return False

    def still_focused(self, pos: tuple[int, int]) -> bool:
        """checks if the given position is hovering over the bitmap"""
        hit_point = [pos[0]-self.rect.left, pos[1]-self.rect.top]
        if self.rect.collidepoint(pos) and self.mask.get_at(hit_point):
            return True
        elif not self.active:
            return False
        hit_point[1] -= self.rect.height-int(self.scroll)
        for button in self.buttons:
            if button.is_hit(hit_point):
                return button.click is self.click
        return False


class GUI(GUISprite):
    def __init__(self, pos: tuple[int | float, int | float], background: pygame.Surface, priority=25, name="gui",
                 use_viewport: bool = True, alignment: Sequence[int, int] = K_ALIGN_CENTER,
                 *groups: pygame.sprite.Group):
        super().__init__(pos, background, priority, name, use_viewport, alignment, *groups)
        self.background = background.copy()  # background used during drawing routine
        self.source_image = background.copy()  # original image. used to reset background
        self.mask = pygame.mask.from_surface(background, 0)
        self.buttons: list[Button | TextBox | Dropdown] = []  # contains the buttons, used for button operations
        self.sub_GUIs: list[GUI] = []  # contains sub menus, used for menu operations
        # contains every object in order of priority, used for drawing operations
        self.sprites: list[GUISprite | Button | GUI | TextBox | Dropdown] = []
        self.focus: TextBox | Dropdown | Button | GUI | None = None
        self.active = False

    def bake_background(self):
        """bake elements to the background surface and removes them from the sprites list.
        usufull for reducing the amount of blitting calls"""
        self.background = self.filled_surface().copy()
        self.sprites.clear()

    def clear_background(self):
        """resets the background to normal. GUI.clear will also reset the background"""
        self.background = self.source_image.copy()

    def filled_surface(self) -> pygame.Surface:
        """returns a surface filled with all the elements."""
        self.image.blit(self.background, (0, 0))
        # recursive calls till the end is reached.
        self.image.blits([(sprite.filled_surface(), sprite.rect.topleft) for sprite in self.sprites], False)
        return self.image

    def set_surface(self, background: pygame.surface.Surface, redraw_self: bool = False) -> None:
        self.background = background.copy()
        self.source_image = background.copy()
        self.rect.update(self.rect.left, self.rect.top, background.get_width(), background.get_height())
        self._update_pos()
        if redraw_self:
            self.filled_surface()

    def calc_drawing_order(self):
        """recalculates the drawing order by using the priority of every sprite."""
        self.sprites.sort(key=lambda sprite: sprite.priority)

    # get functions
    def get_button(self, names: str | set[str]) -> list[Button | TextBox | Dropdown]:
        """returns a list of interactive menu objects with the given name"""
        if isinstance(names, str):
            return [button for button in self.buttons if button.name == names]
        else:
            return [button for button in self.buttons if button.name in names]

    def get_submenu(self, names: str | set[str]) -> list["GUI"]:
        """returns a list of gui objects with given names"""
        if isinstance(names, str):
            return [menu for menu in self.sub_GUIs if menu.name == names]
        else:
            return [menu for menu in self.sub_GUIs if menu.name in names]

    def get_sprite(self, names: str | set[str]) -> list[GUISprite | Button | TextBox | Dropdown]:
        """return a list of visible objects with the given names"""
        if isinstance(names, str):
            return [sprite for sprite in self.sprites if sprite.name == names]
        else:
            return [sprite for sprite in self.sprites if sprite.name in names]

    # adding objects
    def add_objects(self, sprites: Sequence[GUISprite | TextBox, ...] = (), buttons: Sequence[Button, ...] = (),
                    guis: Sequence["GUI", ...] = ()):
        self.sprites.extend(sprites)
        self.buttons.extend(buttons)
        self.sprites.extend(buttons)
        self.sub_GUIs.extend(guis)
        self.sprites.extend(guis)
        for sprite in sprites:
            sprite.parent = self
            sprite._update_pos()
        for button in buttons:
            button.parent = self
            button._update_pos()
        for gui in guis:
            gui.parent = self
            gui._update_pos()

    # removing objects
    def remove_objects(self, sprites: Sequence[GUISprite | TextBox, ...] = (), buttons: Sequence[Button, ...] = (),
                       guis: Sequence["GUI", ...] = ()):
        for sprite in sprites:
            try:
                self.sprites.remove(sprite)
            except ValueError:
                print("sprite not present")

        for button in buttons:
            try:
                self.buttons.remove(button)
                self.sprites.remove(button)
            except ValueError:
                print("button not present")

        for gui in guis:
            try:
                self.sub_GUIs.remove(gui)
                self.sprites.remove(gui)
            except ValueError:
                print("menu not present")

    def clear(self):
        self.buttons.clear()
        self.sub_GUIs.clear()
        self.sprites.clear()
        self.background = self.source_image.copy()

    # other

    def hit_reg(self, pos: tuple[int, int]) -> Button | TextBox | Dropdown | None:
        """finds and returns the first hit ui element that is not a GUI itself. works recursively on other GUI`s"""
        # localize the hit point
        hit_point = (pos[0]-self.rect.left, pos[1]-self.rect.top)
        # first check for submenus
        for menu in self.sub_GUIs:
            hit = menu.rect.collidepoint(hit_point) and menu.hit_reg(hit_point)
            if hit:
                self.focus = menu
                return hit

        # after that check buttons
        for button in self.buttons:
            if button.is_hit(hit_point):
                self.focus = button
                return button

        return None

    def still_focused(self, pos: tuple[int, int]) -> bool:
        """checks if the focused object is still hit"""
        return False if self.focus is None else self.focus.still_focused((pos[0]-self.rect.left, pos[1]-self.rect.top))

    def hover(self):
        self.focus.hover()

    def press(self):
        self.focus.press()

    def click(self):
        self.focus.click()

    def lost_focus(self):
        self.focus.lost_focus()

    def get_focus(self) -> None | Button | TextBox | Dropdown:
        if isinstance(self.focus, GUI):
            return self.focus.get_focus()
        return self.focus


class Screen(GUI):
    """top level gui. always contains the screen as its image"""
    def __init__(self, display: pygame.Surface, background: pygame.Surface | None = None, priority=100,
                 name="screen", fullscreen=True, *groups: pygame.sprite.Group):
        super().__init__((0, 0), display, priority, name, False, K_TOP_LEFT, *groups)
        self.background = display.copy() if background is None else background.copy()
        self.source_image = display.copy() if background is None else background.copy()
        self.fullscreen = fullscreen
        self.small_size = (ceil(self.rect.width*0.5), ceil(self.rect.height*0.5)) if fullscreen else self.rect.size

    def set_surface(self, background: pygame.surface.Surface, redraw_self: bool = False) -> None:
        self.background = background.copy()
        self.source_image = background.copy()
        if redraw_self:
            pass

    def toggle_fullscreen(self):
        """toggle the display between fullscreen and windowed mode"""
        self.fullscreen = not self.fullscreen
        old_surface = self.image.copy()
        if self.fullscreen:
            self.small_size = self.rect.size
            self.image = pygame.display.set_mode(flags=pygame.FULLSCREEN)
        else:
            self.image = pygame.display.set_mode(self.small_size, flags=pygame.RESIZABLE)
        self.update_rect()
        self.image.blit(old_surface, (0, 0))
        pygame.display.flip()

    def center_background(self):
        self.update_rect()
        source_rect = self.source_image.get_rect()
        source_rect.center = self.rect.center
        if self.background.get_size() != self.image.get_size():
            self.background = self.image.copy()
        self.background.blit(self.source_image, source_rect.topleft)

    def update_rect(self):
        self.rect.size = self.image.get_size()

    def draw_screen(self, flip: bool = True) -> None:
        self.filled_surface()
        if flip:
            pygame.display.flip()


__all__ = ["GUISprite", "Button", "TextBox", "Dropdown", "GUI", "Screen"]
