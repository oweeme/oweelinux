"""Edición segura del rc.xml de labwc del usuario (~/.config/labwc/rc.xml). Si no existe, parte de una copia del de sistema (/etc/xdg/labwc/rc.xml), así los atajos
y el aspecto de OweeLinux se conservan. Se conservan los comentarios; la escritura es atómica y después se pide a labwc recargar (`labwc --reconfigure`)."""
import os, shutil, xml.etree.ElementTree as ET
from .base import run, config_home

def reconfigure():
    """Pide a labwc recargar su configuración (tema, rc.xml, environment). labwc exige LABWC_PID: lo hereda quien se lanzó desde la sesión; si no está (p. ej. desde una terminal ajena) se busca."""
    run(["sh", "-c", 'LABWC_PID="${LABWC_PID:-$(pgrep -u "$(id -u)" -x labwc | head -1)}" labwc --reconfigure'], timeout=5)
USER = os.path.join(config_home(), "labwc", "rc.xml"); SYSTEM = "/etc/xdg/labwc/rc.xml"

def _parse(path): return ET.parse(path, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True)))

def load():
    if not os.path.exists(USER):
        os.makedirs(os.path.dirname(USER), exist_ok=True)
        if os.path.exists(SYSTEM): shutil.copyfile(SYSTEM, USER)
        else: open(USER, "w").write("<?xml version=\"1.0\"?>\n<labwc_config>\n</labwc_config>\n")
    return _parse(USER)

def _seg(seg):
    """'device[category=touchpad]' → ('device', {'category': 'touchpad'})"""
    if "[" in seg: tag, rest = seg.split("[", 1); return tag, dict(kv.split("=", 1) for kv in rest.rstrip("]").split(","))
    return seg, None

def find(root, path, create=False):
    """path como 'libinput/device[category=touchpad]/tap'. Un 'device' sin corchetes es el genérico (el que no tiene atributo category)."""
    node = root
    for seg in path.split("/"):
        tag, want = _seg(seg)
        def ok(c):
            if c.tag != tag: return False
            if want: return all(c.get(k) == v for k, v in want.items())
            return not c.get("category") if tag == "device" else True
        nxt = next((c for c in node if ok(c)), None)
        if nxt is None:
            if not create: return None
            nxt = ET.SubElement(node, tag, want or {}); nxt.text = "\n"
        node = nxt
    return node

def get(path, default=None):
    try: n = find(_parse(USER if os.path.exists(USER) else SYSTEM).getroot(), path)
    except (OSError, ET.ParseError): return default
    return (n.text or "").strip() if n is not None and n.text and n.text.strip() else default

def set_values(items, reload=True):
    """items: lista de (path, valor). Un valor None borra el elemento."""
    tree = load(); root = tree.getroot()
    for path, value in items:
        n = find(root, path, create=value is not None)
        if n is None: continue
        if value is None:
            parent = find(root, path.rsplit("/", 1)[0]) if "/" in path else root
            if parent is not None: parent.remove(n)
        else: n.text = str(value)
    ET.indent(tree, space="  "); tmp = USER + ".tmp"; tree.write(tmp, encoding="utf-8", xml_declaration=True); os.replace(tmp, USER)
    if reload: reconfigure()


def edit(fn, reload=True):
    """Edición libre: fn(root) modifica el árbol del rc.xml de usuario (que se crea desde el de sistema si no existe); se guarda con escritura atómica y labwc recarga."""
    tree = load(); fn(tree.getroot()); ET.indent(tree, space="  "); tmp = USER + ".tmp"; tree.write(tmp, encoding="utf-8", xml_declaration=True); os.replace(tmp, USER)
    if reload: reconfigure()
