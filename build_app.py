#!/usr/bin/env python3
"""Složí dist/index.html: vloží data/data7.json do src/template.html."""
t = open("src/template.html", encoding="utf-8").read()
assert t.count("/*DATA*/") == 1
open("dist/index.html", "w", encoding="utf-8").write(t.replace("/*DATA*/", open("data/data7.json", encoding="utf-8").read()))
print("dist/index.html hotovo")
