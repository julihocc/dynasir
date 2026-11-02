"""
Formatting utilities for professional visualizations.

This module provides helper functions for creating publication-quality plots
with consistent styling, particularly for time series data visualization.
"""

from datetime import timedelta
from typing import Literal

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

TimeRange = Literal["auto", "short", "medium", "long"]


def format_time_axis(
    ax: plt.Axes,
    data_index: pd.DatetimeIndex,
    time_range: TimeRange = "auto",
    rotation: int = 45,
    labelsize: int = 10,
) -> plt.Axes:
    """Apply consistent time axis formatting to matplotlib axes.

    This function automatically formats the x-axis of time series plots based on
    the data's time span, ensuring appropriate date formatting and tick spacing
    for optimal readability.

    Args:
        ax: Matplotlib axes object to format
        data_index: DatetimeIndex from the data being plotted
        time_range: Time range category:
            - 'auto': Automatically detect based on data span (default)
            - 'short': Less than 2 months (day-level formatting)
            - 'medium': 2 months to 1 year (month-level formatting)
            - 'long': More than 1 year (multi-month formatting)
        rotation: Rotation angle for x-axis labels (degrees)
        labelsize: Font size for x-axis labels (points)

    Returns:
        plt.Axes: The formatted axes object (allows method chaining)

    Examples:
        >>> import matplotlib.pyplot as plt
        >>> import pandas as pd
        >>>
        >>> # Create sample time series
        >>> dates = pd.date_range('2020-01-01', periods=100, freq='D')
        >>> values = np.random.randn(100).cumsum()
        >>>
        >>> # Plot with automatic formatting
        >>> fig, ax = plt.subplots()
        >>> ax.plot(dates, values)
        >>> format_time_axis(ax, dates, time_range="auto")
        >>> plt.show()
        >>>
        >>> # Force specific formatting
        >>> fig, ax = plt.subplots()
        >>> ax.plot(dates, values)
        >>> format_time_axis(ax, dates, time_range="short", rotation=30)
        >>> plt.show()

    Notes:
        - Automatically adds grid for better readability
        - Sets appropriate margins to avoid date label cutoff
        - Uses minor ticks for finer granularity
        - Compatible with all matplotlib plotting functions

    See Also:
        format_subplot_grid: For formatting multiple subplots consistently
    """
    # Calculate time span
    time_span = data_index.max() - data_index.min()

    # Auto-detect time range if requested
    if time_range == "auto":
        if time_span <= timedelta(days=60):
            time_range = "short"
        elif time_span <= timedelta(days=365):
            time_range = "medium"
        else:
            time_range = "long"

    # Apply formatting based on time range
    if time_range == "short":  # Less than 2 months
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
        ax.xaxis.set_minor_locator(mdates.DayLocator(interval=1))
    elif time_range == "medium":  # 2 months to 1 year
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=1))
    else:  # More than 1 year
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=3))

    # Apply common formatting
    ax.tick_params(axis="x", rotation=rotation, labelsize=labelsize)
    ax.margins(x=0.01)

    # Improve readability with grid
    ax.grid(True, alpha=0.3, linestyle="-", linewidth=0.8, which="major")
    ax.grid(True, alpha=0.15, linestyle=":", linewidth=0.5, which="minor")

    return ax


def format_subplot_grid(
    axes,
    data_index: pd.DatetimeIndex,
    time_range: TimeRange = "auto",
    rotation: int = 45,
    labelsize: int = 10,
    hide_inner_xlabels: bool = True,
) -> None:
    """Apply consistent formatting to a grid of subplot axes.

    Formats all axes in a subplot grid with consistent time axis formatting,
    optionally hiding x-axis labels on interior plots for cleaner appearance.

    Args:
        axes: Single axes, 1D array of axes, or 2D array of axes from plt.subplots()
        data_index: DatetimeIndex from the data being plotted
        time_range: Time range category ('auto', 'short', 'medium', 'long')
        rotation: Rotation angle for x-axis labels (degrees)
        labelsize: Font size for x-axis labels (points)
        hide_inner_xlabels: If True, hide x-axis labels on all but bottom row

    Examples:
        >>> fig, axes = plt.subplots(3, 2, figsize=(12, 10))
        >>> # Plot data on each subplot...
        >>> format_subplot_grid(axes, dates, time_range="medium")
        >>> plt.tight_layout()
        >>> plt.show()

    Notes:
        - Works with single axis, 1D, and 2D arrays of axes
        - Bottom row always shows x-axis labels
        - Maintains grid lines across all subplots for consistency
    """
    import numpy as np

    # Handle single axis
    if isinstance(axes, plt.Axes):
        format_time_axis(axes, data_index, time_range, rotation, labelsize)
        return

    # Convert to numpy array for consistent handling
    axes_array = np.atleast_1d(axes)

    # Flatten if 2D
    if axes_array.ndim == 2:
        rows, cols = axes_array.shape
        axes_flat = axes_array.flatten()
    else:
        rows = len(axes_array)
        cols = 1
        axes_flat = axes_array

    # Format all axes
    for idx, ax in enumerate(axes_flat):
        if ax is not None:
            format_time_axis(ax, data_index, time_range, rotation, labelsize)

            # Hide x-axis labels on non-bottom plots if requested
            if hide_inner_xlabels and idx < len(axes_flat) - cols:
                ax.tick_params(axis="x", labelbottom=False)


def add_forecast_highlight(
    ax: plt.Axes,
    forecast_start,
    forecast_end,
    color: str = "#FBD38D",
    alpha: float = 0.12,
    label: str = "Forecast Period",
    add_boundary_line: bool = True,
    boundary_color: str = "#ED8936",
    boundary_alpha: float = 0.9,
) -> plt.Axes:
    """Add highlighted region to indicate forecast period on a plot.

    Creates a shaded vertical region to visually distinguish forecasted data
    from historical data, with optional boundary line marking the transition.

    Args:
        ax: Matplotlib axes object
        forecast_start: Start date/time of forecast period
        forecast_end: End date/time of forecast period
        color: Fill color for highlighted region (hex or named color)
        alpha: Transparency of highlighted region (0.0 to 1.0)
        label: Label for the highlighted region (appears in legend)
        add_boundary_line: If True, adds vertical line at forecast start
        boundary_color: Color of the boundary line
        boundary_alpha: Transparency of the boundary line

    Returns:
        plt.Axes: The modified axes object

    Examples:
        >>> fig, ax = plt.subplots()
        >>> ax.plot(all_dates, all_values)
        >>> add_forecast_highlight(
        ...     ax,
        ...     forecast_start='2021-01-01',
        ...     forecast_end='2021-01-30'
        ... )
        >>> plt.legend()
        >>> plt.show()

    Notes:
        - Shaded region is added at lowest z-order to not obscure data
        - Boundary line is optional but recommended for clarity
        - Label will appear in legend if ax.legend() is called
    """
    # Add shaded forecast period
    ax.axvspan(
        forecast_start,
        forecast_end,
        alpha=alpha,
        color=color,
        label=label,
        zorder=0,
    )

    # Add boundary line if requested
    if add_boundary_line:
        ax.axvline(
            x=forecast_start,
            color=boundary_color,
            linestyle="--",
            alpha=boundary_alpha,
            linewidth=2.5,
            label="Forecast Start",
            zorder=6,
        )

    return ax


def set_professional_style(
    figure_size: tuple = (12, 8),
    dpi: int = 100,
    font_size: int = 11,
) -> None:
    """Apply professional matplotlib style settings.

    Sets global matplotlib configuration for publication-quality figures with
    consistent styling across all plots in the session.

    Args:
        figure_size: Default figure size as (width, height) in inches
        dpi: Dots per inch for figure resolution
        font_size: Base font size in points (other elements scale accordingly)

    Examples:
        >>> set_professional_style(figure_size=(14, 10), font_size=12)
        >>> fig, ax = plt.subplots()  # Uses new default settings
        >>> ax.plot(data)
        >>> plt.show()

    Notes:
        - Call once at the beginning of your script/notebook
        - Settings persist for the entire session
        - Can be overridden for individual plots
        - Removes top and right spines for cleaner look
        - Enables grid by default
    """
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "figure.figsize": figure_size,
            "figure.dpi": dpi,
            "font.size": font_size,
            "font.family": "sans-serif",
            "axes.titlesize": font_size + 3,
            "axes.labelsize": font_size + 1,
            "axes.linewidth": 1.2,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.linewidth": 0.8,
            "grid.alpha": 0.3,
            "lines.linewidth": 2.5,
            "lines.markersize": 6,
            "xtick.labelsize": font_size - 1,
            "ytick.labelsize": font_size - 1,
            "legend.fontsize": font_size - 1,
            "legend.frameon": True,
            "legend.fancybox": True,
            "legend.shadow": True,
            "legend.framealpha": 0.9,
        }
    )
