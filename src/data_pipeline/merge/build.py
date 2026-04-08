import logging
from pathlib import Path
from ingestion import DataIngestion
from builder import DatasetBuilder

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BASE_DIR = Path(__file__).resolve().parents[3]
OUTPUT = Path("raw/csv_full_post.csv")
YEARS = list(range(2020, 2026))


def main():
    logging.info("Initialisation")
    ing = DataIngestion(base_dir=BASE_DIR)
    builder = DatasetBuilder(ing)

    logging.info("Construction du dataset")
    df = builder.build(years=YEARS)

    logging.info("Distribution du label y :\n%s", df["y"].value_counts().to_string())
    logging.info("Distribution 2025 :\n%s", df[df["annee"] == 2025]["y"].value_counts().to_string())

    builder.save(OUTPUT)


if __name__ == "__main__":
    main()