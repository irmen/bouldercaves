try:
    from PIL import Image
    # from PIL import ImageTk
except ImportError:
    import tkinter
    import tkinter.messagebox
    r = tkinter.Tk()
    r.withdraw()
    # tkinter.messagebox.showerror("missing Python library",
    #                              "To run the cave editor, the 'pillow' or 'pil' python library is required, "
    #                              "including the 'imagetk' extension.")
    tkinter.messagebox.showerror("missing Python library",
                                 "To run the cave editor, the 'pillow' or 'pil' python library is required")
    raise SystemExit
