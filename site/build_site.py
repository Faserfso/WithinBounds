#!/usr/bin/env python3
"""Собирает сайт-читалку из глав в ru/ в папку _site/ (нужен pandoc)."""
import html
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "_site")
PANDOC = os.environ.get("PANDOC", "pandoc")
SITE = os.path.join(ROOT, "site")


def meta():
    text = open(os.path.join(ROOT, "metadata.yaml"), encoding="utf-8").read()
    title = re.search(r"^title:\s*(.+)$", text, re.M).group(1).strip()
    subtitle = re.search(r"^subtitle:\s*(.+)$", text, re.M).group(1).strip()
    desc = re.search(r"^description:\s*\|\n((?:  .*\n?)+)", text, re.M)
    desc = " ".join(l.strip() for l in desc.group(1).splitlines()) if desc else ""
    return title, subtitle, desc


def chapters():
    files = sorted(f for f in os.listdir(os.path.join(ROOT, "ru")) if f.endswith(".md"))
    result = []
    for f in files:
        src = open(os.path.join(ROOT, "ru", f), encoding="utf-8").read()
        heading = re.match(r"#\s*(.+)", src).group(1).strip()
        num, name = re.match(r"(\d+)\.\s*(.+)", heading).groups()
        body_md = src.split("\n", 1)[1]
        stamp = ""
        m = re.match(r"\s*\*([^*\n]+)\*\s*\n", body_md)
        if m:
            stamp = m.group(1).strip()
            body_md = body_md[m.end():]
        body = subprocess.run([PANDOC, "-f", "markdown-smart", "-t", "html5"], input=body_md,
                              capture_output=True, text=True, check=True).stdout
        slug = f[:-3]
        result.append(dict(num=int(num), name=name, stamp=stamp, body=body, slug=slug,
                           words=len(re.findall(r"\w+", body_md))))
    return result


def page(title, body, book_title, desc, extra_head=""):
    tpl = open(os.path.join(SITE, "template.html"), encoding="utf-8").read()
    return (tpl.replace("{{title}}", html.escape(title))
               .replace("{{book}}", html.escape(book_title))
               .replace("{{desc}}", html.escape(desc))
               .replace("{{head}}", extra_head)
               .replace("{{body}}", body))


def main():
    title, subtitle, desc = meta()
    chs = chapters()
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copy(os.path.join(SITE, "style.css"), OUT)
    shutil.copy(os.path.join(SITE, "reader.js"), OUT)
    shutil.copy(os.path.join(ROOT, "assets", "cover.png"), OUT)
    os.makedirs(os.path.join(OUT, "files"))
    build = os.path.join(ROOT, "build")
    downloads = []
    for ext, label in (("epub", "EPUB"), ("fb2", "FB2"), ("docx", "DOCX")):
        p = os.path.join(build, f"v-predelah-dopuska.{ext}")
        if os.path.exists(p):
            shutil.copy(p, os.path.join(OUT, "files"))
            downloads.append(f'<a href="files/v-predelah-dopuska.{ext}" download>{label}</a>')

    total = sum(c["words"] for c in chs)
    toc = "\n".join(
        f'<li><a href="{c["slug"]}.html"><span class="n">{c["num"]}</span>'
        f'<span class="t">{html.escape(c["name"])}</span>'
        f'<span class="s">{html.escape(c["stamp"])}</span></a></li>' for c in chs)
    dl = f'<p class="downloads">Скачать: {" | ".join(downloads)}</p>' if downloads else ""
    index_body = f"""
<header class="hero">
  <img class="cover" src="cover.png" alt="Обложка: красное колесо задвижки на тёмном фоне">
  <div>
    <h1>{html.escape(title)}</h1>
    <p class="sub">{html.escape(subtitle)}. Within Bounds</p>
    <p class="desc">{html.escape(desc)}</p>
    <p class="meta">{len(chs)} глав, около {round(total / 1000)} тысяч слов, примерно {round(total / 200 / 60, 1):g} ч чтения</p>
    <p><a class="btn" id="continue" href="{chs[0]['slug']}.html">Начать читать</a></p>
    {dl}
  </div>
</header>
<nav class="toc" aria-label="Оглавление"><h2>Оглавление</h2><ol>{toc}</ol></nav>
"""
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(
        page(title, index_body, title, desc))

    for i, c in enumerate(chs):
        prev_l = (f'<a rel="prev" href="{chs[i-1]["slug"]}.html">Назад: {html.escape(chs[i-1]["name"])}</a>'
                  if i else '<a href="index.html">Оглавление</a>')
        next_l = (f'<a rel="next" href="{chs[i+1]["slug"]}.html">Дальше: {html.escape(chs[i+1]["name"])}</a>'
                  if i + 1 < len(chs) else '<a href="index.html">Оглавление</a>')
        body = f"""
<div class="progress" aria-hidden="true"><div id="bar"></div></div>
<div class="topbar">
  <a href="index.html" class="home">{html.escape(title)}</a>
  <div class="tools">
    <button id="listen" type="button" hidden>Слушать</button>
    <select id="voice" aria-label="Голос" hidden></select>
    <select id="rate" aria-label="Скорость" hidden><option value="0.85">0.85x</option><option value="1" selected>1x</option><option value="1.15">1.15x</option><option value="1.3">1.3x</option></select>
    <button id="font-" type="button" aria-label="Мельче">A-</button>
    <button id="font+" type="button" aria-label="Крупнее">A+</button>
    <button id="theme" type="button" aria-label="Тема">Тема</button>
  </div>
</div>
<article class="chapter" data-slug="{c['slug']}">
  <p class="num">Глава {c['num']}</p>
  <h1>{html.escape(c['name'])}</h1>
  {f'<p class="stamp">{html.escape(c["stamp"])}</p>' if c['stamp'] else ''}
  {c['body']}
</article>
<nav class="pager">{prev_l}{next_l}</nav>
"""
        open(os.path.join(OUT, c["slug"] + ".html"), "w", encoding="utf-8").write(
            page(f"{c['num']}. {c['name']} - {title}", body, title, desc))
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    print(f"site: {len(chs)} chapters -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())
