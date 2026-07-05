"""Shared text and state-tracking for the principles-reinforcement hooks.

Kept in one place so the Claude Code and Cursor variants (reinforce_principles.py,
reinforce_principles_cursor.py) can never drift into saying slightly
different things -- only their input/output JSON framing differs, since
that's dictated by each tool's own hook schema, not by anything worth
duplicating.
"""
from __future__ import annotations

from pathlib import Path

# This file lives at Scripts/harness/hooks/_reinforcement_common.py, three
# levels below the Harness root (unlike Scripts/harness/_index_common.py,
# which is only two levels down) -- parents[3] reaches the root here.
ROOT = Path(__file__).resolve().parents[3]
STATE_DIR = ROOT / "Index" / "session-state"
BIG_CHANGE_FILE_THRESHOLD = 5

CHECKLIST = (
    "[principios do harness] Antes de seguir: (1) algo equivalente ja existe "
    "(reuso > novo)? (2) este e o menor diff possivel para o que foi pedido? "
    "(3) isso vai precisar de teste (unit/integration/e2e)? (4) isso cruza "
    "limite de modulo, auth, dados ou migracao -- merece pre-change-impact-check "
    "antes de continuar?"
)

SESSION_START_REMINDER = (
    "Este workspace carrega principles/PRINCIPLES.md automaticamente e reforca "
    "um checklist antes de cada edicao de codigo via hook (nao depende so de "
    "voce lembrar). Para mudancas grandes ou que cruzam modulos, use a skill "
    "pre-change-impact-check antes de comecar a codar."
)

BIG_CHANGE_ESCALATION = (
    " Esta sessao ja tocou {count} arquivos diferentes -- isso comeca a "
    "parecer uma mudanca grande. Se ainda nao rodou a skill "
    "pre-change-impact-check para avaliar blast radius, considere rodar agora "
    "antes de continuar."
)


def track_touched_file(session_id: str, file_path: str) -> int:
    """Append file_path to this session's touched-file set, return distinct count."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    # session ids may contain characters unsafe for a bare filename (e.g. Cursor's
    # conversation_id could contain slashes in principle) -- keep this defensive
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_id) or "unknown"
    state_file = STATE_DIR / f"{safe_id}.txt"
    touched: set[str] = set()
    if state_file.exists():
        touched = set(state_file.read_text(encoding="utf-8").splitlines())
    touched.add(file_path)
    state_file.write_text("\n".join(sorted(touched)), encoding="utf-8")
    return len(touched)


def checklist_message(file_path: str, session_id: str) -> str:
    message = CHECKLIST
    if file_path:
        count = track_touched_file(session_id, file_path)
        if count >= BIG_CHANGE_FILE_THRESHOLD:
            message += BIG_CHANGE_ESCALATION.format(count=count)
    return message
