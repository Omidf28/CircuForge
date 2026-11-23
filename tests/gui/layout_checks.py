"""Explicit display-only component checks; default core pytest never requires Tk.

Run explicitly with pytest tests/gui/layout_checks.py on a Tk/display host.
These construct their own hidden window and inspect widget geometry; they never
control another application, synthesize OS input or run a simulation.
"""
from types import SimpleNamespace

import pytest
import tkinter as tk

from circuforge.desktop.app import DesktopApp


@pytest.fixture(scope="module")
def desktop(tmp_path_factory):
    root = tk.Tk()
    root.withdraw()
    root.attributes("-alpha", 0)
    app = DesktopApp(root, output_root=tmp_path_factory.mktemp("desktop-layout") / "unused")
    root.deiconify()
    yield root, app
    root.destroy()


def contained(widget, parent):
    x = widget.winfo_rootx() - parent.winfo_rootx()
    y = widget.winfo_rooty() - parent.winfo_rooty()
    return (x >= 0 and y >= 0 and x + widget.winfo_width() <= parent.winfo_width() and
            y + widget.winfo_height() <= parent.winfo_height())


@pytest.mark.parametrize("width,height", [(1040, 620), (1040, 760), (1280, 900)])
def test_run_progress_and_saved_folder_remain_in_the_client_area(desktop, width, height):
    root, app = desktop
    root.geometry(f"{width}x{height}")
    root.update()
    assert (root.winfo_width(), root.winfo_height()) == (width, height)
    for widget in (app.run_button, app.progress, app.open_button, app.form_canvas):
        assert contained(widget, root), f"{widget} clipped at {width}x{height}"
    assert not app.controller.busy


def test_all_settings_scroll_into_view_without_hijacking_chart_wheel(desktop):
    root, app = desktop
    root.geometry("1040x620")
    root.update()
    app.form_canvas.yview_moveto(1)
    root.update()
    assert contained(app.output_entry, app.form_canvas)
    assert contained(app.executable_entry, app.form_canvas)
    before = app.form_canvas.yview()
    assert before[0] > 0
    x, y = app.form_canvas.winfo_rootx(), app.form_canvas.winfo_rooty()
    assert app._scroll_form(SimpleNamespace(x_root=x + 30, y_root=y + 30, delta=120)) == "break"
    root.update()
    assert app.form_canvas.yview()[0] < before[0]
    before = app.form_canvas.yview()
    assert app._scroll_form(SimpleNamespace(x_root=x + app.form_canvas.winfo_width() + 40,
                                           y_root=y + 30, delta=-120)) is None
    assert app.form_canvas.yview() == before
