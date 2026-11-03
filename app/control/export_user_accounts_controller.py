import csv
import io

from app.entity import UserAccountEntity

COLUMNS = ("User ID", "Name", "Email", "User profile", "Status", "Date created")
FORMULA_STARTS = ("=", "+", "-", "@", "\t", "\r")


class ExportUserAccountsController:
    """US-34: an administrator exports the accounts matching the current search filters."""

    def __init__(self):
        self.entity = UserAccountEntity

    def exportUserAccountsCSV(self, keyword: str, profile: str, status: str):
        """1.1: search (1.1.1). [accounts not empty] build the file (1.1.2) and return it.
        [3a. no accounts found] return None."""
        accounts = self.entity.searchUserAccounts(keyword, profile, status)
        if not accounts:
            return None
        return self.generateCSV(accounts)

    def generateCSV(self, accounts):
        """Private: the CSV text with one row per account. Passwords are never written. A
        text cell starting with a formula character gets a leading quote, so a spreadsheet
        does not run it."""
        out = io.StringIO(newline="")
        writer = csv.writer(out, lineterminator="\r\n")
        writer.writerow(COLUMNS)
        for account in accounts:
            writer.writerow(
                [
                    account.userId,
                    self.safeCell(account.name),
                    self.safeCell(account.email),
                    self.safeCell(account.profile.name),
                    account.status,
                    account.createdAt.strftime("%Y-%m-%d"),
                ]
            )
        return out.getvalue()

    @staticmethod
    def safeCell(value: str) -> str:
        return "'" + value if value.startswith(FORMULA_STARTS) else value
