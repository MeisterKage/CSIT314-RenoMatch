"""Generated test data: 100+ rows per main entity, activity over the last 90 days."""

import random
from datetime import timedelta

import click
from faker import Faker
from sqlalchemy import MetaData
from werkzeug.security import generate_password_hash

from app.entity import (
    AuditLogEntity,
    CategoryEntity,
    CompanyInfoEntity,
    EnquiryEntity,
    EnquiryMessageEntity,
    FavouriteEntity,
    IDPEntity,
    IDPFlagEntity,
    LoginAttemptEntity,
    PlatformActivityEntity,
    ReviewEntity,
    UserAccountEntity,
    UserProfileEntity,
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
SUSPENDED_IDP_COUNT = 16  # 4% of IDPs
UPHELD_FLAG_COUNT = 16  # each removes its IDP: 4% of IDPs
DISMISSED_FLAG_COUNT = 34
FEATURED_IDP_COUNT = 6
FAVOURITE_COUNT = 1200
REMOVED_FAVOURITE_COUNT = 300  # shortlist activities = favourites + removed favourites
VIEW_ACTIVITY_COUNT = 8000
ENQUIRY_COUNT = 250
REVIEW_COUNT = 120
FLAG_COUNT = 120
AUDIT_LOG_COUNT = 200
LOGIN_ATTEMPT_COUNT = 500
DAYS_OF_HISTORY = 90
IDP_PHOTO_POOL = [f"/static/img/idp/idp-{n:02d}.jpg" for n in range(1, 33)]

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

ALL_MODELS = [
    UserProfileEntity, UserAccountEntity, LoginAttemptEntity, CompanyInfoEntity,
    CategoryEntity, IDPEntity, FavouriteEntity, PlatformActivityEntity, EnquiryEntity,
    EnquiryMessageEntity, ReviewEntity, IDPFlagEntity, AuditLogEntity,
]


def seed_database(seed: int = 314) -> dict[str, int]:
    """Fill an empty database with generated data and return a row count per table."""
    if db.session.query(UserAccountEntity).first() is not None:
        raise RuntimeError("Database already has accounts; refusing to seed.")
    _Seeder(seed).run()
    return {model.__tablename__: db.session.query(model).count() for model in ALL_MODELS}


def register_seed_command(app) -> None:
    @app.cli.command("seed")
    @click.option("--reset", is_flag=True, help="Drop and recreate all tables first.")
    def seed_command(reset):
        """Fill the database with generated test data."""
        if reset:
            # Drop every table in the database, including ones no entity defines any more.
            existing = MetaData()
            existing.reflect(bind=db.engine)
            existing.drop_all(bind=db.engine)
            db.create_all()
        elif db.session.query(UserAccountEntity).first() is not None:
            click.echo("Database already seeded; use --reset to rebuild.")
            return
        for table, count in seed_database().items():
            click.echo(f"{table}: {count}")


class _Seeder:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        self.fake = Faker()
        self.fake.seed_instance(seed)
        self.now = utcnow()

    def past(self, days_max: int = DAYS_OF_HISTORY):
        """A timestamp within the last days_max days, weighted toward recent days."""
        return self.now - timedelta(days=self.rng.triangular(0, days_max, 0))

    def since(self, *starts):
        """Like past(), but no earlier than any of `starts` (a view can't precede its IDP)."""
        earliest = max(self.now - timedelta(days=DAYS_OF_HISTORY), *starts)
        span = (self.now - earliest).total_seconds()
        return self.now - timedelta(seconds=self.rng.triangular(0, span, 0))

    def activity(self, activityType, userId, idpId, timestamp) -> None:
        db.session.add(
            PlatformActivityEntity(
                activityType=activityType, userId=userId, idpId=idpId, timestamp=timestamp
            )
        )

    def run(self) -> None:
        profiles = self.profiles()
        accounts = self.accounts(profiles)
        designers, customers = accounts["designer"], accounts["customer"]
        self.companies(designers)
        idps = self.idps(designers, self.categories())
        self.flags(customers, idps, accounts["platform"])
        self.suspend_some(idps)
        active = [idp for idp in idps if idp.status == "Active"]
        self.feature(active)
        self.favourites_and_shortlists(customers, active)
        self.views(customers, active)
        self.reviews(self.enquiries(customers, designers, idps))
        self.audit_logs(accounts["admin"], designers + customers)
        self.login_attempts(designers + customers)
        db.session.commit()

    def profiles(self) -> dict[str, list[UserProfileEntity]]:
        by_role = {
            role: [
                UserProfileEntity(
                    name=name, roleType=role, description=f"Default {name} profile"
                )
            ]
            for role, name in DEFAULT_PROFILE_NAMES.items()
        }
        for i, tier in enumerate(PROFILE_TIERS):
            for role, label in DEFAULT_PROFILE_NAMES.items():
                by_role[role].append(
                    UserProfileEntity(
                        name=f"{tier} {label}",
                        roleType=role,
                        description=f"{tier} tier of {label} accounts",
                        status="Suspended" if i % 10 == 9 else "Active",
                    )
                )
        db.session.add_all(p for group in by_role.values() for p in group)
        db.session.flush()
        return by_role

    def accounts(self, profiles) -> dict[str, list[UserAccountEntity]]:
        passwordHash = generate_password_hash(SEED_PASSWORD)
        by_role, n = {}, 0
        for role, count in ACCOUNT_COUNTS.items():
            created = []
            for i in range(count):
                n += 1
                if i == 0:
                    username, profile = DEMO_USERNAMES[role], profiles[role][0]
                else:
                    base = "".join(c for c in self.fake.user_name() if c.isalnum() or c == "_")
                    username = f"{base[:20]}{n}"  # matches the username rule
                    if self.rng.random() < 0.8:
                        profile = profiles[role][0]
                    else:
                        profile = self.rng.choice(profiles[role][1:])
                created.append(
                    UserAccountEntity(
                        username=username,
                        email=f"{username}@example.com",
                        passwordHash=passwordHash,
                        name=self.fake.name(),
                        phone=f"+65 {self.rng.randint(8000, 9999)} {self.rng.randint(1000, 9999)}",
                        profile=profile,
                        status="Suspended" if i > 0 and i % 25 == 0 else "Active",
                        weeklySummaryOptIn=not (role == "designer" and i % 10 == 5),
                        createdAt=self.past(DAYS_OF_HISTORY * 2),
                    )
                )
            by_role[role] = created
        db.session.add_all(a for group in by_role.values() for a in group)
        db.session.flush()
        for account in (a for group in by_role.values() for a in group):
            self.activity("register", account.userId, None, account.createdAt)
        return by_role

    def companies(self, designers) -> None:
        for designer in designers[:-DESIGNERS_WITHOUT_COMPANY]:
            db.session.add(
                CompanyInfoEntity(
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

    def categories(self) -> list[CategoryEntity]:
        categories = [
            CategoryEntity(
                name=f"{room} {theme}",
                description=f"{theme} projects for the {room.lower()}",
                status="Suspended" if i % 20 == 19 else "Active",
            )
            for i, (room, theme) in enumerate((r, t) for r in ROOMS for t in THEMES)
        ]
        db.session.add_all(categories)
        db.session.flush()
        return categories

    def idps(self, designers, categories) -> list[IDPEntity]:
        active = [c for c in categories if c.status == "Active"]
        idps = []
        for i in range(IDP_COUNT):
            style = self.rng.choice(STYLES)
            location = self.rng.choice(LOCATIONS)
            category = self.rng.choice(active)
            is_past = self.rng.random() < 0.7
            completedOn = None
            if is_past:
                completedOn = (self.now - timedelta(days=self.rng.randint(30, 1500))).date()
            photo_count = self.rng.randint(1, 3)
            idps.append(
                IDPEntity(
                    designer=designers[i % len(designers)],
                    category=category,
                    title=f"{style} {category.name} in {location}"[:120],
                    description=self.fake.paragraph(nb_sentences=5),
                    style=style,
                    propertyType=self.rng.choice(PROPERTY_TYPES),
                    budget=float(self.rng.randrange(15_000, 250_001, 1_000)),
                    location=location,
                    photoUrls=self.rng.sample(IDP_PHOTO_POOL, photo_count),
                    stage="Past" if is_past else "Current",
                    status="Active",
                    viewCount=0,
                    shortlistCount=0,
                    completedOn=completedOn,
                    createdAt=self.past(DAYS_OF_HISTORY * 2),
                )
            )
        db.session.add_all(idps)
        db.session.flush()
        for idp in idps:
            self.activity("idp_added", idp.designerId, idp.idpId, idp.createdAt)
        return idps

    def flags(self, customers, idps, managers) -> None:
        """Flags on distinct IDPs. An Upheld flag removes its IDP."""
        statuses = (
            ["Upheld"] * UPHELD_FLAG_COUNT
            + ["Dismissed"] * DISMISSED_FLAG_COUNT
            + ["Open"] * (FLAG_COUNT - UPHELD_FLAG_COUNT - DISMISSED_FLAG_COUNT)
        )
        self.rng.shuffle(statuses)
        for i, status in enumerate(statuses):
            idp = idps[(i * 3) % len(idps)]
            flag = IDPFlagEntity(
                idpId=idp.idpId,
                reporterId=self.rng.choice(customers).userId,
                reason=self.rng.choice(FLAG_REASONS),
                status=status,
                createdAt=self.past(),
            )
            if status != "Open":
                flag.reviewedBy = self.rng.choice(managers).userId
                flag.reviewedAt = self.now
                if status == "Upheld":
                    idp.status = "Removed"
            db.session.add(flag)

    def suspend_some(self, idps) -> None:
        active = [idp for idp in idps if idp.status == "Active"]
        for idp in self.rng.sample(active, SUSPENDED_IDP_COUNT):
            idp.status = "Suspended"

    def feature(self, active) -> None:
        for idp in self.rng.sample(active, FEATURED_IDP_COUNT):
            idp.isFeatured = True
            idp.featuredDate = (self.now - timedelta(days=self.rng.randint(0, 30))).date()

    def favourites_and_shortlists(self, customers, active) -> None:
        """Every save is a shortlist activity; some favourites were later removed."""
        pairs = set()
        while len(pairs) < FAVOURITE_COUNT + REMOVED_FAVOURITE_COUNT:
            pairs.add((self.rng.randrange(len(customers)), self.rng.randrange(len(active))))
        ordered = sorted(pairs)
        self.rng.shuffle(ordered)
        for n, (c, i) in enumerate(ordered):
            customer, idp = customers[c], active[i]
            savedAt = self.since(idp.createdAt, customer.createdAt)
            self.activity("shortlist", customer.userId, idp.idpId, savedAt)
            idp.shortlistCount += 1
            if n < FAVOURITE_COUNT:  # the rest were saved and later removed
                note = self.rng.choice(FAVOURITE_NOTES) if self.rng.random() < 0.4 else ""
                db.session.add(
                    FavouriteEntity(user=customer, idp=idp, note=note, savedAt=savedAt)
                )

    def views(self, customers, active) -> None:
        weights = [self.rng.paretovariate(1.5) for _ in active]  # a few IDPs are far more popular
        for idp in self.rng.choices(active, weights=weights, k=VIEW_ACTIVITY_COUNT):
            if self.rng.random() < 0.3:  # anonymous visitor
                self.activity("view", None, idp.idpId, self.since(idp.createdAt))
            else:
                viewer = self.rng.choice(customers)
                timestamp = self.since(idp.createdAt, viewer.createdAt)
                self.activity("view", viewer.userId, idp.idpId, timestamp)
            idp.viewCount += 1

    def enquiries(self, customers, designers, idps) -> list[tuple]:
        """Returns (customer, designer, reply time) for each enquiry the designer answered."""
        idps_by_designer = {}
        for idp in idps:
            idps_by_designer.setdefault(idp.designerId, []).append(idp)
        replied = []
        for i in range(ENQUIRY_COUNT):
            customer = customers[i % len(customers)]
            designer = designers[(i * 7) % len(designers)]
            idp = self.rng.choice(idps_by_designer[designer.userId])
            created = self.past()
            enquiry = EnquiryEntity(
                userId=customer.userId,
                designerId=designer.userId,
                idpId=idp.idpId,
                subject=f"Enquiry about {idp.title}",
                createdAt=created,
            )
            enquiry.messages.append(
                EnquiryMessageEntity(
                    senderId=customer.userId,
                    body=self.fake.paragraph(nb_sentences=3),
                    sentAt=created,
                )
            )
            if i % 5 != 0:  # four in five enquiries get a reply
                replied_at = min(created + timedelta(hours=self.rng.randint(1, 48)), self.now)
                enquiry.messages.append(
                    EnquiryMessageEntity(
                        senderId=designer.userId,
                        body=self.fake.paragraph(nb_sentences=3),
                        sentAt=replied_at,
                    )
                )
                replied.append((customer, designer, replied_at))
            db.session.add(enquiry)
            self.activity("enquiry", customer.userId, idp.idpId, created)
        return replied

    def reviews(self, replied) -> None:
        reviewed = set()
        for customer, designer, replied_at in replied:
            if len(reviewed) == REVIEW_COUNT:
                break
            if (customer.userId, designer.userId) in reviewed:
                continue  # one review per (designerId, userId)
            reviewed.add((customer.userId, designer.userId))
            createdAt = min(replied_at + timedelta(hours=self.rng.randint(1, 72)), self.now)
            db.session.add(
                ReviewEntity(
                    userId=customer.userId,
                    designerId=designer.userId,
                    rating=self.rng.choices([1, 2, 3, 4, 5], weights=[1, 1, 3, 6, 8])[0],
                    comment=self.fake.paragraph(nb_sentences=2),
                    createdAt=createdAt,
                )
            )
            self.activity("review", customer.userId, None, createdAt)

    def audit_logs(self, admins, targets) -> None:
        for _ in range(AUDIT_LOG_COUNT):
            target = self.rng.choice(targets)
            action = self.rng.choice(AUDIT_ACTIONS)
            is_profile = "profile" in action
            db.session.add(
                AuditLogEntity(
                    adminId=self.rng.choice(admins).userId,
                    action=action,
                    targetType="user_profile" if is_profile else "user_account",
                    targetId=target.profileId if is_profile else target.userId,
                    details=f"{action.replace('_', ' ')} via admin console",
                    timestamp=self.past(),
                )
            )

    def login_attempts(self, accounts) -> None:
        for _ in range(LOGIN_ATTEMPT_COUNT):
            account = self.rng.choice(accounts)
            db.session.add(
                LoginAttemptEntity(
                    username=account.username,
                    userId=account.userId,
                    success=self.rng.random() < 0.85,
                    attemptedAt=self.past(),
                )
            )
