from flask import render_template

import base64
from io import BytesIO

import pandas as pd
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import matplotlib.style as mplstyle
from matplotlib.patches import Rectangle
from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})
mplstyle.use('ggplot')

import folium
import json




# receiving errors from errorhandler and render to user
def errorfeedback(name, code = 400, description = "no more description provided ..."):
    return render_template("error.html", name=name, code=code, description=description), code



def get_df():
    """load data into a dataframe object and wrangle it a bit"""
    df = pd.read_excel("ozimmig.xlsx", sheet_name="all_by_country_birth", header=None, index_col=0)
    df = df.T
    df.rename(
        columns={"Continent":"continent", "Region":"region", "Year":"country"},
        inplace=True)
    df.set_index('country', drop=True, inplace=True)

    # merging to coluns related to year 1959-60
    df["1959–60"] = df[['Jan-Jun 1959', '1959–60']].sum(axis=1).values
    df.drop(["Jan-Jun 1959"], axis=1, inplace=True)

    year_list = df.columns.tolist()[2:]

    # cast a numeric type to all digits (migration numbers)
    df[year_list] = df[year_list].apply(pd.to_numeric)

    df["sum"] = df[year_list].sum(axis=1)

    return df




def genchart(option, df):
    """ Generating graphs based on user selected options """

    if option == "timeline":
        year_list = df.columns[2:-1]

        # configuring canvas and plot area
        fig = Figure(figsize=(18, 10), dpi=100)
        canvas = FigureCanvasAgg(fig)
        ax = fig.subplots()

        # generating the basic line chart
        chart = ax.plot(df[year_list].sum().index, df[year_list].sum().values, 'k-o')

        # improving chart appearance
        ax.set_title(
            "Australia  Historical Migration [From 1945 to 2018]\n",
            {'fontsize': 18, "color":"k"}, loc='center')
        ax.set_ylabel("Number of Migrants\n", fontsize=16, color='k')
        ax.set_xlabel("Year", fontsize=16, color='k')
        ax.set_yticks(np.arange(0, 300000, 20000))
        ax.tick_params(axis='x', labelrotation=90)
        ax.tick_params(axis='both', labelsize=12, colors='k')

        # adding patches for each party-in-power period
        max_mig = df[year_list].sum(axis=0).max()
        min_mig = df[year_list].sum(axis=0).min()

        patch1 = Rectangle((0, min_mig), 2, max_mig-min_mig, color='red', alpha=.3)
        patch2 = Rectangle((2, min_mig), 24, max_mig-min_mig, color='blue', alpha=.3)
        patch3 = Rectangle((26, min_mig), 3, max_mig-min_mig, color='red', alpha=.3)
        patch4 = Rectangle((29, min_mig), 8, max_mig-min_mig, color='blue', alpha=.3)
        patch5 = Rectangle((37, min_mig), 13, max_mig-min_mig, color='red', alpha=.3)
        patch6 = Rectangle((50, min_mig), 11, max_mig-min_mig, color='blue', alpha=.3)
        patch7 = Rectangle((61, min_mig), 6, max_mig-min_mig, color='red', alpha=.3)
        patch8 = Rectangle((67, min_mig), 5, max_mig-min_mig, color='blue', alpha=.3)
        ax.add_patch(patch1)
        ax.add_patch(patch2)
        ax.add_patch(patch3)
        ax.add_patch(patch4)
        ax.add_patch(patch5)
        ax.add_patch(patch6)
        ax.add_patch(patch7)
        ax.add_patch(patch8)

        # adding the chart legend
        ax.legend(
            [patch1, patch2],
            ['Labor in Power', 'Liberal in Power'],
            loc='upper left',
            fontsize='x-large')

        # adding total number of migrants to the chart
        total = df['sum'].sum()
        ax.annotate(
            "Total Number of Migrants: {:,.0f}".format(total),
            (45, 15000),
            fontsize = 14,
            fontweight = 'bold')

        # Saving the chart in memory
        buf = BytesIO()
        fig.savefig(buf, format="png")
        infograph = base64.b64encode(buf.getbuffer()).decode("ascii")

    if option == "continent":

        # configuring canvas and plot area
        fig = Figure(figsize=(18, 10), dpi=100)
        canvas = FigureCanvasAgg(fig)
        ax = fig.subplots()

        # Generating the pie chart
        chart = ax.pie(
            df.groupby('continent').sum()['sum'].values,
            colors=["#999999", "#666666", "#e6e600", "#008080", "#808080"],
            explode=[.04,.04,0,0,.04],
            autopct="%1.1f%%",
            pctdistance = 1.1,
            wedgeprops  = dict(width=0.3, edgecolor='w'),
            textprops=dict(size=16, weight='bold'))

        # adding title to the chart
        ax.set_title("\nMigration per Continent \nAustralia [1945 - 2018]", fontsize=18, fontweight='bold')

        # adding legend to the chart
        leg_hand = []
        for continent in df.groupby('continent').sum().index:
            leg_hand.append("{}: {:,.0f}".format(continent, df.groupby('continent').sum().at[continent, 'sum']))
        ax.legend(leg_hand, loc='center', fontsize='xx-large')

        # Saving the chart in memory
        buf = BytesIO()
        fig.savefig(buf, format="png")
        infograph = base64.b64encode(buf.getbuffer()).decode("ascii")

    if option == "region":

        fig = Figure(figsize=(18, 10), dpi=100)
        canvas = FigureCanvasAgg(fig)
        ax = fig.subplots()

        # generate a horizontal barchart
        chart = ax.barh(
            df.groupby('region').sum().sort_values('sum', axis=0, ascending=False).index,
            df.groupby('region').sum().sort_values('sum', axis=0, ascending=False)['sum'],
            height=.5,
            color=["#008080", "#e6e600", 'k', 'k','k','k','k','k','k','k','k'],)

        # improving the chart appearance
        ax.set_title("Migrants per World Region; Australia [1945 - 2018]", fontsize=18)
        ax.set_xlabel("\nNumber of Migrants", fontsize=16, color="k")
        ax.set_ylabel("World Region", fontsize=16, color='k')
        ax.set_xticks(np.arange(0, 3500000, 250000))
        ax.tick_params(axis='both', labelsize=12, colors='k')

        # adding percent for each bar
        for bar in chart.patches:
            ax.text(1.01 * bar.get_width(), bar.get_y() + .3 * bar.get_height(), \
            '{:.1%}'.format(bar.get_width() / df['sum'].sum()), dict(fontsize=15, fontweight='bold'))

        # Saving the chart in memory
        buf = BytesIO()
        fig.savefig(buf, format="png")
        infograph = base64.b64encode(buf.getbuffer()).decode("ascii")

    if option == "topten":

        fig = Figure(figsize=(18, 10), dpi=100)
        canvas = FigureCanvasAgg(fig)
        ax = fig.subplots()

        chart = ax.barh(
            df['sum'].sort_values(ascending=False).head(10).index,
            df['sum'].sort_values(ascending=False).head(10).values,
            height=.5,
            color=["#008080", "#e6e600", 'k', 'k','k','k','k','k','k','k'],)

        # improving chart appearance
        ax.set_title("Top 10 Countries; Migration to Australia [1945 - 2018]\n", dict(fontsize=16))
        ax.set_xlabel("\nNumber of Migrants", fontsize=16, color='k')
        ax.set_ylabel("Top 10 Countries", fontsize=16, color='k')
        ax.set_xticks(np.arange(0, 2750000, 250000))
        ax.tick_params(axis='both', labelsize=14, colors='k')

        # adding bar chart percent
        for bar in chart.patches:
            ax.text(1.01 * bar.get_width(), bar.get_y() + 0.3 * bar.get_height(), \
            "{:.1%}".format(bar.get_width() / df['sum'].sum()), dict(fontsize=16, fontweight='bold', color='k'))

        # Saving the chart in memory
        buf = BytesIO()
        fig.savefig(buf, format="png")
        infograph = base64.b64encode(buf.getbuffer()).decode("ascii")

    if option == "Asia" or option == 'Europe' or option == "Africa" or option == "America":

        fig = Figure(figsize=(18, 8), dpi=100)
        canvas = FigureCanvasAgg(fig)
        ax = fig.subplots()

        chart = ax.barh(
            df[df['continent'] == option]["sum"].sort_values(ascending=False).head(5).index,
            df[df['continent'] == option]["sum"].sort_values(ascending=False).head(5).values,
            height=.3,
            color=["#b30000", "k", 'k', 'k','k'],)

        # improving chart appearance
        ax.set_title("Top Five Countries in {}; Migration to Australia [1945 - 2018]\n".format(option), dict(fontsize=18))
        ax.set_xlabel("\nNumber of Migrants", fontsize=16, color='k')
        ax.set_ylabel("Top Five Countries\n", fontsize=16, color='k')

        MAX = df[df['continent'] == option]["sum"].sort_values(ascending=False).head(5).values.max()
        ax.set_xticks(np.arange(0, MAX + MAX/10, int(str(int(MAX))[0]) * (10 ** len(str(int(MAX/10))) / 10)))

        ax.tick_params(axis='both', labelsize=14, colors='k')

        # adding bar chart percent
        for bar in chart.patches:
            ax.text(1.01 * bar.get_width(), bar.get_y() + 0.3 * bar.get_height(), \
            "{:.1%}".format(bar.get_width() / df['sum'].sum()), dict(fontsize=16, fontweight='bold', color='k'))

        # Saving the chart in memory
        buf = BytesIO()
        fig.savefig(buf, format="png")
        infograph = base64.b64encode(buf.getbuffer()).decode("ascii")

    if option == "map":
        """ generating a leaflet map using folium library"""

        # loading geojson overlay
        with open ("world.json") as data:
            wjson = json.load(data)

        year_list = df.columns[2:-1]
        # creating dataframe required to used during parsing geojson overlay
        map_df=df[year_list].sum(axis=1).to_frame().reset_index()
        # just for more readable legend on the map
        map_df[0] = map_df[0] / 1000000

        MigMap = folium.Map(location=[30, 10], zoom_start=1.5, tiles='OpenStreetMap')

        folium.Choropleth(
            geo_data=wjson,
            name='choropleth',
            data=map_df,
            columns=['country', 0],
            key_on='feature.properties.name',
            fill_color='YlOrRd',
            fill_opacity=0.8,
            line_opacity=0.2,
            nan_fill_color='white',
            nan_fill_opacity=0.3,
            legend_name='Migration to Australia from 1945 to 2018 (million)',
            bins=[0, 0.15, 0.3, 0.5, 1, 2.5]
        ).add_to(MigMap)

        return MigMap._repr_html_()
        #return MigMap._repr_html_() #it does the same as above line of code

    return f"data:image/png;base64,{infograph}"


def country_chart(nation1, nation2, df):
    """ generates and/or compare historical line chart for each country """

    fig = Figure(figsize=(18, 10), dpi=100)
    canvas = FigureCanvasAgg(fig)
    ax1 = fig.subplots()

    year_list = df.columns[2:-1]

    if nation1:
        line1 = ax1.plot(
            df.loc[nation1, year_list].index,
            df.loc[nation1, year_list].values,
            '-o',
            color='#660000',
            label="{} : {:,.0f}".format(nation1, df.loc[nation1, 'sum']),)
        lines = line1
        title = nation1

    if nation2:
        ax2 = ax1.twinx()
        line2 = ax2.plot(
            df.loc[nation2, year_list].index,
            df.loc[nation2, year_list].values,
            '--o',
            color='#006666',
            label="{} : {:,.0f}".format(nation2, df.loc[nation2, 'sum']),)
        ax2.set_ylabel("\nNumber of Migrants - {}".format(nation2), dict(color='#006666', fontsize=16))
        ax2.tick_params(axis='y', labelsize=14, colors='#006666')
        lines = line2
        title = nation2

    if nation1 and nation2:
        title = nation1 + " Compared to " + nation2
        lines = line1 + line2

    ax1.set_title("{}\nHistorical Migration to Australia [1945 - 2018]".format(title), dict(fontsize=18))
    ax1.set_xlabel("Year", dict(color='k', fontsize=16))
    ax1.set_ylabel("Number of Migrants - {}\n".format(nation1), dict(color='#660000', fontsize=16))
    ax1.tick_params(axis='x', labelrotation=90, labelsize=13, colors='k')
    ax1.tick_params(axis='y', labelsize=14, colors='#660000')

    labels = [line.get_label() for line in lines]
    ax1.legend(lines, labels, loc='upper left', fontsize=18)

    # Saving the chart in memory
    buf = BytesIO()
    fig.savefig(buf, format="png")
    infograph = base64.b64encode(buf.getbuffer()).decode("ascii")

    return f"data:image/png;base64,{infograph}"


def hist(df):
    """ generates and returns a histogram """

    fig = Figure(figsize=(8, 6), dpi=100)
    canvas = FigureCanvasAgg(fig)
    ax = fig.subplots()

    year_list = df.columns[2:-1]
    ax.hist(df[year_list].sum(axis=0).values, 25, color="#0d3300", edgecolor="white")

    ax.set_title("Histogram for All Migrants Each Year\n", dict(size=12, color='black'))
    ax.set_xlabel("\nNumber of Migrants", dict(size=12, color='black'))
    ax.set_ylabel("Frequency\n", dict(size=12, color='black'))
    ax.tick_params(axis='both', labelsize=10, colors='black')

    # Saving the chart in memory
    buf = BytesIO()
    fig.savefig(buf, format="png")
    infograph = base64.b64encode(buf.getbuffer()).decode("ascii")

    return f"data:image/png;base64,{infograph}"
