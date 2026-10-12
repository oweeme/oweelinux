#!/usr/bin/env python3
"""Lista las ventanas abiertas con pywayland + ext-foreign-toplevel-list-v1 (PROTOTIPO de riesgos: ¿puede Python
listar ventanas, base de Alt+Tab y de la vista general?). Los enlaces del protocolo se generan en la imagen con
`python3 -m pywayland.scanner` (Debian no trae ningún protocolo con python3-pywayland).
Solo LISTA (título, app_id): activar o cerrar ventanas necesita wlr-foreign-toplevel-management, cuyo XML no está en Debian."""
import json, os, sys
sys.path.insert(0, os.environ.get("OWEE_WLGEN", "/usr/lib/owee/wlgen"))
from pywayland.client import Display
from ext_foreign_toplevel_list_v1 import ExtForeignToplevelListV1

windows = {}
def on_toplevel(_lst, handle):
    info = windows.setdefault(handle, {"title": "", "app_id": ""})
    handle.dispatcher["title"] = lambda h, t: info.update(title=t)
    handle.dispatcher["app_id"] = lambda h, a: info.update(app_id=a)
    handle.dispatcher["closed"] = lambda h: windows.pop(h, None)

def on_global(reg, name, interface, version):
    if interface == "ext_foreign_toplevel_list_v1":
        lst = reg.bind(name, ExtForeignToplevelListV1, 1); lst.dispatcher["toplevel"] = on_toplevel

d = Display(); d.connect(); reg = d.get_registry(); reg.dispatcher["global"] = on_global
for _ in range(4): d.roundtrip()
print(json.dumps(sorted(windows.values(), key=lambda w: w["title"]), ensure_ascii=False))
d.disconnect()
