"""password_lab: a reproducible, local-only password-cracking experiment.

Everything in this package operates on *synthetic* passwords and hashes that
are generated inside the project. There are no network requests, no external
accounts, and no real or leaked credentials anywhere in the code or data.

The package answers one question with three small experiments:

    How much do two extra characters change password cracking difficulty,
    and how does the hashing algorithm affect the result?

See README.md for setup and the exact commands to reproduce the results.
"""

__version__ = "1.0.0"
