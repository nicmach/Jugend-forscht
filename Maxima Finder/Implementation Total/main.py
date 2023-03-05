from folium.plugins import HeatMap
from maxima import *

import customtkinter
import pandas as pd
import numpy as np
import geopy.distance
import math
import folium
import webbrowser
import time



customtkinter.set_appearance_mode('dark')
customtkinter.set_default_color_theme('dark-blue')

root = customtkinter.CTk()
root.title('Positionsrechner')
root.geometry("1280x720")


relative_effectivity = customtkinter.IntVar()

def main_calculate(file_path, effective_range, grid_distance, crime_type, cctv_number, cctv_effectivity, avg_damage):

    data = pd.read_csv(file_path)

    # Time messurement
    start_time = time.time()
    crime_matrix_test, long_diff, lat_diff, lat_min, long_min, long_max, lat_max = create_crime_type_matrix(data, distance=grid_distance, crimeType=crime_type)
    print(crime_matrix_test.shape)
    crime_matrix_test_final_crime, crime_matrix_test_cctv = cctv_placement(crime_matrix_test, cctv_number, grid_distance, effective_range, cctv_effectivity)
    # Time messurement
    end_time = time.time()
    elapsed_time = end_time - start_time
    print("Elapsed time: ", elapsed_time, "seconds")
    #print(coordinates_cctv)
    print(np.sum(crime_matrix_test))
    reduced_crime = crime_reduced_cost(crime_matrix_test, crime_matrix_test_final_crime)
    #print(np.sum(changed!=0))
    #print(np.sum(crime_matrix_test_cctv==2))

    text.delete("1.0", customtkinter.END)
    text.insert("1.0", f"Es wird eine Reduktion von {round(reduced_crime)} in der Kategorie {crime_type} erwartet. Dies würde einer Schadensreduktion von {round(reduced_crime * avg_damage)}€ entsprechend.")



    crime_original_map = original_crime(data, crime_type)
    crime_original_map.save('crime_original.map.html')
    show_map('crime_original.map.html')

    coordinates_cctv = get_location_of_cctv(long_diff, lat_diff, lat_min, long_min, crime_matrix_test_cctv, grid_distance)
    cctv_map = create_map(coordinates_cctv)
    cctv_map.save('cctv_map.html')
    show_map('cctv_map.html')

    coordinates_crime_final = get_location_of_crimes(long_diff, lat_diff, lat_min, long_min, crime_matrix_test_final_crime, grid_distance)
    crime_map = create_map(coordinates_crime_final)
    crime_map.save('crime_final_map.html')
    show_map('crime_final_map.html')

    crime_heatmap = create_crime_heatmap_list(coordinates_crime_final)
    crime_heatmap.save('crime_final_heatmap.html')
    show_map('crime_final_heatmap.html')

    combined_map = combined_point_heatmap(coordinates_cctv, data, crime_type)
    combined_map.save('combined_map.html')
    show_map('combined_map.html')


def show_map(map):
    webbrowser.open(map)

frame = customtkinter.CTkFrame(master=root)
frame.pack(pady=15, padx=15, fill="both", expand=True)

label = customtkinter.CTkLabel(master=frame, text="Positionsberechner", height=35, width=500, font=('Time New Roman',30,'bold'))
label.pack(pady=12, padx=10)

entry_1 = customtkinter.CTkEntry(master=frame, placeholder_text="Dateipfad", height=35, width=500)
entry_1.pack(pady=12, padx=10)

entry_2 = customtkinter.CTkEntry(master=frame, placeholder_text="Effktivreichweite", height=35, width=500)
entry_2.pack(pady=12, padx=10)

entry_3 = customtkinter.CTkEntry(master=frame, placeholder_text="Feldgröße", height=35, width=500)
entry_3.pack(pady=12, padx=10)

entry_4 = customtkinter.CTkEntry(master=frame, placeholder_text="Kriminalitätstyp", height=35, width=500)
entry_4.pack(pady=12, padx=10)

entry_5 = customtkinter.CTkEntry(master=frame, placeholder_text="Kameraanzahl", height=35, width=500)
entry_5.pack(pady=12, padx=10)

entry_6 = customtkinter.CTkEntry(master=frame, placeholder_text="Effektivität", height=35, width=500)
entry_6.pack(pady=12, padx=10)

entry_7 = customtkinter.CTkEntry(master=frame, placeholder_text="Durchschnittlicher Schaden", height=35, width=500)
entry_7.pack(pady=12, padx=10)

button = customtkinter.CTkButton(master=frame, text="Positionen berechnen", command= lambda: main_calculate(entry_1.get(), float(entry_2.get()), float(entry_3.get()), entry_4.get(), float(entry_5.get()), float(entry_6.get()), float(entry_7.get())), height=35, width=500)
button.pack(pady=12, padx=10)

text = customtkinter.CTkTextbox(master=frame, height=105, width=500)
text.pack(pady=12, padx=10)

#text.delete("1.0", customtkinter.END)
#text.insert("1.0", f"Test")


root.mainloop()

