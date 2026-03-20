try:  # optional dependency
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover
    pd = None

try:  # optional dependency
    from sklearn.cluster import KMeans  # type: ignore
except Exception:  # pragma: no cover
    KMeans = None
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Interaction


def segment_customers(db: Session, org_id: int):

    if pd is None or KMeans is None:
        return []

    rows = db.query(
        Interaction.customer_id,
        func.count(Interaction.id).label("interaction_count"),
        func.avg(Interaction.sentiment_compound).label("avg_sentiment")
    ).filter(Interaction.org_id == org_id).group_by(Interaction.customer_id).all()

    data = []

    for r in rows:
        data.append({
            "customer_id": r.customer_id,
            "interaction_count": r.interaction_count,
            "avg_sentiment": r.avg_sentiment
        })

    if len(data) < 3:
        return []

    df = pd.DataFrame(data)

    model = KMeans(n_clusters=3, random_state=42)

    df["cluster"] = model.fit_predict(
        df[["interaction_count", "avg_sentiment"]]
    )

    return df.to_dict(orient="records")
