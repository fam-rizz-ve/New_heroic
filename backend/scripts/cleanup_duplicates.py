#!/usr/bin/env python3
"""Remove duplicate games from the SQLite database.

Keeps only one game per (store, title) combination — the one with
the smallest primary key (first-imported copy). Prints the count
of duplicates removed.
"""

from __future__ import annotations

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.core.database import Base
from app.models.game import GameModel


def main() -> None:
    """Find and remove duplicate games, keeping the oldest copy per (store, title)."""
    engine = create_engine("sqlite:///./data/games.db", echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # Find all rows grouped by (store, title) having more than one entry
        dupes = session.execute(
            text(
                """
                SELECT store, title, COUNT(*) AS cnt
                FROM games
                GROUP BY store, title
                HAVING COUNT(*) > 1
                """
            )
        ).all()

        total_removed = 0
        for store, title, cnt in dupes:
            # Get all rows for this (store, title), ordered by rowid ascending
            rows = session.execute(
                select(GameModel)
                .where(GameModel.store == store, GameModel.title == title)
                .order_by(GameModel.id.asc())
            ).scalars().all()

            # Keep the first (lowest id / earliest inserted), delete the rest
            keep = rows[0]
            remove = rows[1:]
            for game in remove:
                session.delete(game)
                total_removed += 1

            print(
                f"  [{store}] \"{title}\": kept {keep.id}, "
                f"removed {len(remove)} duplicate(s)"
            )

        if total_removed > 0:
            session.commit()
            print(f"\nRemoved {total_removed} duplicate game(s) total.")
        else:
            print("No duplicates found.")

    # VACUUM to reclaim space
    with engine.connect() as conn:
        conn.execute(text("VACUUM"))

    print("Database vacuumed.")


if __name__ == "__main__":
    main()
