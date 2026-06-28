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
strings_df = pd.DataFrame({
    "string": [1, 2, 3, 4, 5, 6, 7, 8],
    "height_low_mm": [1.5, None, None, None, None, 2.0, 2.2, 2.4],
    "height_hi_mm": [1.7, None, None, None, None, 2.2, 2.4, 2.6]
}).set_index("string")

# Interpolate the mising values
strings_df = strings_df.interpolate(method="index")

# Perform unit conversions
strings_df["height_low_inch"] = strings_df["height_low_mm"] * MM_TO_INCH
strings_df["height_hi_inch"] = strings_df["height_hi_mm"] * MM_TO_INCH

strings_df["height_mm_avg"] = strings_df[["height_low_mm", "height_hi_mm"]].mean(axis=1)
strings_df["height_inch_avg"] = strings_df[["height_low_inch", "height_hi_inch"]].mean(axis=1)

# Rounding to available gauges
strings_df["nearest_mm"] = round_to_nearest_multiple_of(strings_df["height_mm_avg"], 0.25)
strings_df["nearest_inch"] = round_to_nearest_multiple_of(strings_df["height_inch_avg"], 0.01)

# Error calculation
eps = 1e-12

strings_df["error_mm_rel"] = (
        (strings_df["height_mm_avg"] - strings_df["nearest_mm"]).abs()
        / (strings_df["height_mm_avg"].abs() + eps)
)

strings_df["error_inch_rel"] = (
        (strings_df["height_inch_avg"] - strings_df["nearest_inch"]).abs()
        / (strings_df["height_inch_avg"].abs() + eps)
)

# Decision logic (vectorized)
use_inch = strings_df["error_inch_rel"] < strings_df["error_mm_rel"]

strings_df["gauge_to_be_used"] = np.where(use_inch, "INCH", "MM")
strings_df["final_height"] = np.where(use_inch, strings_df["nearest_inch"], strings_df["nearest_mm"])

strings_df["final_error_rel"] = np.minimum(strings_df["error_inch_rel"], strings_df["error_mm_rel"])
strings_df["final_error_pct"] = strings_df["final_error_rel"] * 100

print(strings_df)
