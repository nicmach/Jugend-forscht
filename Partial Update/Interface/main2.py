from helper import *
import time
import webbrowser

data = pd.read_csv(r'C:\Users\samue\OneDrive\Desktop\Jugend-forscht-main\Interface\test_data\baton_rouge_final.csv')
distance = 0.01
# Time messurement
start_time = time.time()
crime_matrix_test, long_diff, lat_diff, lat_min, long_min, long_max, lat_max = create_crime_type_matrix(data, distance=0.01, crimeType='MISCELLANEOUS')
print(crime_matrix_test.shape)
crime_matrix_test_final_crime, crime_matrix_test_cctv, crime_matrix_test_final_difference, changed = cctv_placement(crime_matrix_test, 50, distance, 0.078, 0.2)
# Time messurement
end_time = time.time()
elapsed_time = end_time - start_time
print("Elapsed time: ", elapsed_time, "seconds")
#print(coordinates_cctv)
print(np.sum(crime_matrix_test))
reduced_crime = crime_reduced_cost(crime_matrix_test, crime_matrix_test_final_crime)
print(reduced_crime)

coordinates_cctv = get_location_of_cctv(long_diff, lat_diff, lat_min, long_min, crime_matrix_test_cctv, distance)
combined_map = combined_point_heatmap(coordinates_cctv, data, 'MISCELLANEOUS')
combined_map.save('combined_map.html')
webbrowser.open('combined_map.html')