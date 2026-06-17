"""
models.py — SQLAlchemy ORM models.
Three tables: issues, issue_genres, reading_progress.
"""

from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, Integer, ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Issue(Base):
    __tablename__ = "issues"

    id              = Column(Integer, primary_key=True, autoincrement=True)

    # Core identity
    series          = Column(Text, nullable=False)          # <Series> — grouping key
    volume          = Column(Integer, nullable=True)
    number          = Column(Text, nullable=True)           # "1", "Annual", "½", or NULL for singles
    title           = Column(Text, nullable=True)           # same as series in this collection
    year            = Column(Integer, nullable=True)
    month           = Column(Integer, nullable=True)

    # Publishing
    publisher       = Column(Text, nullable=True)
    format          = Column(Text, nullable=True)           # "One Shot", "Annual", "TPB", etc.
    format_group    = Column(Text, nullable=True)           # "Series" or "Singles" — from folder path

    # Content
    summary         = Column(Text, nullable=True)
    story_arc       = Column(Text, nullable=True)
    story_arc_number = Column(Integer, nullable=True)       # position within arc

    # Credits — raw CSV strings, never split (except genres)
    writer          = Column(Text, nullable=True)
    penciller       = Column(Text, nullable=True)
    inker           = Column(Text, nullable=True)
    colorist        = Column(Text, nullable=True)
    letterer        = Column(Text, nullable=True)
    cover_artist    = Column(Text, nullable=True)

    # Extra metadata — raw CSV
    characters      = Column(Text, nullable=True)
    teams           = Column(Text, nullable=True)
    locations       = Column(Text, nullable=True)

    # Flags
    age_rating      = Column(Text, nullable=True)
    language        = Column(Text, nullable=True)
    black_and_white = Column(Boolean, default=False, nullable=False)
    manga           = Column(Text, default="No", nullable=False)  # "No"/"Yes"/"YesAndRightToLeft"

    # Counts
    page_count      = Column(Integer, nullable=True)        # from XML; verified vs actual image count
    count           = Column(Integer, nullable=True)        # total issues in series if known

    # File tracking
    file_path       = Column(Text, nullable=False, unique=True)
    cover_path      = Column(Text, nullable=True)           # path to generated thumbnail
    metadata_source = Column(Text, nullable=True)           # "xml" or "filename"
    missing         = Column(Boolean, default=False, nullable=False)

    # Timestamps
    date_added      = Column(DateTime, default=datetime.utcnow, nullable=False)
    date_modified   = Column(DateTime, nullable=True)       # filesystem mtime at last scan

    # Relationships
    genres          = relationship("IssueGenre", back_populates="issue",
                                   cascade="all, delete-orphan")
    progress        = relationship("ReadingProgress", back_populates="issue",
                                   uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Issue id={self.id} series={self.series!r} number={self.number!r}>"


class IssueGenre(Base):
    __tablename__ = "issue_genres"
    __table_args__ = (
        UniqueConstraint("issue_id", "genre_name", name="uq_issue_genre"),
    )

    issue_id    = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"),
                         primary_key=True)
    genre_name  = Column(Text, primary_key=True)

    issue = relationship("Issue", back_populates="genres")

    def __repr__(self):
        return f"<IssueGenre issue_id={self.issue_id} genre={self.genre_name!r}>"


class ReadingProgress(Base):
    __tablename__ = "reading_progress"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    issue_id     = Column(Integer, ForeignKey("issues.id", ondelete="CASCADE"),
                          unique=True, nullable=False)
    status       = Column(Text, default="unread", nullable=False)  # "unread"/"reading"/"read"
    current_page = Column(Integer, default=0, nullable=False)       # 0-indexed
    last_read_at = Column(DateTime, nullable=True)

    issue = relationship("Issue", back_populates="progress")

    def __repr__(self):
        return (f"<ReadingProgress issue_id={self.issue_id} "
                f"status={self.status!r} page={self.current_page}>")
