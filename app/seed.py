"""Generated test data: 100+ rows per main entity, events over the last 90 days."""

import random
from datetime import timedelta
from html import escape

import click
from faker import Faker
from werkzeug.security import generate_password_hash

from app.entity import (
    IDP,
    AuditLog,
    Category,
    CompanyInfo,
    Enquiry,
    EnquiryMessage,
    Favourite,
    IDPFlag,
    IDPPhoto,
    LoginAttempt,
    Review,
    ShortlistEvent,
    UserAccount,
    UserProfile,
    ViewEvent,
    db,
)
from app.entity.db import utcnow
from app.entity.idp import PROPERTY_TYPES, STYLES
from app.entity.user_profile import DEFAULT_PROFILE_NAMES

SEED_PASSWORD = "Password123!"
DEMO_USERNAMES = {
    "admin": "admin",
    "platform": "manager",
    "designer": "designer",
    "customer": "customer",
}
ACCOUNT_COUNTS = {"admin": 5, "platform": 5, "designer": 120, "customer": 300}
DESIGNERS_WITHOUT_COMPANY = 10
IDP_COUNT = 400
FAVOURITE_COUNT = 1200
REMOVED_FAVOURITE_COUNT = 300
VIEW_EVENT_COUNT = 8000
ENQUIRY_COUNT = 250
REVIEW_COUNT = 120
FLAG_COUNT = 120
AUDIT_LOG_COUNT = 200
LOGIN_ATTEMPT_COUNT = 500
DAYS_OF_HISTORY = 90

PROFILE_TIERS = [
    "Trial", "Standard", "Premium", "Enterprise", "Senior", "Junior", "Associate", "Lead",
    "Regional North", "Regional South", "Regional East", "Regional West", "Central",
    "Corporate", "Student", "Partner", "Verified", "Featured", "Legacy", "Pilot", "Seasonal",
    "VIP", "Support", "Contract",
]
ROOMS = [
    "Living Room", "Kitchen", "Bedroom", "Bathroom", "Study", "Dining Room", "Balcony",
    "Whole Unit", "Office", "Retail",
]
THEMES = [
    "Full Renovation", "Refresh", "Remodel", "Storage Solutions", "Lighting", "Carpentry",
    "Flooring", "Smart Home", "Eco-Friendly", "Space Saving",
]
LOCATIONS = [
    "Ang Mo Kio", "Bedok", "Bishan", "Bukit Batok", "Bukit Merah", "Bukit Timah", "Clementi",
    "Hougang", "Jurong East", "Jurong West", "Kallang", "Marine Parade", "Pasir Ris",
    "Punggol", "Queenstown", "Sengkang", "Serangoon", "Tampines", "Toa Payoh", "Woodlands",
    "Yishun", "Novena", "Orchard", "Tiong Bahru",
]
COMPANY_SUFFIXES = ["Interiors", "Design Studio", "Living", "Spaces"]
FAVOURITE_NOTES = [
    "Love the kitchen layout", "Similar size to our flat", "Check budget with designer",
    "Good storage ideas", "Show to my partner", "Like the colour palette",
]
FLAG_REASONS = [
    "Photos appear to be copied from another designer",
    "Contains contact details in the description",
    "Inappropriate image",
    "Misleading budget information",
    "Duplicate listing",
]
AUDIT_ACTIONS = [
    "create_account", "update_account", "suspend_account", "reactivate_account",
    "create_profile", "update_profile", "suspend_profile", "reactivate_profile",
]
PHOTO_COLOURS = [
    "#8d6e63", "#a1887f", "#90a4ae", "#b0bec5", "#c5e1a5",
    "#ffe082", "#ffab91", "#80cbc4", "#ce93d8", "#9fa8da",
]

ALL_MODELS = [
    UserProfile, UserAccount, LoginAttempt, CompanyInfo, Category, IDP, IDPPhoto, Favourite,
    ShortlistEvent, ViewEvent, Enquiry, EnquiryMessage, Review, IDPFlag, AuditLog,
]


def seed_database(seed: int = 314) -> dict[str, int]:
    """Fill an empty database with generated data and return a row count per table."""
    if db.session.query(UserAccount).first() is not None:
        raise RuntimeError("Database already has accounts; refusing to seed.")
    _Seeder(seed).run()
    return {model.__tablename__: db.session.query(model).count() for model in ALL_MODELS}


def register_seed_command(app) -> None:
    @app.cli.command("seed")
    @click.option("--reset", is_flag=True, help="Drop and recreate all tables first.")
    def seed_command(reset):
        """Fill the database with generated test data."""
        if reset:
            db.drop_all()
            db.create_all()
        elif db.session.query(UserAccount).first() is not None:
            click.echo("Database already seeded; use --reset to rebuild.")
            return
        for table, count in seed_database().items():
            click.echo(f"{table}: {count}")


def _placeholder_svg(colour: str, label: str) -> bytes:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">'
        f'<rect width="800" height="600" fill="{colour}"/>'
        '<text x="400" y="310" font-family="sans-serif" font-size="40" fill="#ffffff" '
        f'text-anchor="middle">{escape(label)}</text></svg>'
    ).encode()


class _Seeder:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        self.fake = Faker()
        self.fake.seed_instance(seed)
        self.now = utcnow()

    def past(self, days_max: int = DAYS_OF_HISTORY):
        """A timestamp within the last days_max days, weighted toward recent days."""
        return self.now - timedelta(days=self.rng.triangular(0, days_max, 0))

    def run(self) -> None:
        profiles = self.profiles()
        accounts = self.accounts(profiles)
        designers, customers = accounts["designer"], accounts["customer"]
        self.companies(designers)
        idps = self.idps(designers, self.categories())
        self.photos(idps)
        visible = [idp for idp in idps if not idp.is_archived]
        self.favourites_and_shortlists(customers, visible)
        self.views(customers, visible)
        self.reviews(self.enquiries(customers, designers, idps))
        self.flags(customers, idps, accounts["platform"])
        self.audit_logs(accounts["admin"], designers + customers)
        self.login_attempts(designers + customers)
        db.session.commit()

    def profiles(self) -> dict[str, list[UserProfile]]:
        by_role = {
            role: [UserProfile(name=name, role_type=role, description=f"Default {name} profile")]
            for role, name in DEFAULT_PROFILE_NAMES.items()
        }
        for i, tier in enumerate(PROFILE_TIERS):
            for role, label in DEFAULT_PROFILE_NAMES.items():
                by_role[role].append(
                    UserProfile(
                        name=f"{tier} {label}",
                        role_type=role,
                        description=f"{tier} tier of {label} accounts",
                        is_suspended=(i % 10 == 9),
                    )
                )
        db.session.add_all(p for group in by_role.values() for p in group)
        db.session.flush()
        return by_role

    def accounts(self, profiles) -> dict[str, list[UserAccount]]:
        password_hash = generate_password_hash(SEED_PASSWORD)
        by_role, n = {}, 0
        for role, count in ACCOUNT_COUNTS.items():
            created = []
            for i in range(count):
                n += 1
                if i == 0:
                    username, profile = DEMO_USERNAMES[role], profiles[role][0]
                else:
                    base = "".join(c for c in self.fake.user_name() if c.isalnum() or c == "_")
                    username = f"{base[:20]}{n}"  # matches the US03 username rule
                    if self.rng.random() < 0.8:
                        profile = profiles[role][0]
                    else:
                        profile = self.rng.choice(profiles[role][1:])
                created.append(
                    UserAccount(
                        username=username,
                        email=f"{username}@example.com",
                        password_hash=password_hash,
                        full_name=self.fake.name(),
                        phone=f"+65 {self.rng.randint(8000, 9999)} {self.rng.randint(1000, 9999)}",
                        profile=profile,
                        is_suspended=(i > 0 and i % 25 == 0),
                        created_at=self.past(DAYS_OF_HISTORY * 2),
                    )
                )
            by_role[role] = created
        db.session.add_all(a for group in by_role.values() for a in group)
        db.session.flush()
        return by_role

    def companies(self, designers) -> None:
        for designer in designers[:-DESIGNERS_WITHOUT_COMPANY]:
            db.session.add(
                CompanyInfo(
                    designer=designer,
                    name=f"{self.fake.last_name()} {self.rng.choice(COMPANY_SUFFIXES)}",
                    description=self.fake.paragraph(nb_sentences=4),
                    address=(
                        f"{self.rng.randint(1, 999)} {self.rng.choice(LOCATIONS)} Road, "
                        f"Singapore {self.rng.randint(100000, 829999)}"
                    ),
                    phone=designer.phone,
                    email=f"hello@{designer.username}.example.com",
                    website=f"https://{designer.username}.example.com",
                )
            )

    def categories(self) -> list[Category]:
        categories = [
            Category(
                name=f"{room} {theme}",
                description=f"{theme} projects for the {room.lower()}",
                is_suspended=(i % 20 == 19),
            )
            for i, (room, theme) in enumerate((r, t) for r in ROOMS for t in THEMES)
        ]
        db.session.add_all(categories)
        db.session.flush()
        return categories

    def idps(self, designers, categories) -> list[IDP]:
        active = [c for c in categories if not c.is_suspended]
        idps = []
        for i in range(IDP_COUNT):
            style = self.rng.choice(STYLES)
            location = self.rng.choice(LOCATIONS)
            category = self.rng.choice(active)
            is_past = self.rng.random() < 0.7
            completed_on = None
            if is_past:
                completed_on = (self.now - timedelta(days=self.rng.randint(30, 1500))).date()
            idps.append(
                IDP(
                    designer=designers[i % len(designers)],
                    category=category,
                    title=f"{style} {category.name} in {location}"[:120],
                    description=self.fake.paragraph(nb_sentences=5),
                    style=style,
                    property_type=self.rng.choice(PROPERTY_TYPES),
                    budget=self.rng.randrange(15_000, 250_001, 1_000),
                    location=location,
                    status="past" if is_past else "current",
                    completed_on=completed_on,
                    is_featured=(i % 40 == 0),
                    is_archived=(i % 80 == 79),
                    created_at=self.past(DAYS_OF_HISTORY * 2),
                )
            )
        db.session.add_all(idps)
        db.session.flush()
        return idps

    def photos(self, idps) -> None:
        for idp in idps:
            for position in range(self.rng.randint(1, 3)):
                db.session.add(
                    IDPPhoto(
                        idp=idp,
                        content_type="image/svg+xml",
                        data=_placeholder_svg(
                            self.rng.choice(PHOTO_COLOURS), f"{idp.style} #{position + 1}"
                        ),
                        caption=f"{idp.style} {idp.property_type}, view {position + 1}",
                        position=position,
                    )
                )

    def favourites_and_shortlists(self, customers, visible) -> None:
        pairs = set()
        while len(pairs) < FAVOURITE_COUNT + REMOVED_FAVOURITE_COUNT:
            pairs.add((self.rng.randrange(len(customers)), self.rng.randrange(len(visible))))
        ordered = sorted(pairs)
        self.rng.shuffle(ordered)
        for n, (c, i) in enumerate(ordered):
            customer, idp = customers[c], visible[i]
            saved_at = self.past()
            db.session.add(
                ShortlistEvent(idp_id=idp.id, customer_id=customer.id, shortlisted_at=saved_at)
            )
            if n < FAVOURITE_COUNT:  # the rest were saved and later removed
                note = self.rng.choice(FAVOURITE_NOTES) if self.rng.random() < 0.4 else ""
                db.session.add(
                    Favourite(customer=customer, idp=idp, note=note, saved_at=saved_at)
                )

    def views(self, customers, visible) -> None:
        weights = [self.rng.paretovariate(1.5) for _ in visible]  # a few IDPs are far more popular
        for idp in self.rng.choices(visible, weights=weights, k=VIEW_EVENT_COUNT):
            viewer_id = None if self.rng.random() < 0.3 else self.rng.choice(customers).id
            db.session.add(ViewEvent(idp_id=idp.id, viewer_id=viewer_id, viewed_at=self.past()))

    def enquiries(self, customers, designers, idps) -> list[tuple[UserAccount, UserAccount]]:
        idps_by_designer = {}
        for idp in idps:
            idps_by_designer.setdefault(idp.designer_id, []).append(idp)
        replied = []
        for i in range(ENQUIRY_COUNT):
            customer = customers[i % len(customers)]
            designer = designers[(i * 7) % len(designers)]
            idp = self.rng.choice(idps_by_designer[designer.id])
            created = self.past()
            enquiry = Enquiry(
                customer_id=customer.id,
                designer_id=designer.id,
                idp_id=idp.id,
                subject=f"Enquiry about {idp.title}",
                created_at=created,
            )
            enquiry.messages.append(
                EnquiryMessage(
                    sender_id=customer.id,
                    body=self.fake.paragraph(nb_sentences=3),
                    sent_at=created,
                )
            )
            if i % 5 != 0:  # four in five enquiries get a reply
                enquiry.messages.append(
                    EnquiryMessage(
                        sender_id=designer.id,
                        body=self.fake.paragraph(nb_sentences=3),
                        sent_at=min(created + timedelta(hours=self.rng.randint(1, 48)), self.now),
                    )
                )
                replied.append((customer, designer))
            db.session.add(enquiry)
        return replied

    def reviews(self, replied_pairs) -> None:
        for customer, designer in replied_pairs[:REVIEW_COUNT]:
            db.session.add(
                Review(
                    customer_id=customer.id,
                    designer_id=designer.id,
                    rating=self.rng.choices([1, 2, 3, 4, 5], weights=[1, 1, 3, 6, 8])[0],
                    comment=self.fake.paragraph(nb_sentences=2),
                )
            )

    def flags(self, customers, idps, managers) -> None:
        statuses = ["open", "open", "dismissed", "upheld"]
        for i in range(FLAG_COUNT):
            idp = idps[(i * 3) % len(idps)]
            status = statuses[i % len(statuses)]
            flag = IDPFlag(
                idp_id=idp.id,
                reporter_id=self.rng.choice(customers).id,
                reason=self.rng.choice(FLAG_REASONS),
                status=status,
                created_at=self.past(),
            )
            if status != "open":
                flag.reviewed_by = self.rng.choice(managers).id
                flag.reviewed_at = self.now
                if status == "upheld":
                    idp.is_removed = True
            db.session.add(flag)

    def audit_logs(self, admins, targets) -> None:
        for _ in range(AUDIT_LOG_COUNT):
            target = self.rng.choice(targets)
            action = self.rng.choice(AUDIT_ACTIONS)
            is_profile = "profile" in action
            db.session.add(
                AuditLog(
                    actor_id=self.rng.choice(admins).id,
                    action=action,
                    target_type="user_profile" if is_profile else "user_account",
                    target_id=target.profile_id if is_profile else target.id,
                    details=f"{action.replace('_', ' ')} via admin console",
                    created_at=self.past(),
                )
            )

    def login_attempts(self, accounts) -> None:
        for _ in range(LOGIN_ATTEMPT_COUNT):
            account = self.rng.choice(accounts)
            db.session.add(
                LoginAttempt(
                    username=account.username,
                    account_id=account.id,
                    success=self.rng.random() < 0.85,
                    attempted_at=self.past(),
                )
            )
