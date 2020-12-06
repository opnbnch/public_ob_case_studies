import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from matplotlib.ticker import FormatStrFormatter


class PredExpViz:
    """
    This class manages visualizatiosn comparing experimental and predicted
    values for a given endpoint.
    """

    def __init__(self, df, xcol, ycol, hue_col=None):
        """
        :float_vec x: true values
        :float_vec y: predicted values
        """

        self.df = df
        self.xcol = xcol
        self.ycol = ycol
        self.hue_col = hue_col

        ### Assigning x and y columns
        self.x = df[xcol]
        self.y = df[ycol]


    def init_chart(self, figsize=12):
        """
        Establish seaborn settings.
        """

        self.figsize = figsize

        sns.set(rc={'figure.figsize': (figsize, figsize)})
        sns.set_style('whitegrid')
        sns.set_context('talk')

    def set_colorbar(self, cmap='coolwarm', cbar_label=None):

        self.cmap = cmap

        if cbar_label:
            self.cbar_label = cbar_label

    def plot_colorbar(self):
        """
        Include a colorbar.
        """
        if self.hue_col is not None:

            if self.df[self.hue_col].dtype == 'O':
                self.categorical_hue = True
                return 0
            else:
                points = plt.scatter(self.x, self.y,
                             c=self.df[self.hue_col], cmap=self.cmap)
                cbar = plt.colorbar(points)
        else:
            points = plt.scatter(self.x, self.y)

        if hasattr(self, 'cbar_label'):
            cbar.ax.get_yaxis().labelpad = 20
            cbar.ax.set_ylabel(self.cbar_label, rotation=270)

    def plot_scatter(self):

        if hasattr(self, 'categorical_hue'):
            self.ax = sns.scatterplot(self.xcol, self.ycol, data=self.df,
                                      hue = self.hue_col, s=200)
        else:
            self.ax = sns.regplot(self.xcol, self.ycol, data=self.df,
                                  fit_reg=False, scatter=False, color=".1")

        self.ax.set(xscale="log", yscale="log")

    def axis_manager(self):

        min_val = np.min([np.min(self.x), np.min(self.y)])
        max_val = np.max([np.max(self.x), np.max(self.y)])

        min_floor = np.floor(np.log10(min_val))
        max_ceil = np.ceil(np.log10(max_val))

        self.min_floor = min_floor
        self.max_ceil = max_ceil

        limits = [10**min_floor, 10**max_ceil]

        self.ax.set(xlim=limits, ylim=limits)

        tick_range = np.arange(min_floor+1, max_ceil+1)

        ticks = [10**t for t in tick_range]

        self.ax.set_yticks(ticks)
        self.ax.set_xticks(ticks)

        self.ax.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
        self.ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))

    def add_unity(self):

        # add the unity line
        linemin = 10**self.min_floor
        linemax = 10**self.max_ceil

        self.ax.plot([linemin, linemax], [linemin, linemax], color="black",
                     linewidth=2, linestyle="-")

    def add_nfold_error(self, n=3, col="#ebb810"):

        # add the unity line
        linemin = 10**self.min_floor
        linemax = 10**self.max_ceil

        self.ax.plot([linemin, linemax], [linemin*n, linemax*n],
                     color=col, linewidth=2, linestyle="--")
        self.ax.plot([linemin*n, linemax*n], [linemin, linemax],
                     color=col, linewidth=2, linestyle="--")

    def add_axis_labels(self, xlabel, ylabel):

        self.xlabel = xlabel
        self.ylabel = ylabel

        # define the axis labels
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)

    def add_title(self, title):

        self.title = title

        self.ax.set_title(title)

    def main(self):

        self.init_chart()
        if not hasattr(self, 'cmap'):
            self.set_colorbar()

        self.plot_colorbar()
        self.plot_scatter()
        self.axis_manager()

        return self
