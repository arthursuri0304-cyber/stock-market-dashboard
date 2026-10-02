# App Configuration
APP_NAME = "Wealth & Trading Dashboard"
DEBUG = False

# Default settings
DEFAULT_ANNUAL_RETURN = 7.0
DEFAULT_MONTHLY_INVESTMENT = 50.0

# Recommended allocation
DEFAULT_ALLOCATION = {
    "US Stocks (VOO/VTI)": 0.60,
    "International (VXUS)": 0.25,
    "Bonds (BND)": 0.15
}

# Trading signals thresholds
SIGNAL_BUY_THRESHOLD = 30
SIGNAL_SELL_THRESHOLD = -30
SIGNAL_HOLD_ZONE = (-30, 30)
