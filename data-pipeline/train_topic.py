import sys
from pathlib import Path

# Make backend importable
sys.path.append(str(Path(__file__).resolve().parents[1] / "backend"))

from app.db import SessionLocal
from app.models import Interaction
from app.topic_clustering import train_topic_model


def main():
    db = SessionLocal()

    try:
        interactions = db.query(Interaction).all()
        texts = [i.text for i in interactions]

        if len(texts) < 5:
            print("Not enough data to train topic model.")
            return

        print(f"Training topic model on {len(texts)} interactions...")

        train_topic_model(texts)

        print("Topic model trained successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    main()