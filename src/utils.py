import subprocess
from gi.repository import Gtk, Adw, GLib
from typing import Callable
from threading import Thread
from gettext import gettext as _

from .data import data
from .settings import get_settings


# ------ Functions to show info ------ #


def show_toast(text: str) -> None:
    data["toast_overlay"].add_toast(Adw.Toast(title=text, timeout=3))


def show_message(text: str):
    def on_ok_clicked(btn, win):
        win.destroy()

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    win = Adw.Window(content=box, transient_for=data["main_window"], modal=True)
    text_view = Gtk.Label(
        label=text, justify=2, margin_top=10, margin_start=10, margin_end=10
    )
    box.append(text_view)
    ok_btn = Gtk.Button(
        label="OK", halign=Gtk.Align.CENTER, margin_top=20, margin_bottom=10
    )
    ok_btn.connect("clicked", on_ok_clicked, win)
    box.append(ok_btn)
    win.present()


class Spinner(Gtk.Spinner):
    def __init__(self):
        super().__init__()
        self.start()
        self.set_spinning(True)


# ------ Functions to run tasks in thread that so it doesn't block ui ------ #


def threaded(function: Callable):
    """
    Decorator to run function in thread.
    Don't forget to add threaded_callback() to the end of the function to run callback after the task is completed.
    """

    def wrapper(*args, **kwargs):
        Thread(target=function, args=args, kwargs=kwargs).start()

    return wrapper


def threaded_callback(function: Callable, *args):
    """
    Run passed function after threaded function completed.
    Add at the end of the threaded function.
    """
    GLib.idle_add(function, *args)
