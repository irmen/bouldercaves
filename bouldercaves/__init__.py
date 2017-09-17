import os
try:
    from PIL import Image
except ImportError:
    import tkinter
    import tkinter.messagebox
    r = tkinter.Tk()
    r.withdraw()
    tkinter.messagebox.showerror("missing Python library", "The 'pillow' or 'pil' python library is required.")
    raise SystemExit

user_data_dir = os.path.expanduser("~/.bouldercaves/")
os.makedirs(user_data_dir, exist_ok=True)
