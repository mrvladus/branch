import os
from gi.repository import Adw, Gtk, GLib, Gio
from typing import Callable

from .data import data
from .settings import SettingsWindow, init_settings, get_setting, set_setting
from .add_dialog import AddDialog
from .repo_page import RepoPage


class Application(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.github.mrvladus.Branch")
        self.create_action("quit", self.quit, ["<primary>q"])
        self.create_action("about", self.on_about_action)
        self.create_action("settings", self.on_settings_action)

    def do_activate(self) -> None:
        self.init_files()
        init_settings()
        self.win = MainWindow(self)
        self.win.present()

    def init_files(self) -> None:
        """
        Create application directory to store settings and repos files.
        """
        data["repo_file"] = GLib.get_user_cache_dir() + "/branch/branch.repos"
        os.system(f"mkdir -p {GLib.get_user_cache_dir()}/branch")
        os.system(f"touch {data['repo_file']}")

    def on_about_action(self, widget, _) -> None:
        """
        Show about window.
        """
        self.win.about_window.set_transient_for(self.win)
        self.win.about_window.show()

    def on_settings_action(self, widget, _) -> None:
        SettingsWindow(self.win).show()

    def create_action(self, name: str, callback: Callable, shortcuts=None) -> None:
        """
        Create actions for main menu
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


@Gtk.Template(resource_path="/com/github/mrvladus/branch/window.ui")
class MainWindow(Adw.ApplicationWindow):
    __gtype_name__ = "MainWindow"

    toast_overlay = Gtk.Template.Child()
    tab_view = Gtk.Template.Child()
    tab_bar = Gtk.Template.Child()
    status_page = Gtk.Template.Child()
    about_window = Gtk.Template.Child()

    def __init__(self, app: Adw.Application):
        super().__init__()
        self.props.application = app
        self.props.default_width = get_setting("window_width")
        self.props.default_height = get_setting("window_height")
        data["main_window"] = self
        data["toast_overlay"] = self.toast_overlay
        self.get_settings().props.gtk_icon_theme_name = "Adwaita"
        self.init_repos()
        self.update_status()

    def init_repos(self) -> None:
        """
        Read repos file and add page for each repo.
        """
        with open(data["repo_file"], "r") as f:
            for path in f:
                page = RepoPage(path.strip())
                self.tab_view.append(page)
                self.tab_view.get_page(page).set_title(os.path.basename(path.strip()))

    @Gtk.Template.Callback()
    def on_close_request(self, window: Adw.ApplicationWindow) -> None:
        """
        Remember window dimensions on close.
        """
        set_setting("window_width", self.get_allocated_width())
        set_setting("window_height", self.get_allocated_height())

    @Gtk.Template.Callback()
    def on_add_btn_clicked(self, btn: Gtk.Button) -> None:
        """
        Show add dialog.
        """
        AddDialog(self, self.tab_view).show()

    @Gtk.Template.Callback()
    def on_close_page(self, view: Adw.TabView, page: Adw.TabPage) -> None:
        """
        Remove page and line in repos file.
        """
        page.get_child().delete()
        view.close_page_finish(page, True)
        self.update_status()

    def update_status(self) -> None:
        """
        Show 'Repos not found message' if there is no tabs.
        Call this function every time tabs changes.
        """
        if self.tab_view.get_n_pages() == 0:
            self.status_page.props.visible = True
            self.tab_bar.props.visible = False
        else:
            self.status_page.props.visible = False
            self.tab_bar.props.visible = True


def main():
    app = Application()
    return app.run()
