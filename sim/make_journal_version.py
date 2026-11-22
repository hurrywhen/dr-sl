#!/usr/bin/env python3
"""Regenerate the IEEE journal version from latex/main.tex.

The journal version is a formatting conversion of the authoritative main paper
(documentclass/author/keywords/appendices), not a separate content draft.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src = (ROOT / "latex" / "main.tex").read_text(encoding="utf-8")

src = src.replace("\\documentclass[11pt,a4paper]{article}", "\\documentclass[journal]{IEEEtran}")
src = src.replace("\\usepackage[margin=2.4cm]{geometry}\n", "")
src = src.replace("\\usepackage{float}\n", "")

author = r"""\author{Wen~Hu, Ya~Yu, and Xutong~Wang
\thanks{W. Hu is with the College of Electronic and Information Engineering, Nanjing University of Aeronautics and Astronautics, Nanjing, China, and with Jiangsu Yunhefeng Intelligent Technology Co., Ltd., Jiangsu, China (e-mail: huwen@nuaa.edu.cn). Y. Yu and X. Wang are with the College of Electronic and Information Engineering, Nanjing University of Aeronautics and Astronautics, Nanjing, China (e-mail: 15949116139@163.com; wsgxt@outlook.com). Corresponding author: Y. Yu.}
\thanks{A condensed conference version uses author order Y. Yu, W. Hu, X. Wang; the difference is disclosed in the submission declarations. Code and synthetic artifacts are public at \url{https://github.com/hurrywhen/dr-sl} and \url{https://gitee.com/jiangsu-yunhefeng-intelligent_0/dr-sl}.}
\thanks{This revision uses fully synthetic data and co-author scoring of synthetic artifacts; a holdout human-utility packet is prepared but not collected. Funding, ethics-review status, and venue-specific declarations must be finalized by the authors before submission.}}
\markboth{Manuscript under review}{Hu \MakeLowercase{\textit{et al.}}: Auditing Local Release Gates for Cloud-Local LLM Inference}
"""
src = re.sub(r"\\author\{.*?\\date\{\}\n", lambda m: author, src, flags=re.S)

# Convert the in-abstract keywords line to an IEEEkeywords environment.
m = re.search(r"\\medskip\s*\n\\noindent\\textbf\{Keywords:\}\s*(.*?)\n\\end\{abstract\}", src, flags=re.S)
if m:
    kw = m.group(1).strip()
    src = src[:m.start()] + "\\end{abstract}\n\\begin{IEEEkeywords}\n" + kw + "\n\\end{IEEEkeywords}" + src[m.end():]

# IEEEtran uses \appendices for multiple appendices.
src = src.replace("\\appendix\n", "\\appendices\n")

# Wide tables (7 columns with CIs) must span both IEEE columns.  The result
# tables live in the \input'd revision_results.tex, so copy and convert it too.
def widen_tables(text):
    blocks = re.split(r"(\\begin\{table\}\[!t\].*?\\end\{table\})", text, flags=re.S)
    for i, b in enumerate(blocks):
        if b.startswith("\\begin{table}") and "\\label{tab:neural}" in b:
            blocks[i] = b.replace("\\begin{table}[!t]", "\\begin{table*}[!t]", 1) \
                         .replace("\\end{table}", "\\end{table*}", 1)
    return "".join(blocks)


src = widen_tables(src)
tables = (ROOT / "latex" / "revision_results.tex").read_text(encoding="utf-8")
(ROOT / "submission_journal" / "revision_results.tex").write_text(
    widen_tables(tables), encoding="utf-8")

(ROOT / "submission_journal" / "main.tex").write_text(src, encoding="utf-8")
print("regenerated submission_journal/main.tex from latex/main.tex")
