from flask import Flask, render_template, request
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import io
import pandas as pd
from matplotlib.cm import ScalarMappable

app = Flask(__name__)

# Read world countries data from geopandas
world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

# Filter to include only African countries
africa = world[world['continent'] == 'Africa']

# Read population data for African ethnocultural groups from population_data.txt text file
def read_population_data(file_path):
    ethnic_population_data = {}
    with open(file_path, 'r') as file:
        for line in file:
            country, ethnic_group, population = line.strip().split(',')
            if country not in ethnic_population_data:
                ethnic_population_data[country] = {}
            ethnic_population_data[country][ethnic_group] = int(population)
    
    # Get the list of unique ethnocultural groups
    ethnic_groups = set(ethnic_group for country_data in ethnic_population_data.values() 
                        for ethnic_group in country_data.keys())
    
    return ethnic_population_data, list(ethnic_groups)

# Provide the path to the text file containing population data
population_data_file = "population_data.txt"

# Read population data from text file
ethnic_population_data, ethnic_groups = read_population_data(population_data_file)

# Function to update map based on selected ethnocultural group
def update_map(selected_group):
    # Filter population data for the selected group
    group_data = {}
    for country, data in ethnic_population_data.items():
        if selected_group in data:
            group_data[country] = data[selected_group]

    # Merge population data with world data
    merged_data = africa.merge(pd.DataFrame.from_dict(group_data, orient='index', columns=['Population']),
                              how='left', left_on='name', right_index=True)

    # Plotting map of Africa
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.set_aspect('equal')

    merged_data.plot(ax=ax, column='Population', cmap='YlOrRd', legend=False,
                     missing_kwds={"color": "lightgrey"}, edgecolor='black')
    plt.title('Distribution of '+ selected_group + ' in Africa')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')

    # Colobar
    sm = ScalarMappable(norm=plt.Normalize(merged_data['Population'].min(), merged_data['Population'].max()), cmap='YlOrRd')
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax)  # Specifying the axes for the colorbar
    cbar.set_label('Population of ' + selected_group)

    # Colobar customization
    ticks = [merged_data['Population'].min(), (merged_data['Population'].min() + merged_data['Population'].max()) / 2, merged_data['Population'].max()]
    tick_labels = ['Low Population', 'Medium Population', 'High Population']
    cbar.set_ticks(ticks)
    cbar.set_ticklabels(tick_labels)

    # Save plot to a buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    return buffer

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        selected_group = request.form['ethnic_group']
        buffer = update_map(selected_group)
        return buffer.getvalue(), 200, {'Content-Type': 'image/png'}
    return render_template('index.html', ethnic_groups=ethnic_groups)

if __name__ == '__main__':
    app.run(debug=True)
