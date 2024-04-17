import pygame.event
import pygame.surface
import pygame.display
from pygui.elements import GUI, TextBox, Dropdown, Screen

DRAW_SCREEN = pygame.event.custom_type()
display: Screen


def init(screen: pygame.Surface, background_image: pygame.Surface | None = None, fullscreen=True) -> Screen:
    global display, event_functions
    display = Screen(screen, background_image, fullscreen=fullscreen)
    pygame.event.set_allowed((pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION, pygame.KEYDOWN,
                              pygame.KEYUP, pygame.QUIT, DRAW_SCREEN))
    event_functions[DRAW_SCREEN] = display.draw_screen
    return display


def handle_events():
    """should be called once per frame to handle internal ui stuff. can also take over the main event loop by adding
    functions to event_functions"""
    for event in pygame.event.get():
        if pygame.event.get_blocked(event.type):  # sometimes events are still posted when blocked.
            continue
        try:
            event_function = event_functions[event.type]
        except KeyError:
            print(f"no function was found for event {pygame.event.event_name(event.type)}.")
            continue
        event_function(event)  # run function outside try except block. (helps with debugging)


def handle_single(event: pygame.event.Event):
    if pygame.event.get_blocked(event.type):  # sometimes events are still posted when blocked.
        return
    try:
        event_function = event_functions[event.type]
    except KeyError:
        print(f"no function was found for event {pygame.event.event_name(event.type)}.")
        return
    event_function(event)  # run function outside try except block. (helps with debugging)


def on_mouse_press(event: pygame.event.Event):
    """"checks if any buttons are hit"""
    if event.button != 1:
        return
    focus = display.get_focus()
    result = display.hit_reg(event.pos)
    if focus is not None and focus.active and focus is not result:  # deactivate any active element
        focus.stop()
        pygame.event.post(pygame.event.Event(DRAW_SCREEN))

    if result:
        result.press()


def on_mouse_release(event: pygame.event.Event):
    """activates any held buttons"""
    if event.button != 1:
        return
    if display.still_focused(event.pos):
        display.click()
        if not display.get_focus().active:
            display.focus = None
    elif display.focus is not None:
        display.lost_focus()
        display.focus = None


def on_mouse_move(event: pygame.event.Event):
    """monitors if buttons are still held down"""
    if display.focus is None or not pygame.mouse.get_pressed()[0]:
        return
    if not display.still_focused(event.pos):
        pygame.event.set_blocked(pygame.MOUSEMOTION)
        display.lost_focus()
        display.focus = None


def on_scroll(event: pygame.event.Event):
    focus = display.get_focus()
    if isinstance(focus, Dropdown) and focus.active:
        focus.on_scroll(event)


def on_key_press(event):
    focus = display.get_focus()
    if isinstance(focus, TextBox) and focus.active:
        focus.handle_input(event.unicode, event.key)
        pygame.event.post(pygame.event.Event(DRAW_SCREEN))


def on_key_release(_event):
    pass


active_element = None


event_functions = {pygame.MOUSEBUTTONDOWN: on_mouse_press, pygame.MOUSEBUTTONUP: on_mouse_release,
                   pygame.MOUSEMOTION: on_mouse_move, pygame.MOUSEWHEEL: on_scroll,
                   pygame.KEYDOWN: on_key_press, pygame.KEYUP: on_key_release}


__all__ = ["init", "event_functions", "handle_events", "DRAW_SCREEN", "on_mouse_press", "on_mouse_release",
           "on_mouse_move", "on_scroll", "on_key_press", "on_key_release", "handle_single"]
