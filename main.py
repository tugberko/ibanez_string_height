from numbers import Number
import numpy as np
import pandas as pd

pd.set_option("display.max_columns", 999)

MM_TO_INCH = 1 / 25.4
MAX_DECIMAL_PLACES = 4


def round_to_nearest_multiple_of(value: pd.Series | Number, step: Number) -> pd.Series | float:
    """
    Round value(s) to the nearest multiple of step.
    Works with scalars or pandas Series.
    """
    if step == 0:
        raise ValueError("step must be non-zero")

    return np.round(np.round(value / step) * step, MAX_DECIMAL_PLACES)


# This is what Ibanez tells us
df = pd.DataFrame({
    "string": [1, 2, 3, 4, 5, 6, 7, 8],
    "height_low_mm": [1.5, None, None, None, None, 2.0, 2.2, 2.4],
    "height_hi_mm": [1.7, None, None, None, None, 2.2, 2.4, 2.6]
}).set_index("string")


# Interpolate the mising values
df = df.interpolate(method="index")



# Perform unit conversions
df["height_low_inch"] = df["height_low_mm"] * MM_TO_INCH
df["height_hi_inch"] = df["height_hi_mm"] * MM_TO_INCH

df["height_mm_avg"] = df[["height_low_mm", "height_hi_mm"]].mean(axis=1)
df["height_inch_avg"] = df[["height_low_inch", "height_hi_inch"]].mean(axis=1)


# Rounding to available gauges
df["nearest_mm"] = round_to_nearest_multiple_of(df["height_mm_avg"], 0.25)
df["nearest_inch"] = round_to_nearest_multiple_of(df["height_inch_avg"], 0.01)


# Error calculation
eps = 1e-12

df["error_mm_rel"] = (
    (df["height_mm_avg"] - df["nearest_mm"]).abs()
    / (df["height_mm_avg"].abs() + eps)
)

df["error_inch_rel"] = (
    (df["height_inch_avg"] - df["nearest_inch"]).abs()
    / (df["height_inch_avg"].abs() + eps)
)

# ----------------------------
# Decision logic (vectorized)
# ----------------------------
use_inch = df["error_inch_rel"] < df["error_mm_rel"]

df["gauge_to_be_used"] = np.where(use_inch, "INCH", "MM")
df["final_height"] = np.where(use_inch, df["nearest_inch"], df["nearest_mm"])

df["final_error_rel"] = np.minimum(df["error_inch_rel"], df["error_mm_rel"])
df["final_error_pct"] = df["final_error_rel"] * 100

print(df)