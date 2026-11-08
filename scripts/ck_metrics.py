#!/usr/bin/env python3
"""
ЛР8: об'єктні метрики Чидамбера-Кемерера (CK) та MOOD для Python-проєкту.

Навіщо: SonarQube Community для Python НЕ віддає CBO, LCOM4, DIT, MHF, AHF, COF
(в API є лише complexity, cognitive_complexity, classes, functions, ncloc),
тому відсутні метрики рахуються статичним аналізом AST (Abstract Syntax Tree:
абстрактне синтаксичне дерево) і зберігаються у JSON у тому ж стилі, що й
відповідь SonarQube Web API.

Запуск (з кореня проєкту):
    python3 scripts/ck_metrics.py <мітка>  [--root .] [--out reports/lab8]
Приклад:
    python3 scripts/ck_metrics.py baseline
Результат: reports/lab8/ck_mood_<мітка>.json + таблиця в консолі.

Лише стандартна бібліотека (Python 3.9+).
"""
import argparse
import ast
import json
import os
import sys

EXCLUDE_DIRS = {"scripts", ".venv", ".venv_old", "venv", "exp1", "tests", "reports", ".idea",
                "__MACOSX", ".sonar", ".git", ".github", "templates", "history",
                "__pycache__", ".pytest_cache", "node_modules"}

# Файли ЛР6: три архітектурні ролі
ROLE_FILES = {
    "Core Domain": "privacy/consent.py",
    "Infrastructure": "queries.py",
    "Utility/DTO": "models.py",
}


# ----------------------------------------------------------------------------
# Збір файлів і класів
# ----------------------------------------------------------------------------
def iter_py_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            if fn.endswith(".py"):
                yield os.path.join(dirpath, fn)


def cyclomatic(node):
    """McCabe CC (Cyclomatic Complexity) функції: 1 + кількість точок розгалуження."""
    cc = 1
    for n in ast.walk(node):
        if isinstance(n, (ast.If, ast.For, ast.AsyncFor, ast.While,
                          ast.ExceptHandler, ast.IfExp, ast.Assert)):
            cc += 1
        elif isinstance(n, ast.BoolOp):
            cc += len(n.values) - 1
        elif isinstance(n, ast.comprehension):
            cc += 1 + len(n.ifs)
    return cc


def is_dunder(name):
    return name.startswith("__") and name.endswith("__")


def module_imports(tree):
    """Імена, імпортовані модулем. Повертає (named, star_modules)."""
    named, stars = set(), []
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom):
            for a in n.names:
                if a.name == "*":
                    stars.append(n.module or "")
                else:
                    named.add(a.asname or a.name)
        elif isinstance(n, ast.Import):
            for a in n.names:
                named.add((a.asname or a.name).split(".")[0])
    return named, stars


def module_level_names(tree):
    names = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
    return names


class ClassInfo:
    def __init__(self, node, path, imports, stars):
        self.node = node
        self.name = node.name
        self.path = path
        self.imports = imports
        self.stars = stars
        self.bases = [ast.unparse(b) for b in node.bases]
        self.methods = [n for n in node.body
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        self.method_names = [m.name for m in self.methods]


def collect(root):
    classes, modules = [], {}
    for path in iter_py_files(root):
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except SyntaxError as e:
            print("SKIP (syntax error):", rel, e, file=sys.stderr)
            continue
        named, stars = module_imports(tree)
        modname = rel[:-3].replace("/", ".")
        modules[modname] = module_level_names(tree)
        for n in tree.body:
            if isinstance(n, ast.ClassDef):
                classes.append(ClassInfo(n, rel, named, stars))
    return classes, modules


# ----------------------------------------------------------------------------
# Метрики окремого класу
# ----------------------------------------------------------------------------
def used_names(node):
    ids = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            ids.add(n.id)
    return ids


def self_attr_use(method):
    """Атрибути self.X, до яких звертається метод, та self.метод() виклики."""
    attrs, calls = set(), set()
    first = method.args.args[0].arg if method.args.args else None
    if first not in ("self", "cls"):
        return attrs, calls
    for n in ast.walk(method):
        if (isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
                and n.value.id == first):
            attrs.add(n.attr)
    return attrs, calls


class _DisjointSet:
    def __init__(self, items):
        self.parent = {i: i for i in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        self.parent[self.find(a)] = self.find(b)

    def count(self):
        return len({self.find(i) for i in self.parent})


def _link_methods(ms, attrs, ds):
    """З'єднує методи, що спільно використовують self.<поле> або викликають один одного."""
    names = {m.name for m in ms}
    for a in ms:
        for b in ms:
            if a.name < b.name and attrs[a.name] & attrs[b.name]:
                ds.union(a.name, b.name)
        for other in attrs[a.name] & (names - {a.name}):   # self.метод() = виклик
            ds.union(a.name, other)


def lcom4(ci):
    """LCOM4: кількість компонентів зв'язності графа методів + нормована форма
    (comps - 1) / (methods - 1), де 0 = ідеальна згуртованість, 1 = повна розрізненість."""
    ms = [m for m in ci.methods if not is_dunder(m.name) or m.name == "__init__"]
    if not ms:
        return 0, 0.0
    attrs = {m.name: self_attr_use(m)[0] for m in ms}
    ds = _DisjointSet([m.name for m in ms])
    _link_methods(ms, attrs, ds)
    comps = ds.count()
    norm = 0.0 if len(ms) <= 1 else (comps - 1) / (len(ms) - 1)
    return comps, round(norm, 2)


def dit(ci, by_name, seen=None):
    """DIT (Depth of Inheritance Tree). Клас без предків = 1 (неявний object).
    Зовнішній предок (db.Model, Exception) = +1 рівень (глибше він невідомий статично)."""
    seen = seen or set()
    if ci.name in seen:
        return 1
    seen = seen | {ci.name}
    if not ci.bases:
        return 1
    best = 1
    for b in ci.bases:
        short = b.split(".")[-1].split("[")[0]
        if short in by_name and "." not in b:
            best = max(best, 1 + dit(by_name[short], by_name, seen))
        else:
            best = max(best, 2)
    return best


def overridden(ci, by_name):
    """Кількість методів, що перевизначають метод проєктного предка (Lorenz-Kidd)."""
    names = set()

    def up(c, seen=()):
        for b in c.bases:
            short = b.split(".")[-1]
            if short in by_name and short not in seen:
                p = by_name[short]
                names.update(m for m in p.method_names if not is_dunder(m))
                up(p, seen + (short,))
    up(ci)
    return sum(1 for m in ci.method_names if m in names)


def _project_coupling(ci, ids, by_name):
    found = {n for n in ids if n in by_name and n != ci.name}
    for b in ci.bases:                                  # успадкування теж зачеплення
        short = b.split(".")[-1]
        if short in by_name and short != ci.name:
            found.add(short)
    return found


def _external_coupling(ci, ids, by_name, modules):
    star_syms = set()
    for mod in ci.stars:
        star_syms |= {x for x in modules.get(mod, set()) if x in ids and x not in by_name}
    named = {n for n in ids if n in ci.imports and n not in by_name}
    return named | star_syms


def compute_cbo(ci, by_name, modules):
    """CBO (Coupling Between Objects): проєктні класи + зовнішні імпортовані імена."""
    ids = used_names(ci.node)
    return (_project_coupling(ci, ids, by_name),
            _external_coupling(ci, ids, by_name, modules))


def compute_rfc(ci):
    """RFC (Response For a Class): власні методи + унікальні викликані функції."""
    calls = set()
    for m in ci.methods:
        calls |= {ast.unparse(n.func) for n in ast.walk(m) if isinstance(n, ast.Call)}
    return len(ci.methods) + len(calls)


def class_metrics(ci, by_name, modules):
    proj_cls, ext = compute_cbo(ci, by_name, modules)
    comps, lcom_norm = lcom4(ci)
    return {
        "class": ci.name,
        "file": ci.path,
        "bases": ci.bases,
        "methods": len(ci.methods),
        "WMC": sum(cyclomatic(m) for m in ci.methods),
        "CBO": len(proj_cls) + len(ext),
        "CBO_project_classes": sorted(proj_cls),
        "CBO_external": sorted(ext),
        "LCOM4": comps,
        "LCOM_norm": lcom_norm,
        "DIT": dit(ci, by_name),
        "RFC": compute_rfc(ci),
        "PIM": sum(1 for m in ci.method_names if not m.startswith("_")),
        "overridden": overridden(ci, by_name),
    }, proj_cls


# ----------------------------------------------------------------------------
# MOOD
# ----------------------------------------------------------------------------
def _class_level_attrs(ci):
    attrs = set()
    for n in ci.node.body:                              # поля класу (Column тощо)
        if isinstance(n, ast.Assign):
            attrs |= {t.id for t in n.targets if isinstance(t, ast.Name)}
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            attrs.add(n.target.id)
    return attrs


def _assign_targets(n):
    if isinstance(n, ast.Assign):
        return n.targets
    return [n.target]


def _self_assigned_attrs(method):
    first = method.args.args[0].arg if method.args.args else None
    if first not in ("self", "cls"):
        return set()
    attrs = set()
    for n in ast.walk(method):
        if not isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            continue
        for t in _assign_targets(n):
            if (isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name)
                    and t.value.id == first):
                attrs.add(t.attr)
    return attrs


def class_attributes(ci):
    attrs = _class_level_attrs(ci)
    for m in ci.methods:                                # self.x = ... у методах
        attrs |= _self_assigned_attrs(m)
    return {a for a in attrs if not is_dunder(a)}


def _visibility_counts(classes):
    """Повертає (методи всього, методи прихованих, атрибути всього, атрибути прихованих)."""
    tm = hm = ta = ha = 0
    for ci in classes:
        ms = [m for m in ci.method_names if not is_dunder(m)]
        at = class_attributes(ci)
        tm, ta = tm + len(ms), ta + len(at)
        hm += sum(1 for m in ms if m.startswith("_"))
        ha += sum(1 for a in at if a.startswith("_"))
    return tm, hm, ta, ha


def _pct(part, whole):
    return round(100.0 * part / whole, 2) if whole else 0.0


def mood(classes, coupling):
    """MOOD: MHF/AHF (Method/Attribute Hiding Factor), COF (Coupling Factor)."""
    n = len(classes)
    tm, hm, ta, ha = _visibility_counts(classes)
    pairs = sum(len(v) for v in coupling.values())
    cof = pairs / (n * n - n) if n > 1 else 0.0
    return {
        "classes": n,
        "MHF_percent": _pct(hm, tm),
        "AHF_percent": _pct(ha, ta),
        "COF_percent": round(100.0 * cof, 2),
        "methods_total": tm, "methods_hidden": hm,
        "attributes_total": ta, "attributes_hidden": ha,
        "coupled_pairs": pairs,
    }


# ----------------------------------------------------------------------------
def file_summary(rows):
    """Зведення по трьох файлах ЛР6 (Core Domain / Infrastructure / Utility-DTO)."""
    files = {}
    for role, path in ROLE_FILES.items():
        fr = [r for r in rows if r["file"] == path]
        if not fr:
            continue
        worst = max(fr, key=lambda r: r["CBO"])
        files[path] = {
            "role": role,
            "classes": len(fr),
            "WMC_sum": sum(r["WMC"] for r in fr),
            "CBO_max": worst["CBO"],
            "CBO_max_class": worst["class"],
            "LCOM_norm_max": max(r["LCOM_norm"] for r in fr),
            "DIT_max": max(r["DIT"] for r in fr),
        }
    return files


def analyse(root, label):
    classes, modules = collect(root)
    by_name = {c.name: c for c in classes}
    rows, coupling = [], {}
    for ci in classes:
        m, proj = class_metrics(ci, by_name, modules)
        rows.append(m)
        base_names = {b.split(".")[-1] for b in ci.bases}   # COF без успадкування
        coupling[ci.name] = {x for x in proj if x not in base_names}
    return {"label": label, "mood": mood(classes, coupling),
            "files": file_summary(rows), "classes": rows}


def print_report(result):
    hdr = "%-22s %-20s %4s %4s %4s %6s %5s %4s %4s %4s"
    print(hdr % ("class", "file", "met", "WMC", "CBO", "LCOM4", "LCOMn", "DIT", "RFC", "PIM"))
    for r in sorted(result["classes"], key=lambda r: -r["CBO"])[:15]:
        print(hdr % (r["class"][:22], r["file"][:20], r["methods"], r["WMC"], r["CBO"],
                     r["LCOM4"], r["LCOM_norm"], r["DIT"], r["RFC"], r["PIM"]))
    print("\nПо файлах ЛР6:")
    for path, v in result["files"].items():
        print(" ", path, json.dumps(v, ensure_ascii=False))
    print("\nMOOD:", json.dumps(result["mood"], ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("label", help="baseline | failed | fixed ...")
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="reports/lab8")
    args = ap.parse_args()

    result = analyse(args.root, args.label)
    os.makedirs(args.out, exist_ok=True)
    out = os.path.join(args.out, "ck_mood_%s.json" % args.label)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print_report(result)
    print("Збережено:", out)


if __name__ == "__main__":
    main()
