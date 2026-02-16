"""
Configuration Module
Stores application-wide constants, such as colors and fonts.
"""


class AppColors:
    """
    Application color palette (Dark Theme).
    """

    BG_PRIMARY = "#121212"
    BG_SECONDARY = "#1E1E1E"
    BG_TERTIARY = "#2D2D2D"
    ACCENT = "#4285F4"
    SUCCESS = "#00A67C"
    DANGER = "#FF79B0"
    TEXT_PRIMARY = "#F1F1F1"
    TEXT_SECONDARY = "#AAAAAA"
    BORDER = "#333333"


class AppFonts:
    """
    Application font styles.
    """

    HEADER = ("Roboto", 24, "bold")
    METRIC_LARGE = ("Roboto", 28, "bold")
    METRIC_TITLE = ("Roboto", 10, "normal")
    STAT_VALUE = ("Roboto", 14, "bold")
    STAT_TITLE = ("Roboto", 9, "normal")
    NORMAL = ("Roboto", 10, "normal")
    SMALL = ("Roboto", 8, "normal")
