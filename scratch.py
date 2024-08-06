import pandas as pd
import matplotlib.pyplot as plt

# Load the main CSV file
file_path_main = '/Users/sunshinedaydream/Library/CloudStorage/GoogleDrive-smock.samuel@gmail.com/My Drive/h2oSplash/Measurements/SUBS_measurement_data_2024_06_25_0000_2024_06_25_2359_daily_export_3_SamMeasurements.h5'  # Update with the correct path to your file
df_main = pd.read_csv(file_path_main)

# Load the additional CSV file
file_path_additional = '/Volumes/NO NAME/Teilizahlen_FakRat (Kopie)/tut-Semester.csv'  # Update with the correct path to your additional CSV file
df_additional = pd.read_csv(file_path_additional)


# Summarize the main data
summary = df_main.groupby(['Semester1', 'SemesterNo', 'Fakultät']).size().reset_index(name='count')

# Create a new DataFrame for the desired format
summary_formatted = pd.DataFrame()

# Process each semester
for semester in summary['Semester1'].unique():
    semester_data = summary[summary['Semester1'] == semester]
    
    # Count entries for Fakultät 3
    fakultat3_count = semester_data[semester_data['Fakultät'] == 3]['count'].sum()
    
    # Count entries for other faculties
    andere_fakultaten_count = semester_data[semester_data['Fakultät'] != 3]['count'].sum()
    
    # Append data to the new DataFrame
    semester_no = semester_data['SemesterNo'].iloc[0]
    summary_formatted = summary_formatted.append({
        'Semester1': semester,
        'SemesterNo': semester_no,
        'Fakultät': 'Fakultät 3',
        'count': fakultat3_count
    }, ignore_index=True)
    
    summary_formatted = summary_formatted.append({
        'Semester1': semester,
        'SemesterNo': semester_no,
        'Fakultät': 'Andere Fakultäten',
        'count': andere_fakultaten_count
    }, ignore_index=True)

# Sort by SemesterNo
summary_formatted = summary_formatted.sort_values(by='SemesterNo')

# Summarize the additional data by counting unique ids for each semester
unique_ids_count = df_additional.groupby('Semester')['Tut'].nunique().reset_index()
unique_ids_count.columns = ['Semester1', 'tutCount']

# Merge the two summaries
merged_summary = pd.merge(summary_formatted, unique_ids_count, on='Semester1', how='left')

# Print the head of the merged DataFrame
print(merged_summary.head())

# Export the merged data to CSV (commented out for investigation)
# merged_summary.to_csv('merged_summarized_fakSemester.csv', index=False)

# Pivot the data for plotting
pivot_df = merged_summary.pivot_table(index=['Semester1', 'SemesterNo'], columns='Fakultät', values='count', aggfunc='sum').fillna(0)

# Reset index to get Semester1 back as a column for plotting
pivot_df = pivot_df.reset_index()

# Plotting the stacked bar chart with secondary y-axis for the line chart
fig, ax1 = plt.subplots(figsize=(12, 8))

# Plotting the stacked bar chart
pivot_df.plot(x='Semester1', y=['Fakultät 3', 'Andere Fakultäten'], kind='bar', stacked=True, ax=ax1)
ax1.set_xlabel('Semester')
ax1.set_ylabel('Teilnehmer/innen')
ax1.set_title('Teilnehmende Pro Jahr/ Fakultät')
ax1.legend(title='Fakultät')
plt.xticks(rotation=45, ha='right')

# Creating the secondary y-axis and plotting the line chart
ax2 = ax1.twinx()
ax2.plot(pivot_df['Semester1'], merged_summary['tutCount'], color='red', marker='o', linewidth=2, label='SB Stellen')
ax2.set_ylabel('SB Stellen')
ax2.legend(loc='upper left')

plt.tight_layout()
plt.show()
