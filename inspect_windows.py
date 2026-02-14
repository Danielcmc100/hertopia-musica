from Xlib import display


def print_window_hierarchy(window, indent=0):
    try:
        children = window.query_tree().children
        for child in children:
            name = child.get_wm_name()
            cls = child.get_wm_class()
            print(f"{'  ' * indent}ID: {hex(child.id)} | Name: {name} | Class: {cls}")
            print_window_hierarchy(child, indent + 1)
    except Exception:
        pass


d = display.Display()
root = d.screen().root
print("Root Window Hierarchy:")
print_window_hierarchy(root)
