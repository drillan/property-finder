import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

base_dir = Path(__file__).parent / "data"
data_dir = base_dir / "raw_data"

df = pd.concat([pd.read_parquet(file) for file in data_dir.glob("*.parquet")])
str_cols = [
    "PriceCategory",
    "Type",
    "Region",
    "MunicipalityCode",
    "Prefecture",
    "Municipality",
    "DistrictName",
    "FloorPlan",
    "LandShape",
    "Use",
    "Purpose",
    "Direction",
    "Classification",
    "CityPlanning",
    "Renovation",
    "Remarks",
]
normalize_cols = [
    "FloorPlan",
    "Structure",
]
float_cols = [
    "TradePrice",
    "PricePerUnit",
    "Area",
    "UnitPrice",
    "Frontage",
    "TotalFloorArea",
    "BuildingYear",
    "Breadth",
    "CoverageRatio",
    "FloorAreaRatio",
]
date_cols = [
    "Period",
]


def cast_ser(col_name: str):
    if col_name in float_cols:
        return (
            df.loc[:, col_name]
            .replace("戦前", np.nan)
            .replace(" ", np.nan)
            .replace("", np.nan)
            .str.replace("年", "")
            .astype(float)
        )
    if col_name in date_cols:
        return (
            df.loc[:, col_name]
            .str.replace("年第", "Q")
            .str.replace("四半期", "")
            .apply(lambda x: pd.Period(x, freq="Q").end_time)
        )
    if col_name in normalize_cols:
        return df.loc[:, col_name].map(lambda x: unicodedata.normalize("NFKC", x))
    if col_name in str_cols:
        return df.loc[:, col_name]


pd.concat([cast_ser(col) for col in df.columns], axis=1).to_parquet(base_dir / "data.parquet")
