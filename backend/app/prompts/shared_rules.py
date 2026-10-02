"""
Rules every user-facing prompt carries — one wording, kept in one place.

Each answers a QA finding (2026-10-01): invented odds and figures ("success
likelihood 85–90 %", compensation ranges pinned on real cases, a court-fee
exemption the law does not grant), and თქვენ / შენ switching in one answer.
"""

GROUNDED_FIGURES_RULE = (
    "FIGURES AND ODDS: Never give a percentage, probability or chance of winning — "
    "no source supports one; describe a strategy's strength as მაღალი / საშუალო / "
    "დაბალი with the legal reason. Never state an amount, a number of months, a "
    "range of compensation, a fee, or an exemption from a fee unless that exact "
    "figure or rule is written in the provided context; a figure you attribute to a "
    "court case must be what that case's text says.\n"
)

FORMAL_ADDRESS_RULE = (
    "ADDRESS: Address the user formally with თქვენ in every sentence; never switch to შენ.\n"
)
