# ================================================================
# Convertisseur Markdown -> LaTeX -> PDF pour les rapports de ce
# module. Volontairement simple (pas de dépendance externe type
# pandoc, absente de cet environnement) : gère seulement les
# constructions utilisées dans nos .md (titres #/##/###, gras,
# italique, listes à puces/numérotées, tableaux |...|, code
# `inline`, séparateurs ---). Produit un PDF via tectonic (déjà
# utilisé et validé dans ce projet).
# ================================================================

import re
import shutil
import subprocess
import sys
from pathlib import Path

SPECIAL_CHARS = {
    "×": r"$\times$", "µ": r"$\mu$", "→": r"$\rightarrow$",
    "±": r"$\pm$", "≈": r"$\approx$", "≤": r"$\le$", "≥": r"$\ge$",
    "−": "$-$", "–": "--", "—": "---", "…": "...",
    "’": "'", "‑": "-", "œ": r"\oe{}", "Œ": r"\OE{}",
    "«": r"\guillemotleft{}", "»": r"\guillemotright{}",
    "§": r"\S{}", "⁻": r"$^{-}$", "⁺": r"$^{+}$",
    "⁰": r"$^{0}$", "¹": r"$^{1}$", "²": r"$^{2}$", "³": r"$^{3}$",
    "⁴": r"$^{4}$", "⁵": r"$^{5}$", "⁶": r"$^{6}$", "⁷": r"$^{7}$",
    "⁸": r"$^{8}$", "⁹": r"$^{9}$",
}

LATEX_ESCAPE = {
    "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
    "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def escape_latex(text):
    # Protège d'abord les backslashes introduits par nos propres
    # remplacements (\times, \mu, ...) en les traitant à part.
    out = []
    i = 0
    while i < len(text):
        matched = False
        for symbol, replacement in SPECIAL_CHARS.items():
            if text.startswith(symbol, i):
                out.append(replacement)
                i += len(symbol)
                matched = True
                break
        if matched:
            continue
        ch = text[i]
        out.append(LATEX_ESCAPE.get(ch, ch))
        i += 1
    return "".join(out)


def _escape_latex_breakable_code(text):
    """Comme escape_latex, mais insère \\allowbreak après chaque
    underscore/point échappé : un identifiant Python long
    (ex. select_b5_haenel_rff_then_mac_decision) dans un \\texttt{}
    ne peut normalement jamais être coupé en fin de ligne (pas
    d'espace), ce qui produit un débordement hors marge. \\allowbreak
    autorise LaTeX à couper à ces endroits si nécessaire, sans jamais
    forcer une coupure si la ligne a la place."""
    escaped = escape_latex(text)
    return escaped.replace(r"\_", r"\_\allowbreak{}").replace(
        ".", r".\allowbreak{}"
    )


def _render_code_spans(text):
    """Convertit les `code` inline restants et échappe le reste pour
    LaTeX. Utilisé à la fois au niveau supérieur d'une ligne et à
    l'intérieur d'un span gras/italique (un `code` peut apparaître
    à l'intérieur d'un **gras**, ex: "**voir `x.py`**")."""
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            out.append(
                r"\texttt{" + _escape_latex_breakable_code(part[1:-1]) + "}"
            )
        else:
            out.append(escape_latex(part))
    return "".join(out)


_INLINE_PATTERN = re.compile(r"`[^`]+`|\*\*(.+?)\*\*|\*([^*]+)\*")


def inline_markdown(text):
    """Gère `code`, **gras**, *italique* en une seule passe (positions
    non chevauchantes), de sorte qu'un `code` imbriqué dans un **gras**
    ne casse pas la détection du gras (bug historique : découper
    d'abord sur les backticks séparait le marqueur ** ouvrant de son
    fermant quand un `code` s'intercalait entre les deux)."""

    out = []
    pos = 0
    for m in _INLINE_PATTERN.finditer(text):
        out.append(_render_code_spans(text[pos:m.start()]))
        full = m.group(0)
        if full.startswith("**"):
            out.append(r"\textbf{" + _render_code_spans(m.group(1)) + "}")
        elif full.startswith("`"):
            out.append(
                r"\texttt{"
                + _escape_latex_breakable_code(full[1:-1])
                + "}"
            )
        else:
            out.append(r"\textit{" + _render_code_spans(m.group(2)) + "}")
        pos = m.end()
    out.append(_render_code_spans(text[pos:]))
    return "".join(out)


def convert_table(lines):
    """Convertit un bloc de tableau markdown (lignes consécutives
    commençant par |) en tabular LaTeX simple."""

    rows = []
    for line in lines:
        line = line.strip()
        if re.match(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?$", line):
            continue  # ligne de séparation ---|---
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)

    if not rows:
        return ""

    n_cols = len(rows[0])
    col_spec = "l" * n_cols

    table_body = ["\\begin{tabular}{" + col_spec + "}", "\\hline"]
    for row in rows:
        cells = [inline_markdown(c) for c in row]
        table_body.append(" & ".join(cells) + r" \\")
        table_body.append("\\hline")
    table_body.append("\\end{tabular}")
    tabular_src = "\n".join(table_body)

    # Ne réduit que si le tableau dépasse la largeur de page (certaines
    # lignes contiennent des tuples/décimales longs) ; sinon garde la
    # taille naturelle plutôt que de l'étirer artificiellement.
    out = [
        "\\begin{center}",
        r"\fittable{%",
        tabular_src,
        "}",
        "\\end{center}",
    ]
    return "\n".join(out)


IMAGE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)$")


def _is_block_starter(stripped):
    """Une ligne qui commence un nouveau bloc (donc qui ne doit
    jamais être fusionnée avec la ligne précédente en tant que
    simple continuation de paragraphe/item enroulé)."""
    if stripped == "":
        return True
    if stripped == "---":
        return True
    if stripped.startswith("|"):
        return True
    if re.match(r"^#{1,4}\s+", stripped):
        return True
    if re.match(r"^[-*]\s+", stripped):
        return True
    if re.match(r"^\d+\.\s+", stripped):
        return True
    if IMAGE_RE.match(stripped):
        return True
    return False


def markdown_to_latex_body(md_text):
    """Les fichiers source enroulent les paragraphes (et parfois les
    items de liste) sur plusieurs lignes brutes sans ligne vide entre
    elles (retour à la ligne "manuel" à ~80 colonnes). Un markdown
    **gras** ou *italique* peut donc avoir son marqueur ouvrant et
    fermant sur deux lignes brutes différentes. On fusionne d'abord
    les lignes de continuation (texte simple ne commençant pas un
    nouveau bloc) avec la ligne précédente avant toute conversion."""

    image_paths = []

    raw_lines = md_text.split("\n")
    lines = []
    for raw in raw_lines:
        stripped = raw.strip()
        # Ne fusionne que sur un entrée précédente non vide : sinon
        # une ligne blanche (marqueur de coupure de paragraphe) se
        # ferait absorber la ligne suivante au lieu de rester une
        # vraie coupure (bug trouvé : "**Q : ...**" fusionné sur la
        # ligne vide précédente au lieu de démarrer un paragraphe).
        if lines and lines[-1] != "" and not _is_block_starter(stripped):
            lines[-1] = lines[-1] + " " + stripped
        else:
            lines.append(stripped)

    out = []
    i = 0
    in_itemize = False
    in_enumerate = False

    def close_lists():
        nonlocal in_itemize, in_enumerate
        if in_itemize:
            out.append("\\end{itemize}")
            in_itemize = False
        if in_enumerate:
            out.append("\\end{enumerate}")
            in_enumerate = False

    while i < len(lines):
        stripped = lines[i]

        if stripped == "":
            close_lists()
            out.append("")
            i += 1
            continue

        if stripped == "---":
            close_lists()
            out.append("\\bigskip\\hrule\\bigskip")
            i += 1
            continue

        image_match = IMAGE_RE.match(stripped)
        if image_match:
            close_lists()
            alt_text = image_match.group(1).strip()
            src_path = image_match.group(2).strip()
            image_paths.append(src_path)
            basename = Path(src_path).name
            out.append("\\begin{figure}[h]")
            out.append("\\centering")
            out.append(
                f"\\includegraphics[width=\\linewidth]{{{basename}}}"
            )
            if alt_text:
                out.append(f"\\caption{{{inline_markdown(alt_text)}}}")
            out.append("\\end{figure}")
            i += 1
            continue

        # Tableau : bloc de lignes commençant par |
        if stripped.startswith("|"):
            close_lists()
            table_lines = []
            while i < len(lines) and lines[i].startswith("|"):
                table_lines.append(lines[i])
                i += 1
            out.append(convert_table(table_lines))
            continue

        heading_match = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if heading_match:
            close_lists()
            level = len(heading_match.group(1))
            title = inline_markdown(heading_match.group(2))
            cmd = {1: "section", 2: "subsection",
                   3: "subsubsection", 4: "paragraph"}[level]
            out.append(f"\\{cmd}{{{title}}}")
            i += 1
            continue

        bullet_match = re.match(r"^[-*]\s+(.*)$", stripped)
        if bullet_match:
            if in_enumerate:
                out.append("\\end{enumerate}")
                in_enumerate = False
            if not in_itemize:
                out.append("\\begin{itemize}")
                in_itemize = True
            out.append("\\item " + inline_markdown(bullet_match.group(1)))
            i += 1
            continue

        numbered_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if numbered_match:
            if in_itemize:
                out.append("\\end{itemize}")
                in_itemize = False
            if not in_enumerate:
                out.append("\\begin{enumerate}")
                in_enumerate = True
            out.append("\\item " + inline_markdown(numbered_match.group(1)))
            i += 1
            continue

        close_lists()
        out.append(inline_markdown(stripped))
        i += 1

    close_lists()
    return "\n".join(out), image_paths


LATEX_TEMPLATE = r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[french]{babel}
\usepackage{lmodern}
\usepackage{geometry}
\usepackage{amsmath,amssymb}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{longtable}
\usepackage{graphicx}
\geometry{margin=2.2cm}
\setlength{\parindent}{0pt}
\setlength{\parskip}{5pt}
\hypersetup{colorlinks=true,linkcolor=black,urlcolor=blue}
\newsavebox{\fittablebox}
\newcommand{\fittable}[1]{%
  \sbox{\fittablebox}{#1}%
  \ifdim\wd\fittablebox>\textwidth
    \resizebox{\textwidth}{!}{\usebox{\fittablebox}}%
  \else
    \usebox{\fittablebox}%
  \fi
}
\title{__TITLE__}
\author{}
\date{}
\setcounter{secnumdepth}{-1}
\begin{document}
\maketitle
__BODY__
\end{document}
"""


def convert_file(md_path, pdf_dir, title=None):

    md_path = Path(md_path)
    # Résolu en absolu : évite un bug où un pdf_dir relatif, combiné
    # au cwd=pdf_dir passé à tectonic plus bas, ferait chercher le
    # .tex à un chemin doublé (ex. "a/b/a/b/x.tex" au lieu de
    # "a/b/x.tex") -- tectonic échouait alors silencieusement en
    # laissant un ancien PDF périmé passer le test d'existence.
    pdf_dir = Path(pdf_dir).resolve()
    text = md_path.read_text(encoding="utf-8")

    if title is None:
        first_line = text.split("\n", 1)[0]
        title = re.sub(r"^#+\s*", "", first_line).strip()
        title = escape_latex(title)

    # Retire le titre H1 du corps s'il est identique (déjà mis en \title).
    body_text = text
    lines = text.split("\n")
    if lines and lines[0].startswith("# "):
        body_text = "\n".join(lines[1:])

    body, image_paths = markdown_to_latex_body(body_text)

    for src in image_paths:
        src_path = Path(src)
        if not src_path.is_absolute():
            src_path = Path.cwd() / src_path
        dst_path = pdf_dir / Path(src).name
        if src_path.exists():
            shutil.copy2(src_path, dst_path)
        else:
            print(f"IMAGE MANQUANTE, ignorée : {src_path}")

    latex_source = LATEX_TEMPLATE.replace("__TITLE__", title).replace(
        "__BODY__", body
    )

    tex_path = pdf_dir / (md_path.stem + ".tex")
    tex_path.write_text(latex_source, encoding="utf-8")

    result = subprocess.run(
        ["tectonic", tex_path.name],
        cwd=str(pdf_dir),
        capture_output=True,
        text=True,
    )

    pdf_path = pdf_dir / (md_path.stem + ".pdf")

    return pdf_path, result


if __name__ == "__main__":

    pdf_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "/tmp/haenel_pdfs"
    )
    pdf_dir.mkdir(parents=True, exist_ok=True)

    files_to_convert = [
        "docs/haenel/Compte_Rendu_Final_Haenel_vs_P0.md",
        "results/haenel_comparison/p0_decision_explanation.md",
        "docs/haenel/EXPLICATION_SIMPLE_POUR_PARFAIT.md",
        "docs/haenel/HAENEL_COMPARISON_README.md",
    ]

    for filename in files_to_convert:
        path = Path(filename)
        if not path.exists():
            print(f"MANQUANT, ignoré : {path}")
            continue

        pdf_path, result = convert_file(path, pdf_dir)

        # Vérifie le code retour de tectonic, pas seulement la
        # présence du PDF : un ancien PDF périmé passerait sinon un
        # simple test d'existence même si cette compilation a échoué.
        if result.returncode == 0 and pdf_path.exists():
            print(f"OK  : {path} -> {pdf_path}")
        else:
            print(f"ECHEC : {path}")
            print(result.stdout[-2000:])
            print(result.stderr[-2000:])
