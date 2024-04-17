import pygame


def colored_rect(color, size, transparent=False, srcalpha=False):
    """creates a simple rectangle with the given color."""
    if srcalpha:
        surface = pygame.Surface(size, pygame.SRCALPHA)
    else:
        surface = pygame.Surface(size)  # create a surface
    surface.fill(color)
    if transparent:
        surface.set_colorkey(color)
    return surface


def comp_text_box(length: int):
    """creates a textbox from the text box image at the given length."""
    path = __file__[0:__file__.rfind("\\")]
    surface = colored_rect((0, 0, 0), (length, 40), True).convert_alpha()
    side_image = get_img("text_box_side", path)
    surface.blits([(side_image, (0, 0)), (pygame.transform.scale(get_img("text_box_line", path), (length-16, 40)),
                                          (8, 0)),
                   (pygame.transform.flip(side_image, True, False), (length-8, 0))], False)
    return surface


def get_img(name: str, folder: str | None = None, alpha=True, extension=".png") -> pygame.Surface:
    """returns a converted image from the texture`s folder. alpha optional"""
    if folder is not None:
        name = rf"{folder}\{name}"
    if alpha:
        return pygame.image.load(name + extension).convert_alpha()
    else:
        return pygame.image.load(name + extension).convert()


def center_text(text: str, surface: pygame.Surface, font: pygame.font.Font,
                color=(255, 255, 255), pos=(0.5, 0.5), smooth=True) -> pygame.Surface:
    """"blits text centered on the given surface and returns that surface"""
    text_surface = font.render(text, smooth, color)
    surface_rect = surface.get_rect()
    text_rect = text_surface.get_rect()
    text_rect.center = (round(surface_rect.width*pos[0]), round(surface_rect.height*pos[1]))
    compound = surface.copy()
    compound.blit(text_surface, text_rect.topleft)
    return compound


def safe_subsurface(parent_surface: pygame.Surface, area: pygame.Rect) -> pygame.Surface:
    """unlike getting a subsurface normally this function returns new surface that does not
    share its pixels with the original surface"""
    try:
        child_surface = parent_surface.subsurface(area).copy()
    except ValueError:
        child_surface = pygame.Surface(area.size, 0, parent_surface)
        child_surface.blit(parent_surface, (-area.x, -area.y))
    return child_surface


__all__ = ["colored_rect", "comp_text_box", "get_img", "center_text", "safe_subsurface"]
