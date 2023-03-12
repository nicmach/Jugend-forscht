import pandas as pd
import numpy as np
import geopy.distance
import math
import folium
from folium.plugins import HeatMap

# NOTE: There is an approximation made here (i.e. that the latitudes, when calculating the distance between longitudes, are the same)
# As we are normally working with smaller distances, this should make pretty much no difference.

# This function is used to determine the number of partitions to be made, based on an approximate distance (e.g. according to baltimore police CCTV is effective in ca. 256ft)
def calculate_partition_amount(data, distance=0.050):
  lat_max = data['LATITUDE'].max()
  lat_min = data['LATITUDE'].min()
  long_max = data['LONGITUDE'].max()
  long_min = data['LONGITUDE'].min()

  # Calculating the distance between the furthest longitudes
  
  coord_1 = (lat_max, long_max)
  coord_2 = (lat_max, long_min)

  long_dist = geopy.distance.geodesic(coord_1, coord_2).km
  long_partition_amount = round(long_dist/ distance)
  long_diff = (long_max - long_min) / long_partition_amount

  coord_1 = (lat_max, long_max)
  coord_2 = (lat_min, long_max)

  lat_dist = geopy.distance.geodesic(coord_1, coord_2).km
  lat_partition_amount = round(lat_dist/ distance)
  lat_diff = ( lat_max -  lat_min) /  lat_partition_amount

  return long_dist, long_partition_amount, long_diff, lat_dist, lat_partition_amount, lat_diff

def partitioning(data, distance = 0.050):
  long_dist, long_partition_amount, long_diff, lat_dist, lat_partition_amount, lat_diff = calculate_partition_amount(data, distance)

  lat_max = data['LATITUDE'].max()
  lat_min = data['LATITUDE'].min()
  long_max = data['LONGITUDE'].max()
  long_min = data['LONGITUDE'].min()

  crime_matrix = np.zeros((lat_partition_amount+1, long_partition_amount+1))

  for i in range(len(data.index)):
    index_column = round((data.iloc[i].LONGITUDE - long_min) / long_diff)
    index_row = round((data.iloc[i].LATITUDE - lat_min) / lat_diff)
    crime_matrix[index_row][index_column] += 1

  return crime_matrix, long_diff, lat_diff, lat_min, long_min, long_max, lat_max

# As the name of the function says, it will create a dataset containing only specific crimes.

def create_crime_type_matrix(data, distance = 0.050, crimeType='VEHICLE CRIME'):
  crime_specific_data = data.loc[data['CRIME TYPE'] == crimeType]
  crime_specific_matrix, long_diff, lat_diff, lat_min, long_min, long_max, lat_max = partitioning(crime_specific_data, distance)

  return crime_specific_matrix, long_diff, lat_diff, lat_min, long_min, long_max, lat_max

def impacted_fields(distance, cctv_effectivity=0.078): 
  fields =  math.floor(abs(cctv_effectivity - 0.5 * distance) / distance) # The 0.5 * distance resembles the fact, that the camera is placed in the middle of the field
  return fields

def shift(matrix, row, col):

  shifted_arr = matrix

  if (row == 0) and (col == 0):
    return matrix

  if row < 0:
    zeros_arr = np.zeros((abs(row), matrix.shape[1]))
    matrix_copy_padded = np.vstack((shifted_arr, zeros_arr))
    shifted_arr = matrix_copy_padded[abs(row):]

  elif row > 0:
    matrix_copy_padded = np.pad(shifted_arr, ((abs(row), 0), (0, 0)), mode='constant', constant_values=0)
    shifted_arr = matrix_copy_padded[:-abs(row)]
  
  if col < 0:
    zeros_arr = np.zeros((matrix.shape[0], abs(col)))
    matrix_copy_padded = np.concatenate((zeros_arr, shifted_arr), axis=1)
    shifted_arr = matrix_copy_padded[:, :-abs(col)]

  elif col > 0:
    matrix_copy_padded = np.pad(shifted_arr, ((0, 0), (0, abs(col))), mode='constant', constant_values=0)
    shifted_arr = matrix_copy_padded[:, abs(col):]
  
  return shifted_arr

def calculate_difference_matrix(crime_matrix, coordinates_changed, distance, cctv_effectivity=0.078, effectivity=0):

  number_of_fields = impacted_fields(distance, cctv_effectivity)

  if number_of_fields != 0:
    crime_matrix_edit = np.copy(crime_matrix)
    crime_matrix_edit[coordinates_changed == 1] = 0
    crime_difference_matrix = np.zeros_like(crime_matrix_edit)

    for row in range(-number_of_fields, number_of_fields + 1):
      for col in range(-number_of_fields, number_of_fields + 1):
        
        if ((abs(row) + abs(col)) <= number_of_fields):
            field_shift = shift(crime_matrix_edit, row, col)
            crime_difference_matrix = crime_difference_matrix + field_shift

  elif number_of_fields == 0:
    print("Is zero")
    crime_matrix_edit = np.copy(crime_matrix)
    crime_matrix_edit[coordinates_changed == 1] = 0
    crime_difference_matrix = np.copy(crime_matrix_edit)

  crime_difference_matrix = crime_difference_matrix * effectivity

  return crime_difference_matrix

def cctv_placement(crime_matrix, cctv_number, distance=0.05, cctv_effectivity=0.078, effectivity=0):

  coordinates_changed = np.zeros_like(crime_matrix)

  cctv_matrix = np.zeros_like(crime_matrix)

  difference_crime_matrix = calculate_difference_matrix(crime_matrix, coordinates_changed, distance, cctv_effectivity, effectivity)
  print(difference_crime_matrix.sum())
  final_crime_matrix = np.copy(crime_matrix)
  number_of_fields = impacted_fields(distance, cctv_effectivity)
  num_rows, num_cols = final_crime_matrix.shape


  # Getting the highest values of the difference matrix (corresponding to the cctv_number)
  difference_crime_matrix_flat = difference_crime_matrix.flatten()
  indices = np.argpartition(difference_crime_matrix_flat, -int(cctv_number*20))[-int(cctv_number*20):]
  indices_sorted = indices[np.argsort(difference_crime_matrix_flat[indices])]
  indices_sorted = indices_sorted[::-1]
  row_indices, col_indices = np.unravel_index(indices_sorted, difference_crime_matrix.shape)
  print(difference_crime_matrix[row_indices[:100], col_indices[:100]])

  # For the gradual implementation of the maxima finder algorithm the difference matrix is
  # calculated after a certain number of cameras was placed. This number is defined by the
  # following ratio.

  recalculate_ratio = 0.2
  recalculate_turn = int(round(cctv_number * recalculate_ratio))


  cameras_placed = 0
  
  while cameras_placed < cctv_number:

      for j in range(0,int(cctv_number * recalculate_ratio)):
        if (cameras_placed == cctv_number):
            break
        
        for i in range(len(indices_sorted)):

          if (cctv_matrix[row_indices[i], col_indices[i]] != 2) and (cctv_matrix[row_indices[i], col_indices[i]] != 1): 
            cctv_matrix[row_indices[i], col_indices[i]] = 2
            final_crime_matrix[row_indices[i], col_indices[i]] = final_crime_matrix[row_indices[i], col_indices[i]] * (1-effectivity)
            cameras_placed += 1
            coordinates_changed[row_indices[i], col_indices[i]] = 1

            current_row = row_indices[i] 
            current_col = col_indices[i]

            for row in range(current_row - number_of_fields, current_row + number_of_fields + 1):
              for col in range(-1 * (number_of_fields - abs(current_row - row)), number_of_fields - abs(current_row - row) + 1):
                if (row < num_rows) and (row >= 0) and (col + current_col < num_cols) and (current_col + col >= 0):
                    if (cctv_matrix[row][current_col + col] != 1) and (cctv_matrix[row][current_col + col] != 2):
                      if (row != row_indices[i]) or (current_col + col != col_indices[i]):
                        final_crime_matrix[row, current_col + col] = final_crime_matrix[row, current_col + col] * (1-effectivity)
                        cctv_matrix[row, current_col + col] = 1
                        coordinates_changed[row, current_col + col] = 1
            
            break

          elif cctv_matrix[current_row, current_col] == 1:
            cctv_matrix[current_row, current_col] = 2    
            cameras_placed += 1
            
            for row in range(current_row - number_of_fields, current_row + number_of_fields + 1):
              for col in range(-1 * (number_of_fields - abs(current_row - row)), number_of_fields - abs(current_row - row) + 1):
                if (row < num_rows) and (row >= 0) and (col + current_col < num_cols) and (current_col + col >= 0):
                  if (cctv_matrix[row][current_col + col] != 1) and (cctv_matrix[row][current_col + col] != 2):
                    if (row != row_indices[i]) or (current_col + col != col_indices[i]):
                      final_crime_matrix[row, current_col + col] = final_crime_matrix[row, current_col + col] * (1-effectivity)
                      cctv_matrix[row, current_col + col] = 1
                      coordinates_changed[row, current_col + col] = 1

            break

        print(np.sum(cctv_matrix==2)) 

      if (cameras_placed % recalculate_turn == 0) and (cameras_placed != 0) and (cameras_placed != cctv_number):
        difference_crime_matrix = calculate_difference_matrix(final_crime_matrix, coordinates_changed, distance, cctv_effectivity, effectivity)
        print(np.sum(difference_crime_matrix))
        #for idx in range(len(cctv_matrix)):
        #  difference_crime_matrix[cctv_matrix == 1] = 0
        
        difference_crime_matrix_flat = difference_crime_matrix.flatten()
        indices = np.argpartition(difference_crime_matrix_flat, -int(cctv_number*20))[-int(cctv_number*20):]
        indices_sorted = indices[np.argsort(difference_crime_matrix_flat[indices])]
        indices_sorted = indices_sorted[::-1]
        row_indices, col_indices = np.unravel_index(indices_sorted, difference_crime_matrix.shape)
        print(difference_crime_matrix[row_indices[:100], col_indices[:100]])
      
      
  

  return final_crime_matrix, cctv_matrix

def crime_reduced_cost(crime_matrix, crime_matrix_final):
  return np.sum(crime_matrix) - np.sum(crime_matrix_final)

def get_location_of_cctv(long_diff, lat_diff, lat_min, long_min, data_cctv, distance=0.050):

  coordinates = []

  num_rows, num_cols = data_cctv.shape

  for index1 in range(num_rows):
    for index2 in range(num_cols):

      if data_cctv[index1, index2] == 2:

        # NOTE: Due to the rounding in the creation of the partitioning it might come to smaller inaccuracies in comparison to the original coordinates
        latitude = lat_min + index1 * lat_diff
        longitude = long_min + index2 * long_diff

        coordinates.append([latitude, longitude])


  return coordinates

def create_map(coordinates):

  m = folium.Map()

  for point in coordinates:
      folium.CircleMarker(point, radius=3, color='red').add_to(m)

  return m

def get_location_of_crimes(long_diff, lat_diff, lat_min, long_min, crime_matrix, distance=0.050):

  coordinates = []

  num_rows, num_cols = crime_matrix.shape

  for index1 in range(num_rows):
    for index2 in range(num_cols):

      if crime_matrix[index1, index2] == 2:

        # NOTE: Due to the rounding in the creation of the partitioning it might come to smaller inaccuracies in comparison to the original coordinates
        latitude = lat_min + index1 * lat_diff
        longitude = long_min + index2 * long_diff

        coordinates.append([latitude, longitude])


  return coordinates

def create_crime_heatmap_list(crime_matrix):

  m = folium.Map()

  HeatMap(crime_matrix).add_to(m)

  return m

def combined_point_heatmap(base_coordinates, data, crime_type):
  
  data  = data[data['CRIME TYPE'] == crime_type]
  crime_coordinates = list(zip(data['LATITUDE'].tolist(), data['LONGITUDE'].tolist()))

  m = folium.Map()

  heatmap = HeatMap(data=crime_coordinates, radius=15)

  point_map = folium.FeatureGroup(name='point_map')
  for coord in base_coordinates:
    folium.CircleMarker(coord, radius=2, color='red', fill=True).add_to(point_map)

  point_map.add_to(m)
  heatmap.add_to(m)

  return m

def original_crime(data, crime_type):

  data  = data[data['CRIME TYPE'] == crime_type]

  m = folium.Map(prefer_canvas=True)

  for index, row in data.iterrows():
    folium.CircleMarker(location=[row['LATITUDE'], row['LONGITUDE']], radius = 2, color = 'red').add_to(m)

  return m