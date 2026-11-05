#!/usr/bin/env python3
"""Složí index.html: vloží data/data8.json do src/template.html."""
t = open("src/template.html", encoding="utf-8").read()
assert t.count("/*DATA*/") == 1
open("index.html", "w", encoding="utf-8").write(t.replace("/*DATA*/", open("data/data8.json", encoding="utf-8").read()))
print("index.html hotovo")
