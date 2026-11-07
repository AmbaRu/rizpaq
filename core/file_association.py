













































































from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes

EXTENSION = ".zpaq"
PROG_ID = "Rizpaq.zpaq"
FRIENDLY_NAME = "Rizpaq Archive"

RZP_EXTENSION = ".rzp"
RZP_PROG_ID = "Rizpaq.rzp"
RZP_FRIENDLY_NAME = "Rizpaq Tasks Container"

                                      
UNIVERSAL_EXTENSIONS = {
    ".zip": ("Rizpaq.zip", "Rizpaq ZIP Archive"),
    ".7z":  ("Rizpaq.7z",  "Rizpaq 7Z Archive"),
    ".rar": ("Rizpaq.rar", "Rizpaq RAR Archive"),
}

_HKCU_CLASSES_PREFIX = "Software\\Classes"

                                                                          
_USER_CHOICE_PREFIX = (
    "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts"
)

                                                                       
                                                            
                                                                      
                                                                    
                         
_READ_CONTROL = 0x00020000
_WRITE_DAC = 0x00040000
_WRITE_OWNER = 0x00080000


def _ck(subpath: str) -> str:
    if subpath:
        return _HKCU_CLASSES_PREFIX + "\\" + subpath
    return _HKCU_CLASSES_PREFIX


                           
 
                                                                      
                                                                          
                                                                           
                                                                         
_CTX_FLAT = {
    f"SystemFileAssociations\\{EXTENSION}\\shell": {
        "Rizpaq.extract": {"label": "Распаковать сюда", "args": '--extract-here "%1"'},
        "Rizpaq.test":    {"label": "Проверить",        "args": '--test "%1"'},
    },
    "*\\shell": {
        "Rizpaq.create":  {"label": "Добавить в архив Rizpaq…", "args": '--create "%V"'},
    },
}

                                                                       
                                                                       
                                            
 
                                                                         
                                                                      
                                             
_LEGACY_CTX_KEYS = [
    f"SystemFileAssociations\\{EXTENSION}\\shell\\Rizpaq",
    f"\\shell\\Rizpaq",
    f"SystemFileAssociations\\{EXTENSION}\\shell\\open",
    f"SystemFileAssociations\\{EXTENSION}\\shell\\rz_open",
    f"SystemFileAssociations\\{EXTENSION}\\shell\\rz_extract",
    f"SystemFileAssociations\\{EXTENSION}\\shell\\rz_test",
    f"\\shell\\rz_create",
    "Directory\\Background\\shell\\rz_extract_bg",
]

                                                                     
                                                    
_LEGACY_KEYS_ZPAQ = [
    f"SystemFileAssociations\\{EXTENSION}\\shell\\Rizpaq",
    f"\\shell\\Rizpaq",
    f"SystemFileAssociations\\{EXTENSION}\\shell\\open",
    f"SystemFileAssociations\\{EXTENSION}\\shell\\rz_open",
    f"SystemFileAssociations\\{EXTENSION}\\shell\\rz_extract",
    f"SystemFileAssociations\\{EXTENSION}\\shell\\rz_test",
    f"\\shell\\rz_create",
    "Directory\\Background\\shell\\rz_extract_bg",
]

_LEGACY_KEYS_RZP = [
    f"SystemFileAssociations\\{RZP_EXTENSION}\\shell\\Rizpaq",
    f"SystemFileAssociations\\{RZP_EXTENSION}\\shell\\rz_open",
]


                                                                             
                          
                                                                             

def _default_exe_path() -> str:
    return sys.executable


def _open_command(exe_path: str) -> str:
    if getattr(sys, "frozen", False):
        return f'"{exe_path}" "%1"'
    here = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.abspath(os.path.join(here, "..", "main.py"))
    return f'"{exe_path}" "{main_py}" "%1"'


def _rzp_open_command(exe_path: str) -> str:
    pass







    if getattr(sys, "frozen", False):
        return f'"{exe_path}" "%1"'
    here = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.abspath(os.path.join(here, "..", "main.py"))
    return f'"{exe_path}" "{main_py}" "%1"'


def _verb_command(exe_path: str, verb_args: str) -> str:
    if getattr(sys, "frozen", False):
        return f'"{exe_path}" {verb_args}'
    here = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.abspath(os.path.join(here, "..", "main.py"))
    return f'"{exe_path}" "{main_py}" {verb_args}'


def _icon_value(exe_path: str) -> str:
    if getattr(sys, "frozen", False):
        return f'"{exe_path}",0'
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, ".."))
    for c in (os.path.join(root, "app.ico"), os.path.join(os.path.dirname(exe_path), "app.ico")):
        if os.path.isfile(c):
            return f'"{c}"'
    return f'"{exe_path}",0'


def _set_default(subpath: str, value: str) -> None:
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _ck(subpath)) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, value)


def _set_value(subpath: str, name: str, value: str) -> None:
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _ck(subpath)) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)


def _delete_key_tree(root, path: str) -> None:
    import winreg
    try:
        with winreg.OpenKey(root, path, 0, winreg.KEY_READ) as key:
            subkeys = []
            i = 0
            while True:
                try:
                    subkeys.append(winreg.EnumKey(key, i))
                    i += 1
                except OSError:
                    break
    except OSError:
        return
    for sub in subkeys:
        _delete_key_tree(root, f"{path}\\{sub}")
    try:
        winreg.DeleteKey(root, path)
    except OSError:
        pass


                                                                             
                                                    
                                                                             

def _clear_user_choice(ext: str) -> bool:
    pass




























    if os.name != "nt":
                                                                
        return True

    import winreg

    ext_norm = str(ext).strip().lower()
    if not ext_norm.startswith("."):
        ext_norm = "." + ext_norm

    key_path = f"{_USER_CHOICE_PREFIX}\\{ext_norm}\\UserChoice"

                                                               
                                                                    
    try:
        hkey = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
            0,
            winreg.KEY_READ | _READ_CONTROL | _WRITE_DAC | _WRITE_OWNER,
        )
    except FileNotFoundError:
                                                      
        return True
    except OSError:
                                                            
        return False

    acl_cleared = False
    try:
        advapi = ctypes.windll.advapi32

                                                                  
                                                                
        SE_FILE_OBJECT = 1
        DACL_SECURITY_INFORMATION = 0x00000004
        UNPROTECTED_DACL_SECURITY_INFORMATION = 0x80000000

        advapi.SetSecurityInfo.restype = wintypes.DWORD
        advapi.SetSecurityInfo.argtypes = [
            wintypes.HANDLE,              
            wintypes.DWORD,                   
            wintypes.DWORD,                     
            wintypes.LPVOID,                 
            wintypes.LPVOID,                 
            wintypes.LPVOID,             
            wintypes.LPVOID,             
        ]

        res = advapi.SetSecurityInfo(
            wintypes.HANDLE(int(hkey.handle)),
            SE_FILE_OBJECT,
            DACL_SECURITY_INFORMATION | UNPROTECTED_DACL_SECURITY_INFORMATION,
            None, None, None, None,
        )
                                                                     
        acl_cleared = (res == 0)
    except Exception:
        acl_cleared = False
    finally:
        try:
            hkey.Close()
        except Exception:
            pass

    if not acl_cleared:
        return False

                                                        
                                                                     
                                                   
    try:
        shlwapi = ctypes.windll.shlwapi
        shlwapi.SHDeleteKeyW.restype = ctypes.c_long
        shlwapi.SHDeleteKeyW.argtypes = [wintypes.HKEY, wintypes.LPCWSTR]

                                                            
                                                
        hkey_cu = wintypes.HKEY(int(winreg.HKEY_CURRENT_USER))
        rc = shlwapi.SHDeleteKeyW(hkey_cu, key_path)
                                                                  
                                 
        if rc in (0, 2):
            return True
                                                                    
                                                                      
                                                           
    except Exception:
        pass

    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        return True
    except OSError:
        return False


                                                                             
                                               
                                                                             

def _register_ext(ext: str, prog_id: str, friendly_name: str,
                  exe_path: str, icon: str, command: str = None) -> None:
    pass
    if command is None:
        command = _open_command(exe_path)
    _set_default(ext, prog_id)
    _set_default(prog_id, friendly_name)
    _set_default(f"{prog_id}\\DefaultIcon", icon)
    _set_default(f"{prog_id}\\shell\\open\\command", command)


def _unregister_ext(ext: str, prog_id: str) -> None:
    pass
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _ck(ext), 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, "")
        if value == prog_id:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, _ck(ext))
    except OSError:
        pass
    _delete_key_tree(winreg.HKEY_CURRENT_USER, _ck(prog_id))


def _notify_association_changed() -> None:
    try:
        SHCNE_ASSOCCHANGED = 0x08000000
        ctypes.windll.shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, 0, None, None)
    except Exception:
        pass


                                                                             
                  
                                                                             

def _remove_legacy_context_menus() -> None:
    import winreg
    for key_path in _LEGACY_CTX_KEYS:
        _delete_key_tree(winreg.HKEY_CURRENT_USER, _ck(key_path))
    for scope, verbs in _CTX_FLAT.items():
        for verb_id in verbs:
            _delete_key_tree(winreg.HKEY_CURRENT_USER, _ck(f"{scope}\\{verb_id}"))


def _register_context_menus(exe_path: str, icon: str) -> None:
    for scope, verbs in _CTX_FLAT.items():
        for verb_id, verb in verbs.items():
            verb_key = f"{scope}\\{verb_id}"
            _set_default(verb_key, verb["label"])
            _set_value(verb_key, "Icon", icon)
            _set_default(f"{verb_key}\\command", _verb_command(exe_path, verb["args"]))


def _unregister_context_menus() -> None:
    pass






    import winreg
    for scope, verbs in _CTX_FLAT.items():
        for verb_id in verbs:
            _delete_key_tree(winreg.HKEY_CURRENT_USER, _ck(f"{scope}\\{verb_id}"))
    for key_path in _LEGACY_CTX_KEYS:
        _delete_key_tree(winreg.HKEY_CURRENT_USER, _ck(key_path))


def _cleanup_hkcr_for_zpaq() -> None:
    pass














    import winreg
    for key_path in _LEGACY_KEYS_ZPAQ:
        _delete_key_tree(winreg.HKEY_CLASSES_ROOT, key_path)
    for verb_id in _CTX_FLAT.get(f"SystemFileAssociations\\{EXTENSION}\\shell", {}):
        _delete_key_tree(
            winreg.HKEY_CLASSES_ROOT,
            f"SystemFileAssociations\\{EXTENSION}\\shell\\{verb_id}",
        )
    _delete_key_tree(winreg.HKEY_CLASSES_ROOT, "\\shell\\Rizpaq.create")
    _delete_key_tree(winreg.HKEY_CLASSES_ROOT, PROG_ID)
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, EXTENSION, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, "")
        if value == PROG_ID:
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, EXTENSION)
    except OSError:
        pass


def _cleanup_hkcr_for_rzp() -> None:
    pass
    import winreg
    for key_path in _LEGACY_KEYS_RZP:
        _delete_key_tree(winreg.HKEY_CLASSES_ROOT, key_path)
    _delete_key_tree(winreg.HKEY_CLASSES_ROOT, RZP_PROG_ID)
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, RZP_EXTENSION, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, "")
        if value == RZP_PROG_ID:
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, RZP_EXTENSION)
    except OSError:
        pass


def _cleanup_hkcr_best_effort() -> None:
    pass







    _cleanup_hkcr_for_zpaq()
    _cleanup_hkcr_for_rzp()


                                                                             
                    
                                                                             

def is_registered() -> bool:
    pass
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _ck(EXTENSION), 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, "")
            return value == PROG_ID
    except OSError:
        return False


def is_rzp_registered() -> bool:
    pass
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _ck(RZP_EXTENSION), 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, "")
            return value == RZP_PROG_ID
    except OSError:
        return False


def is_universal_registered(ext: str) -> bool:
    pass
    info = UNIVERSAL_EXTENSIONS.get(ext.lower())
    if not info:
        return False
    prog_id = info[0]
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _ck(ext), 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, "")
            return value == prog_id
    except OSError:
        return False


                                                                             
                                 
 
                                                            
                                                                        
                                                                  
                                                                      
                                                              
               
                                                                             

def register_zpaq(exe_path: str = None) -> None:
    pass
    if exe_path is None:
        exe_path = _default_exe_path()
    exe_path = os.path.abspath(exe_path)
    icon = _icon_value(exe_path)
    _register_ext(EXTENSION, PROG_ID, FRIENDLY_NAME, exe_path, icon)
    _remove_legacy_context_menus()
    _register_context_menus(exe_path, icon)
    _notify_association_changed()


def unregister_zpaq() -> bool:
    pass






    _unregister_ext(EXTENSION, PROG_ID)
    _unregister_context_menus()
                                                          
    _cleanup_hkcr_for_zpaq()
    _notify_association_changed()
    return _clear_user_choice(EXTENSION)


def register_rzp(exe_path: str = None) -> None:
    pass
    if exe_path is None:
        exe_path = _default_exe_path()
    exe_path = os.path.abspath(exe_path)
    icon = _icon_value(exe_path)
    rzp_command = _rzp_open_command(exe_path)
    _register_ext(RZP_EXTENSION, RZP_PROG_ID, RZP_FRIENDLY_NAME,
                  exe_path, icon, command=rzp_command)
    _notify_association_changed()


def unregister_rzp() -> bool:
    pass







    _unregister_ext(RZP_EXTENSION, RZP_PROG_ID)
    _cleanup_hkcr_for_rzp()
    _notify_association_changed()
    return _clear_user_choice(RZP_EXTENSION)


def register_universal(ext: str, exe_path: str = None) -> None:
    pass
    info = UNIVERSAL_EXTENSIONS.get(ext.lower())
    if not info:
        return
    if exe_path is None:
        exe_path = _default_exe_path()
    exe_path = os.path.abspath(exe_path)
    prog_id, friendly = info
    icon = _icon_value(exe_path)
    _register_ext(ext, prog_id, friendly, exe_path, icon)
    _notify_association_changed()


def unregister_universal(ext: str) -> bool:
    pass





    info = UNIVERSAL_EXTENSIONS.get(ext.lower())
    if not info:
        return True
    prog_id = info[0]
    _unregister_ext(ext, prog_id)
    _notify_association_changed()
    return _clear_user_choice(ext)


                                                                             
                                                                        
                                                                             

def register(exe_path: str = None) -> None:
    pass
    register_zpaq(exe_path)
    register_rzp(exe_path)


def unregister() -> bool:
    pass





    ok_zpaq = unregister_zpaq()
    ok_rzp = unregister_rzp()
    return ok_zpaq and ok_rzp


                                                                             
             
                                                                             

def _read_default(path: str):
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _ck(path), 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, "")
            return value
    except OSError:
        return None


def _read_value(path: str, name: str):
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _ck(path), 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, name)
            return value
    except OSError:
        return None


def _dump_key_tree(path: str, indent: int = 0) -> None:
    import winreg
    prefix = "  " * indent
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _ck(path), 0, winreg.KEY_READ) as key:
            values = []
            i = 0
            while True:
                try:
                    name, value, _vtype = winreg.EnumValue(key, i)
                except OSError:
                    break
                disp = name if name else "(Default)"
                values.append((disp, value))
                i += 1
            subkeys = []
            j = 0
            while True:
                try:
                    subkeys.append(winreg.EnumKey(key, j))
                except OSError:
                    break
                j += 1
        for disp, value in values:
            print(f"{prefix}{disp} = {value!r}")
        for sk in subkeys:
            print(f"{prefix}[{sk}]")
            _dump_key_tree(f"{path}\\{sk}", indent + 1)
    except OSError as exc:
        print(f"{prefix}(ключ недоступен: {exc})")


def diagnose() -> None:
    import winreg
    print("=== Диагностика ассоциации .zpaq (HKCU\\Software\\Classes) ===")
    prog_id = None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _ck(EXTENSION), 0, winreg.KEY_READ) as key:
            prog_id, _ = winreg.QueryValueEx(key, "")
        print(f"HKCU\\Software\\Classes\\{EXTENSION}  ->  {prog_id!r}")
    except OSError as exc:
        print(f"HKCU\\Software\\Classes\\{EXTENSION}  не найден ({exc}).")
    if prog_id == PROG_ID:
        print(f"Команда открытия:  {_read_default(PROG_ID + chr(92) + 'shell' + chr(92) + 'open' + chr(92) + 'command')}")
        print(f"Иконка:            {_read_default(PROG_ID + chr(92) + 'DefaultIcon')}")
    print()
    print("=== Диагностика ассоциации .rzp ===")
    rzp_prog_id = None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _ck(RZP_EXTENSION), 0, winreg.KEY_READ) as key:
            rzp_prog_id, _ = winreg.QueryValueEx(key, "")
        print(f"HKCU\\Software\\Classes\\{RZP_EXTENSION}  ->  {rzp_prog_id!r}")
    except OSError as exc:
        print(f"HKCU\\Software\\Classes\\{RZP_EXTENSION}  не найден ({exc}).")
    print()
    print("=== Универсальные форматы ===")
    for ext in (".zip", ".7z", ".rar"):
        status = "Rizpaq" if is_universal_registered(ext) else "нет"
        print(f"  {ext}: {status}")
    print()
    print("Контекстное меню (плоские пункты Rizpaq):")
    for scope, verbs in _CTX_FLAT.items():
        print(f"  [{scope}]")
        for verb_id, verb in verbs.items():
            vlabel = _read_default(f"{scope}\\{verb_id}")
            vcmd = _read_default(f"{scope}\\{verb_id}\\command")
            if vlabel and vcmd:
                print(f"    ✓ {verb['label']}")
            else:
                print(f"    ✗ {verb['label']} — НЕ зарегистрирован")
    if not getattr(sys, "frozen", False):
        print(f"\nИнтерпретатор: {sys.executable}")
