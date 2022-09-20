import os
from gi.repository import Gtk, Adw
from gettext import gettext as _

from .data import data
from .utils import show_toast
from .repo_page import RepoPage


@Gtk.Template(resource_path="/com/github/mrvladus/branch/ui/add_dialog.ui")
class AddDialog(Gtk.FileChooserDialog):
    __gtype_name__ = "AddDialog"

    def __init__(self, main_window: Adw.ApplicationWindow, tab_view: Adw.TabView):
        super().__init__()
        self.main_window = main_window
        self.tab_view = tab_view
        self.set_transient_for(self.main_window)

    @Gtk.Template.Callback()
    def on_response(self, widget: Gtk.Widget, response: int) -> None:
        # Hide dialog
        self.hide()
        if response == Gtk.ResponseType.OK:
            # Add page for each repo
            path = self.get_file().get_path()
            with open(data["repo_file"], "r+") as f:
                text = f.read()
                # If repo exists - add new page
                if path not in text and os.path.exists(path + "/.git"):
                    f.write(path + "\n")
                    page = RepoPage(path)
                    self.tab_view.append(page)
                    self.tab_view.get_page(page).set_title(os.path.basename(path))
                    self.tab_view.set_selected_page(self.tab_view.get_page(page))
                    self.main_window.update_status()
                elif path in text:
                    show_toast(_("Repository already added"))
                elif not path in text and not os.path.exists(path + "/.git"):
                    show_toast(("Not a git repository"))
