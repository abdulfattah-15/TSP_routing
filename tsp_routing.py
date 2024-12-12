import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# Title of the App
st.title('TSP ROUTING')

# Load DataFrame
df_cov_bandung = pd.read_parquet('cov_bandung.parquet')

# List for Route and Week Selection
# list_Route = df_cov_bandung['ROUTE'].unique()
list_Week = df_cov_bandung['WEEK'].unique()
list_Route = ['Senin','Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu']

# Route Selection
option_route = st.selectbox("Route:", list_Route, placeholder="Select Route...")
st.write("You selected Route:", option_route)

# Week Selection
option_week = st.selectbox("Week:", list_Week, placeholder="Select Week...")
st.write("You selected Week:", option_week)

# Filter DataFrame based on Route and Week
filtered_df = df_cov_bandung[
    (df_cov_bandung['ROUTE'] == option_route) &
    (df_cov_bandung['WEEK'] == option_week)
]

# Route ID Selection
list_route_id = filtered_df['ROUTE_ID'].unique()
option_id = st.selectbox("Route_ID:", list_route_id, placeholder="Select Route_ID...")
st.write("You selected Route_ID:", option_id)

# Further Filter DataFrame by Route_ID
filtered_df = filtered_df[filtered_df['ROUTE_ID'] == option_id]
filtered_df = filtered_df[filtered_df['LATITUDE'] != '0']
filtered_df= filtered_df[filtered_df['LONGITUDE'] != '0']
df = filtered_df[['OUTLET_NAME', 'LATITUDE', 'LONGITUDE', 'ROUTE_ID']]

# Display the filtered DataFrame
st.dataframe(df)

# Check if the DataFrame is empty
if df.empty:
    st.warning("No data available for the selected filters.")
else:
    # Run Script Button
    if st.button("Run the Script"):
        st.write("The script is running...")

        # Define the OSRM server URL
        # osrm_url = "http://localhost:5000/trip/v1/driving/"
        osrm_url = "http://10.206.24.14:30450/trip/v1/driving/"


        # Convert DataFrame coordinates to OSRM format
        coordinate_str = ";".join(
            f"{row['LONGITUDE']},{row['LATITUDE']}" for _, row in df.iterrows()
        )

        # Build the request URL
        url = osrm_url + coordinate_str

        # Query the OSRM server
        response = requests.get(
            url,
            params={"roundtrip": "true", "source": "first", "destination": "last", "geometries": "geojson"}
        )

        # Check response status
        if response.status_code == 200:
            try:
                # Extract route geometry (coordinates)
                trip_data = response.json()
                trip_coords = trip_data['trips'][0]['geometry']['coordinates']

                # Convert to (latitude, longitude) for Folium
                trip_coords = [(lat, lon) for lon, lat in trip_coords]

                # Create Folium Map
                m = folium.Map(location=[df.iloc[0]["LATITUDE"], df.iloc[0]["LONGITUDE"]], zoom_start=15)

                # Add the trip route to the map
                folium.PolyLine(trip_coords, color="blue", weight=5, opacity=0.8).add_to(m)

                # Add Markers
                for idx, row in df.iterrows():
                    folium.Marker(
                        [row["LATITUDE"], row["LONGITUDE"]],
                        popup=f"{row['OUTLET_NAME']}",
                        icon=folium.Icon(color="green")
                    ).add_to(m)

                # Render Map in Streamlit
                st_folium(m, width=725, returned_objects=[])
                # Extract total distance and duration
                total_distance = trip_data['trips'][0]['distance']  # Distance in meters
                total_duration = trip_data['trips'][0]['duration']  # Duration in seconds

                # Convert duration to hours, minutes, seconds
                hours, remainder = divmod(total_duration, 3600)
                minutes, seconds = divmod(remainder, 60)

                st.write(f"Total distance traveled: {total_distance / 1000:.2f} km")
                st.write(f"Total duration: {int(hours)}h {int(minutes)}m {int(seconds)}s")
            except Exception as e:
                st.error(f"Failed to process OSRM response: {e}")
        else:
            st.error(f"Error: {response.status_code}, {response.text}")
