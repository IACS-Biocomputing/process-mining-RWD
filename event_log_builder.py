import episode_linking
import os
import sys
import argparse
import pymongo
import time
from datetime import datetime
import pandas as pd
import numpy as np
from tabulate import tabulate

patient_dict = {}
patient_ids = set()

event_list = []

# Check input files availability
stroke_codes = 'data/stroke_codes.csv'
hospital_events = ''
urgent_care_events = ''
patients_data = ''

parser = argparse.ArgumentParser(description='Code Stroke log generator from RWD datasets')
parser.add_argument('hospital_events', type=str, help='Hospital events data file')
parser.add_argument('urgent_care_events', type=str, help='Urgent Care events data file')
parser.add_argument('patients_data', type=str, help='Patients information data file')

args = parser.parse_args()

hospital_events=args.hospital_events
urgent_care_events=args.urgent_care_events
patients_data=args.patients_data

StudyDataSingleton = episode_linking.StudyData()
StudyDataSingleton.first_day_of_study=datetime(2017, 1, 1)
StudyDataSingleton.last_day_of_study=datetime(2017, 12, 31)

input_files = [stroke_codes, hospital_events, urgent_care_events, patients_data]

for infile in input_files:
    if not os.path.isfile(infile):
        print ("Input file '"+infile+"' not found. Please check the inputs directory.", file=sys.stderr)
        exit(-1)


print("---------------------------------------------------")
print("TIMING (secs.)")
print("---------------------------------------------------")

# Stroke codes
start_time = time.time()

try:

    def to_bool(x):
        result = None
        if x is not None:
            if x == 'S':
                result = True
            elif x == 'N':
                result = False
        return result

    stroke_codes_df = pd.read_csv(stroke_codes, sep=";")

    StrokeCodesSingleton = episode_linking.StrokeCodes()
    StrokeCodesSingleton.stroke_codes_df = stroke_codes_df

except Exception as e:
    print("Error processing '" + stroke_codes+ "' " + str(e), file=sys.stderr)
    exit(-1)

stroke_codes_load_time = time.time() - start_time
print("Stroke codes load time = " + str(stroke_codes_load_time))

# Hospital events
start_time = time.time()

try:
    hospital_df = pd.read_csv(hospital_events,
                              parse_dates=['admission_time', 'surgery_time', 'discharge_time'],
                              infer_datetime_format=True)

except Exception as e:
    print("Error processing '" + hospital_events + "' " + str(e), file=sys.stderr)
    exit(-1)

for index, row in hospital_df.iterrows():
    new_event = \
        episode_linking.HospitalEvent(row['event_id'],
                                      row['patient_id'],
                                      row['admission_time'],
                                      row['surgery_time'],
                                      row['discharge_time'],
                                      row['hospital_code'],
                                      row['admission_type'],
                                      row['discharge_code'],
                                      # row['discharge_service_code'],
                                      row['diagnosis_code'],
                                      row['poa1'],
                                      row['d2'],row['poa2'],row['d3'],row['poa3'],row['d4'],row['poa4'],
                                      row['d5'],row['poa5'],row['d6'],row['poa6'],row['d7'],row['poa7'],
                                      row['d8'],row['poa8'],row['d9'],row['poa9'],row['d10'],row['poa10'],
                                      row['d11'],row['poa11'],row['d12'],row['poa12'],row['d13'],row['poa13'],
                                      row['d14'],row['poa14'],row['d15'],row['poa15'])

    event_list.append(new_event)
    patient_ids.add(row['patient_id'])

hosp_events_fetch_time = time.time() - start_time
print("Hospitalisations load time = " +str(hosp_events_fetch_time))

# Urgent events
start_time = time.time()

try:

    def to_bool(x):
        result = None
        if x is not None:
            if x == 'S':
                result = True
            elif x == 'N':
                result = False
        return result

    urgent_care_df = pd.read_csv(urgent_care_events,
                                 parse_dates=['admission_time',
                                              'first_attention_time',
                                              'ct_time',
                                              'fibrinolysis_time',
                                              'observation_room_time',
                                              'discharge_time',
                                              'exit_time'],
                                 infer_datetime_format=True,
                                 converters={'code_stroke_activated': to_bool})
except Exception as e:
    print("Error processing '" + urgent_care_events+ "' " + str(e))
    exit(-1)


# print(tabulate(urgent_care_df.head(20), headers=urgent_care_df.columns, tablefmt='psql'))
#
# print("Number of SUH registers loaded in the dataframe = " + str(len(urgent_care_df)))
# exit(0)

for index, row in urgent_care_df.iterrows():
    new_event = episode_linking.UrgentCareEvent(row['event_id'],
                                                row['patient_id'],
                                                row['admission_time'],
                                                row['first_attention_time'],
                                                row['ct_time'],
                                                row['fibrinolysis_time'],
                                                row['observation_room_time'],
                                                row['discharge_time'],
                                                row['exit_time'],
                                                row['urgent_care_facility_code'],
                                                row['discharge_code'],
                                                row['diagnosis_code'],
                                                row['triage'],
                                                row['code_stroke_activated'])

    event_list.append(new_event)
    patient_ids.add(row['patient_id'])


urg_events_fetch_time = time.time() - start_time
print("Urgent care load time = " + str(urg_events_fetch_time))

# Scatter events per patient
start_time = time.time()

try:
    patients_df = pd.read_csv(patients_data, parse_dates=['dob', 'dod', 'from_dt', 'to_dt'], infer_datetime_format=True)

except Exception as e:
    print("Error processing '" + patients_data + "' " + str(e), file=sys.stderr)
    exit(-1)

for current_patient_id in patient_ids:

    current_patient_data = patients_df.loc[patients_df['patient_id'] == current_patient_id, :]

    if len(current_patient_data) > 0:


        patient_dict[current_patient_id] = episode_linking.Patient(current_patient_id,
                                                                current_patient_data['dob'].iloc[0],
                                                                current_patient_data['dod'].iloc[0],
                                                                current_patient_data['sex'].iloc[0],
                                                                current_patient_data.loc[:, ['location_id', 'from_dt', 'to_dt']])
    else:
        episode_linking.ErroneousDataAccount.missing_patients += 1


for current_event in sorted(event_list):
    if current_event.patient in patient_dict:
        patient_dict[current_event.patient].add_event(current_event)

patient_event_scatter_time = time.time() - start_time
print("Patient event scatter time = " + str(patient_event_scatter_time))

# Close episodes
start_time = time.time()
for patient_id, patient in patient_dict.items():
    patient.close_episodes()
episode_close_time = time.time() - start_time
print("Episode closing time = " + str(episode_close_time))

# Mongo raw event load
start_time = time.time()

# Snapshot-time not required 
# snapshot_time = datetime.now().strftime("%Y%m%d_%H%M")
snapshot_time = ""

mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
mongo_db     = mongo_client["stroke_"+snapshot_time]

if "event_log" in mongo_db.list_collection_names():
    mongo_db["event_log"].drop()

mongo_log_collection = mongo_db["event_log"]

for x in event_list:
    mongo_log_collection.insert_one(vars(x))

mongo_raw_event_insertion_time = time.time() - start_time
print("MongoDB raw events insertion time = " + str(mongo_raw_event_insertion_time))


# Mongo patient and event action log insertion
start_time = time.time()

if "patients" in mongo_db.list_collection_names():
    mongo_db["patients"].drop()

if "activity_log" in mongo_db.list_collection_names():
    mongo_db["activity_log"].drop()

mongo_patients_collection = mongo_db["patients"]
mongo_event_actions = mongo_db["activity_log"]

total_episodes = 0
identified_episodes = 0
stroke_and_incorrect = 0
not_stroke = 0
incorrect_episodes = 0
left_censored = 0
right_censored = 0
incorrect_events = 0
bad_endpoint = 0

for patient_id, patient in patient_dict.items():
    mongo_patients_collection.insert_one(patient.to_dict())

    # A single patient may have multiple episodes, so get each episode and insert the list
    for episode in patient.episode_list:
        total_episodes += 1

        if episode.stroke_episode and episode.correct and not episode.left_censored and not episode.right_censored:
            identified_episodes +=1
            mongo_event_actions.insert_many(episode.to_activity_dict())
        else:

            if not episode.stroke_episode:
                not_stroke += 1

            if not episode.correct:
                incorrect_episodes += 1

            if episode.stroke_episode and not episode.correct:
                stroke_and_incorrect += 1

            if episode.incorrect_event:
                incorrect_events += 1

            if episode.bad_endpoint:
                bad_endpoint += 1

            if episode.left_censored:
                left_censored += 1

            if episode.right_censored:
                right_censored += 1


mongo_patients_insertion_time = time.time() - start_time
print("MongoDB patients insertion time = " + str(mongo_patients_insertion_time))

print("")
print("---------------------------------------------------")
print("STATISTICS")
print("---------------------------------------------------")
print("|---> Total episodes processed = " + str(total_episodes))
print("|---> Identified episodes = " + str(identified_episodes))
print("|")
print("|---> Non-stroke episodes = " + str(not_stroke))
print("|---> Stroke episodes and incorrect = " + str(stroke_and_incorrect))
print("|")
print("|---> Incorrect episodes = " + str(incorrect_episodes))
print("| |--> Incorrect events = " + str(incorrect_events))
print("| |--> Bad endpoint = " + str(bad_endpoint))
print("|")
print("|---> Left censored = " + str(left_censored))
print("|---> Right censored = " + str(right_censored))
print("")
print("")
print("|---> Urgent care suspicious timestamp granularity = " + str(episode_linking.ErroneousDataAccount.urg_suspicious_timestamp_granularity))
print("|---> Missing patients = " + str(episode_linking.ErroneousDataAccount.missing_patients))

# with open("ictusnet_stats_"+snapshot_time+".csv", "w") as f:
#     f.write("episodes_processed," + str(total_episodes)+ "\n")
#     f.write("episodes_identified," + str(identified_episodes)+ "\n")
#     f.write("incorrect_episodes," + str(incorrect_events)+ "\n")
#     f.write("only_urgent_care_events_without_code_stroke," +
#                  str(episode_linking.ErroneousDataAccount.only_urg_care_no_code_stroke)+ "\n")
#     f.write("missing_hospital_event_on_urgent_care_events_to_hospital_discharge," + str(
#         episode_linking.ErroneousDataAccount.urg_care_stroke_to_hosp_missing_hosp)+ "\n")
#     f.write("hospital_surgery_out_of_bounds," +
#                  str(episode_linking.ErroneousDataAccount.hosp_surgery_out_of_bounds)+ "\n")
#     f.write("urgent_care_fibrinolysis_out_of_bounds," +
#                  str(episode_linking.ErroneousDataAccount.urg_fibr_out_of_bounds)+ "\n")
#     f.write("right_cen," + str(right_censored_or_missing_long_stay)+ "\n")
#     f.write("right_censored_episodes," + str(episode_linking.ErroneousDataAccount.right_censored)+ "\n")
#     f.write("missing_long_stay_hospital_episodes," +
#                  str(episode_linking.ErroneousDataAccount.missing_long_stay_hospital)+ "\n")
#     f.write("urgent_care_suspicious_timestamp_granularity," + str(
#         episode_linking.ErroneousDataAccount.urg_suspicious_timestamp_granularity)+ "\n")
#     f.write("missing_patients," + str(episode_linking.ErroneousDataAccount.missing_patients)+ "\n")
#
