import json, os
from gi.repository import Adw, Gtk, GLib

from .data import data

default_settings = {
    "window_height": 300,
    "window_width": 500,
    "email": "",
    "name": "",
    "github_username": "",
    "github_token": "",
}


def init_settings() -> None:
    # Create settings file if not exists
    data["settings_file"] = GLib.get_user_cache_dir() + "/branch/settings.json"
    os.system(f"touch {data['settings_file']}")
    # Load file
    with open(data["settings_file"], "r") as f:
        content = f.read()
    # If new settings added then add a new setting to existing file
    if content != "":
        old_settings = json.loads(content)
        if sorted(list(default_settings.keys())) != sorted(list(old_settings.keys())):
            for key in default_settings:
                if key not in old_settings:
                    old_settings[key] = default_settings[key]
                    with open(data["settings_file"], "w") as f:
                        json.dump(old_settings, f)
    # Create default settings if file is empty
    else:
        with open(data["settings_file"], "w") as f:
            json.dump(default_settings, f)


def get_settings() -> dict:
    with open(data["settings_file"], "r") as f:
        return json.load(f)


def get_setting(setting: str) -> str:
    settings = get_settings()
    return settings[setting]


def set_setting(setting: str, value: str) -> None:
    new_settings = get_settings()
    # Set new value
    new_settings[setting] = value
    # Write to file
    with open(data["settings_file"], "w") as f:
        json.dump(new_settings, f)


@Gtk.Template(resource_path="/com/github/mrvladus/branch/ui/settings.ui")
class SettingsWindow(Adw.PreferencesWindow):
    __gtype_name__ = "SettingsWindow"

    name = Gtk.Template.Child()
    email = Gtk.Template.Child()
    github_username = Gtk.Template.Child()
    github_token = Gtk.Template.Child()

    def __init__(self, main_window):
        super().__init__(transient_for=main_window)
        # Set all fields
        settings = get_settings()
        self.name.props.text = settings["name"]
        self.email.props.text = settings["email"]
        self.github_username.props.text = settings["github_username"]
        self.github_token.props.text = settings["github_token"]

    @Gtk.Template.Callback()
    def on_email_changed(self, widget: Adw.EntryRow) -> None:
        set_setting("email", widget.props.text)

    @Gtk.Template.Callback()
    def on_name_changed(self, widget: Adw.EntryRow) -> None:
        set_setting("name", widget.props.text)

    @Gtk.Template.Callback()
    def on_github_username_changed(self, widget: Adw.EntryRow) -> None:
        set_setting("github_username", widget.props.text)

    @Gtk.Template.Callback()
    def on_github_token_changed(self, widget: Adw.PasswordEntryRow) -> None:
        set_setting("github_token", widget.props.text)

    @Gtk.Template.Callback()
    def on_reset_git_btn_clicked(self, btn: Gtk.Button) -> None:
        self.email.props.text = ""
        self.name.props.text = ""

    @Gtk.Template.Callback()
    def on_reset_github_btn_clicked(self, btn: Gtk.Button) -> None:
        self.github_token.props.text = ""
        self.github_username.props.text = ""
