import inspect
import sys

import id3vx.frame


classes = inspect.getmembers(sys.modules["id3vx.frame"], inspect.isclass)
FRAMES = {name: clazz for (name, clazz) in classes}

print(FRAMES)