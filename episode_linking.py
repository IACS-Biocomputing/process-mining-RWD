from functools import total_ordering
import abc
from datetime import datetime, timedelta
import calendar
import pytz
import pandas as pd
import numpy as np
import json
from bson import json_util

madrid_time = pytz.timezone('Europe/Madrid')


def madrid_datetime(datetime_var):
    result = None

    # date to datetime as in https://stackoverflow.com/a/1937636/9664743

    if datetime_var is not None and datetime_var is not pd.NaT:
        # https://stackoverflow.com/a/1423736/9664743
        if not datetime_var.time():
            result = datetime.combine(datetime_var, datetime.min.time())
        else:
            result = datetime_var

        # Check if datetime is a naïve date (do not have tzinfo) https://stackoverflow.com/a/27596917/9664743
        # if datetime_var.tzinfo is None or datetime_var.tzinfo.utcoffset(datetime_var) is None:

        # result = madrid_time.localize(datetime_var)
        result = datetime.utcfromtimestamp(calendar.timegm(result.timetuple()))

    return result


class ErroneousDataAccount:

    missing_patients = 0
    non_stroke_epidose = 0
    only_urg_care_no_code_stroke = 0
    urg_care_stroke_to_hosp_missing_hosp = 0
    hosp_surgery_out_of_bounds = 0
    urg_suspicious_timestamp_granularity = 0
    urg_fibr_out_of_bounds = 0
    missing_hospital_link = 0
    right_censored = 0

# Singleton taken from
# https://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html
class StrokeCodes(object):

    class __StrokeCodes:
        def __init__(self):
            self.stroke_codes_df = None


        def get_type(self, code_to_check):

            if code_to_check is None:
                return None
            else:
                clean_code = str(code_to_check).replace('.', '')

                result = self.stroke_codes_df[self.stroke_codes_df['clean_code'] == clean_code]

                if result.empty:
                    return None
                else:
                    return result

    instance = None

    def __new__(cls): # __new__ always a classmethod
        if not StrokeCodes.instance:
            StrokeCodes.instance = StrokeCodes.__StrokeCodes()
        return StrokeCodes.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)

# Singleton taken from
# https://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html
class StudyData(object):

    class __StudyData:
        def __init__(self):
            self.first_day_of_study = None
            self.last_day_of_study = None


    instance = None

    def __new__(cls): # __new__ always a classmethod
        if not StudyData.instance:
            StudyData.instance = StudyData.__StudyData()
        return StudyData.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)



@total_ordering
class Event:

    def __init__(self, event_id, event_type, patient, start_time, end_time):
        self.episode_id = 0
        self.event_id = event_id
        self.event_type = event_type
        self.patient = patient
        self.start_time = start_time
        self.end_time = end_time
        self.correct = True
        self.suspicious = False

    @abc.abstractmethod
    def check_correctness(self):
        pass

    @abc.abstractmethod
    def synchronize_timestamps(self, prev_event):
        pass

    @abc.abstractmethod
    def to_activity_dict(self):
        pass

    def __eq__(self, other):
        return (self.event_id == other.event_id and self.event_type == other.evt_type and
                self.start_time == other.start_time and self.end_time == other.end_time and
                self.used == other.used)

    def __lt__(self, other):

        if self.event_type == other.event_type:

            return self.start_time < other.start_time

        else:

            if self.start_time.date() == other.start_time.date():
                # When timestamps are the same, the urgent care is supposed to occur before the hospitalization
                return self.event_type == "URG"
            else:
                return self.start_time.date() < other.start_time.date()


class HospitalEvent(Event):

    def __init__(self,
                 event_id,
                 patient,
                 admission_time,
                 surgery_time,
                 discharge_time,
                 hospital_code,
                 admission_type,
                 discharge_code,
                 diagnosis_code,
                 poa1,
                 d2, poa2, d3, poa3, d4, poa4, d5, poa5, d6, poa6, d7, poa7, d8, poa8, d9, poa9, d10, poa10,
                 d11, poa11, d12, poa12, d13, poa13, d14, poa14, d15, poa15):

        super().__init__(event_id, 'HOSP', patient, madrid_datetime(admission_time), madrid_datetime(discharge_time))

        self.admission_time = madrid_datetime(admission_time)
        self.surgery_time = madrid_datetime(surgery_time)
        self.discharge_time = madrid_datetime(discharge_time)

        self.long_stay_hospital = False
        self.stroke_event = StrokeCodes().get_type(diagnosis_code) is not None

        self.hospital_code = hospital_code
        self.admission_type = admission_type
        self.discharge_code = discharge_code
        # self.discharge_service_code = discharge_service_code

        self.diagnosis_code = diagnosis_code
        self.poa1 = poa1

        self.d2 = d2
        self.poa2 = poa2
        self.d3 = d3
        self.poa3 = poa3
        self.d4 = d4
        self.poa4 = poa4
        self.d5 = d5
        self.poa5 = poa5
        self.d6 = d6
        self.poa6 = poa6
        self.d7 = d7
        self.poa7 = poa7
        self.d8 = d8
        self.poa8 = poa8
        self.d9 = d9
        self.poa9 = poa9
        self.d10 = d10
        self.poa10 = poa10
        self.d11 = d11
        self.poa11 = poa11
        self.d12 = d12
        self.poa12 = poa12
        self.d13 = d13
        self.poa13 = poa13
        self.d14 = d14
        self.poa14 = poa14
        self.d15 = d15
        self.poa15 = poa15

        self.correct, self.suspicious = self.check_correctness()


    def check_correctness(self):
        correct = True
        suspicious = False

        if self.surgery_time is not None and \
                (self.surgery_time < self.admission_time or self.surgery_time > self.discharge_time):
            ErroneousDataAccount.hosp_surgery_out_of_bounds += 1
            correct = False

        return [correct, suspicious]

    def synchronize_timestamps(self, prev_event=None):

        if prev_event is None:
            admission_timedelta = timedelta(hours=12)
        else:
            admission_timedelta = prev_event.end_time - self.admission_time + timedelta(seconds=1)

        self.admission_time = self.admission_time + admission_timedelta

        if self.discharge_time.date() == self.admission_time.date():
            self.discharge_time = self.admission_time + timedelta(seconds=1)
        else:
            self.discharge_time = self.discharge_time + timedelta(hours=12)

        if self.surgery_time is not None:
            if self.surgery_time.date() == self.admission_time.date():
                self.surgery_time = self.admission_time + timedelta(seconds=1)
            else:
                self.surgery_time = self.surgery_time + timedelta(hours=12)

            if self.surgery_time.date() == self.discharge_time.date():
                self.discharge_time = self.surgery_time + timedelta(seconds=1)

        self.start_time = self.admission_time
        self.end_time = self.discharge_time


    def sync_from_next_event(self, next_event):


        # Decision: ONLY MODIFY THE DISCHARGE AND THE POSSIBLE SURGERY TIME. NEVER THE ADMISSION TIME
        self.discharge_time = next_event.start_time

        # if self.admission_time.date() == self.discharge_time.date():
        #     self.admission_time == self.discharge_time - timedelta(seconds = 1)

        if self.surgery_time is not None:
            if self.surgery_time.date() == self.discharge_time.date():
                self.surgery_time = self.discharge_time - timedelta(seconds=1)

            # if self.surgery_time.date() == self.admission_time.date():
            #     self.admission_time = self.surgery_time - timedelta(seconds=1)

        self.end_time = self.discharge_time



    def to_activity_dict(self, episode_id):
        result = []

        evt_prefix = ""
        if self.long_stay_hospital:
            evt_prefix = "long_stay_"

        result.append(
            {
                "id": episode_id,
                "hospital_event_id": self.event_id,
                "event": evt_prefix+"hospital_admission",
                "timestamp": self.admission_time,
                "resource": self.hospital_code,
                "hospital_id": self.hospital_code,
                "admission_type": self.admission_type
            }
        )

        if self.surgery_time is not None:
            result.append(
                {
                    "id": episode_id,
                    "hospital_event_id": self.event_id,
                    "event": evt_prefix+"hospital_surgery",
                    "timestamp": self.surgery_time,
                    "resource": self.hospital_code
                }
            )

        result.append(
            {
                "id": episode_id,
                "hospital_event_id": self.event_id,
                "event": evt_prefix+"hospital_discharge",
                "timestamp": self.discharge_time,
                "resource": self.hospital_code,
                "hospital_diagnosis_code": self.diagnosis_code,
                "hospital_discharge_code": self.discharge_code
            }
        )

        return result


class UrgentCareEvent(Event):

    def __init__(self,
                 event_id,
                 patient,
                 admission_time,
                 first_attention_time,
                 ct_time,
                 fibrinolysis_time,
                 observation_room_time,
                 discharge_time,
                 exit_time,
                 urgent_care_facility_code,
                 discharge_code,
                 diagnosis_code,
                 triage,
                 code_stroke_activated):

        # solution to avoid None times from https://stackoverflow.com/a/6254950/9664743
        # We are considering possible admission, first attention, fibrinolysis or observation as start times
        # and observation room, discharge and exit as possible end times
        super().__init__(event_id,
                         'URG',
                         patient,
                         min([t for t in [madrid_datetime(admission_time),
                                          madrid_datetime(ct_time),
                                          madrid_datetime(first_attention_time),
                                          madrid_datetime(fibrinolysis_time),
                                          madrid_datetime(observation_room_time)] if t is not None]),
                         max([t for t in [madrid_datetime(observation_room_time),
                                          madrid_datetime(discharge_time),
                                          madrid_datetime(exit_time)] if t is not None]))

        self.admission_time = madrid_datetime(admission_time)
        self.first_attention_time = madrid_datetime(first_attention_time)
        self.ct_time = madrid_datetime(ct_time)
        self.fibrinolysis_time = madrid_datetime(fibrinolysis_time)
        self.observation_room_time = madrid_datetime(observation_room_time)
        self.discharge_time = madrid_datetime(discharge_time)
        self.exit_time = madrid_datetime(exit_time)
        self.urgent_care_facility_code = urgent_care_facility_code
        self.discharge_code = discharge_code
        self.diagnosis_code = diagnosis_code
        self.triage = triage
        self.code_stroke_activated = None if code_stroke_activated == np.nan else code_stroke_activated
        self.correct, self.suspicious = self.check_correctness()
        self.stroke_suspect = StrokeCodes().get_type(diagnosis_code) is not None

    def second_to_last_time(self):

        times = [self.admission_time,
                 self.first_attention_time,
                 self.ct_time,
                 self.fibrinolysis_time,
                 self.observation_room_time,
                 self.discharge_time,
                 self.exit_time]

        times = sorted([x for x in times if x is not None])

        return times[-2]


    def check_correctness(self):
        correct = True
        suspicious = False

        urg_care_timestamps = [self.admission_time,
                               self.first_attention_time,
                               self.ct_time,
                               self.fibrinolysis_time,
                               self.observation_room_time,
                               self.discharge_time,
                               self.exit_time]

        for time in urg_care_timestamps:
            if time is not None:
                minutes = time.minute
                seconds = time.second
                if minutes%5 == 0 and seconds == 0:
                    ErroneousDataAccount.urg_suspicious_timestamp_granularity += 1
                    suspicious = True

        # As CT time may have been entered manually, check for possible *year*, *month* and event *day*!
        # mismatch
        if self.ct_time is not None:

            if self.admission_time is not None:

                if (self.ct_time.year < self.admission_time.year and
                        self.ct_time.year < self.first_attention_time.year):
                    self.ct_time = self.ct_time.replace(year=self.admission_time.year)

                if self.first_attention_time is not None:

                    if ((self.ct_time.year == self.admission_time.year and
                         self.ct_time.year == self.first_attention_time.year) and
                            (self.ct_time.month != self.admission_time.month and
                             self.ct_time.month != self.first_attention_time.month)):
                        self.ct_time = self.ct_time.replace(month=self.admission_time.month)

                    if ((self.ct_time.year == self.admission_time.year and
                         self.ct_time.year == self.first_attention_time.year) and
                            (self.ct_time.month == self.admission_time.month and
                             self.ct_time.month == self.first_attention_time.month) and
                            (self.ct_time.day != self.admission_time.day and
                             self.ct_time.day != self.first_attention_time.day)):
                        self.ct_time = self.ct_time.replace(day=self.admission_time.day)

        # As fibrinolysis time may have been entered manually, check for possible *year*, *month* and event *day*!
        # mismatch
        if self.fibrinolysis_time is not None:

            if self.admission_time is not None:

                if (self.fibrinolysis_time.year < self.admission_time.year and
                        self.fibrinolysis_time.year < self.first_attention_time.year):

                    self.fibrinolysis_time = self.fibrinolysis_time.replace(year=self.admission_time.year)

                if self.first_attention_time is not None:

                    if ((self.fibrinolysis_time.year == self.admission_time.year and
                            self.fibrinolysis_time.year == self.first_attention_time.year) and
                            (self.fibrinolysis_time.month != self.admission_time.month and
                                self.fibrinolysis_time.month != self.first_attention_time.month)):

                        self.fibrinolysis_time = self.fibrinolysis_time.replace(month=self.admission_time.month)

                    if ((self.fibrinolysis_time.year == self.admission_time.year and
                         self.fibrinolysis_time.year == self.first_attention_time.year) and
                            (self.fibrinolysis_time.month == self.admission_time.month and
                             self.fibrinolysis_time.month == self.first_attention_time.month) and
                                (self.fibrinolysis_time.day != self.admission_time.day and
                                self.fibrinolysis_time.day != self.first_attention_time.day)):

                        self.fibrinolysis_time = self.fibrinolysis_time.replace(day=self.admission_time.day)

        return [correct, suspicious]

    def synchronize_timestamps(self, prev_event=None):
        if prev_event is not None and prev_event.event_type == "HOSP":
            prev_event.sync_from_next_event(self)

    def to_activity_dict(self, episode_id):

        result = []

        result.append(
            {
                "id": episode_id,
                "urgent_care_event_id": self.event_id,
                "event": "urgent_care_admission",
                "timestamp": self.admission_time,
                "resource": self.urgent_care_facility_code,
                "urgent_care_hospital_id": self.urgent_care_facility_code,
                "triage": self.triage
            }
        )

        if self.first_attention_time is not None:
            result.append(
                {
                    "id": episode_id,
                    "urgent_care_event_id": self.event_id,
                    "event": "urgent_care_first_attention",
                    "timestamp": self.first_attention_time,
                    "resource": self.urgent_care_facility_code
                }
            )

        if self.ct_time is not None:
            result.append(
                {
                    "id": episode_id,
                    "urgent_care_event_id": self.event_id,
                    "event": "urgent_care_ct",
                    "timestamp": self.ct_time,
                    "resource": self.urgent_care_facility_code
                }
            )

        if self.fibrinolysis_time is not None:
            result.append(
                {
                    "id": episode_id,
                    "urgent_care_event_id": self.event_id,
                    "event": "urgent_care_fibrinolysis",
                    "timestamp": self.fibrinolysis_time,
                    "resource": self.urgent_care_facility_code
                }
            )

        if self.observation_room_time is not None:
            result.append(
                {
                    "id": episode_id,
                    "urgent_care_event_id": self.event_id,
                    "event": "urgent_care_observation_room",
                    "timestamp": self.observation_room_time,
                    "resource": self.urgent_care_facility_code
                }
            )

        result.append(
            {
                "id": episode_id,
                "urgent_care_event_id": self.event_id,
                "event": "urgent_care_discharge",
                "timestamp": self.discharge_time,
                "resource": self.urgent_care_facility_code,
                "urgent_care_diagnosis_code": self.diagnosis_code,
                "urgent_care_discharge_code": self.discharge_code
            }
        )

        if self.exit_time is not None:
            result.append(
                {
                    "id": episode_id,
                    "urgent_care_event_id": self.event_id,
                    "event": "urgent_care_exit",
                    "timestamp": self.exit_time,
                    "resource": self.urgent_care_facility_code
                }
            )

        return result


class Patient:

    def __init__(self, patient_id, dob, dod, sex, location_history, gma_n_affected_systems = None, gma_weight = None):
        self.patient_id = patient_id

        self.dob = madrid_datetime(dob)
        self.dod = madrid_datetime(dod)
        self.sex = sex
        self.gma_n_affected_systems = gma_n_affected_systems
        self.gma_weight = gma_weight
        self.location_history = location_history
        self.location_history[["from_dt", "to_dt"]] = \
            self.location_history[["from_dt", "to_dt"]].applymap(madrid_datetime).replace({pd.NaT:None})
        self.episode_list = []

    def add_event(self, new_event: Event):
        if len(self.episode_list) == 0:
            self.episode_list.append(Episode())

        if not self.episode_list[-1].add_event(new_event):
            # Current event did not link with previous episode event

            # Update location
            self.episode_list[-1].add_location(self.location_history)

            # And start a new episode
            self.episode_list.append(Episode())
            self.episode_list[-1].add_event(new_event)

    def close_episodes(self):
        for ep in self.episode_list:
            ep.close()

    def to_dict(self):
        # Here 'dict' is required to copy the dictionary of the object and avoid the overwriting done by following
        # statements
        result = dict(vars(self))
        result['location_history'] = self.location_history.to_dict(orient='records')
        result['episode_list'] = [ep.to_dict() for ep in self.episode_list]
        return result

    def to_json(self):
        return json.dumps(self.to_dict(), default=json_util.default)

    def to_event_activity_dict(self):
        return [ep.to_event_activity_dict() for ep in self.episode_list]

class Episode:

    episode_id_seq = 0

    def __init__(self):
        Episode.episode_id_seq += 1

        self.open = True

        self.episode_id = Episode.episode_id_seq

        # In aragon, the ZBS
        self.location_id = 0

        self.stroke_episode = False
        self.correct = True
        self.suspicious = False

        self.left_censored = False
        self.right_censored = False

        self.bad_endpoint = False
        self.incorrect_event = False

        self.event_list = []

    def add_event(self, new_event):

        event_included = False

#        print("Episode " + str(self.episode_id) + ". Adding event " + str(new_event.event_id))

        if len(self.event_list) == 0:
            self.event_list.append(new_event)
            new_event.episode_id = self.episode_id
            event_included = True

        else:
            prev_event = self.event_list[-1]
            if self.linked_events(prev_event, new_event):
                self.event_list.append(new_event)
                new_event.episode_id = self.episode_id
                event_included = True
                new_event.synchronize_timestamps(prev_event)

        if not event_included:
            pass 
#            print("Event not linked!")

        # Check if there are hospital events in the episode, to ease the further cleanup
        if event_included is True and new_event.event_type == 'HOSP':

            if new_event.stroke_event:
                self.stroke_episode = True

        # Check if there are urgent care events specific states, to ease the further cleanup
        if event_included is True and new_event.event_type == 'URG':
            if (new_event.code_stroke_activated is not None and new_event.code_stroke_activated) or \
                    new_event.stroke_suspect:
                self.stroke_episode = True

            # It is required here to verify all partners use same codes
            # if new_event.discharge_code == 6:
            #   self.urgent_care_to_hospital_discharges = True

        if event_included is False:
            self.close()
#            print("Closing episode!")
        else:
            if not new_event.correct:
                self.incorrect_event = True
                self.correct = False

        return event_included

    def close(self):

        if self.open and self.stroke_episode and self.correct:

            last_event = self.event_list[-1]

            if last_event.event_type == 'URG':
                if last_event.discharge_code in [2, 6, 11]:
                    self.correct = False
                    self.bad_endpoint = True

            if last_event.event_type == 'HOSP':
                if last_event.discharge_code in [2, 20, 5, 50]:
                    self.correct = False
                    self.bad_endpoint = True

            self.correct = not self.bad_endpoint

            if self.stroke_episode and self.correct:
                self.censors(StudyData().first_day_of_study, StudyData().last_day_of_study)

        self.open = False

    def censors(self, first_day_of_study, last_day_of_study):

        # Censorships and missing "tail" (FILTERS)
        if len(self.event_list) > 0:

            if first_day_of_study is not None:

                first_event = self.event_list[0]

                first_day_of_study_with_time = \
                    madrid_datetime(datetime.combine(first_day_of_study, datetime.min.time()))
                if first_event.start_time < first_day_of_study_with_time:
                    self.left_censored = True

            if last_day_of_study is not None:

                last_event = self.event_list[-1]

                if not self.left_censored:

                    last_day_of_study_with_time = datetime.combine(last_day_of_study, datetime.min.time())
                    last_day_of_study_with_time = \
                        madrid_datetime(last_day_of_study_with_time + timedelta(hours=23, minutes=59, seconds=59))

                    if last_event.event_type == 'URG' and \
                            last_event.end_time > (last_day_of_study_with_time - timedelta(days=30)):
                        self.right_censored = True



            # if last_event.event_type == 'HOSP' and last_event.discharge_code in [2, 20, 5,  50]:
            #     self.missing_hospital_link = True
            #     ErroneousDataAccount.missing_hospital_link += 1

            # if len(self.event_list) >= 2:
            #     next_to_last_event = self.event_list[-2]
            #
            #     # if next_to_last_event.event_type == 'HOSP' and next_to_last_event.discharge_code in [5, 50]:
            #     #     last_event.long_stay_hospital = True


    def add_location(self, location_history):

        if self.stroke_episode and self.correct:

            if len(self.event_list) > 0:
                reference_time = self.event_list[0].start_time

                if len(location_history.loc[(reference_time >= location_history['from_dt']) &
                                            ((reference_time < location_history['to_dt']) |
                                             location_history['to_dt'].isnull())]['location_id'].values) > 0:

                    # 'int' to guarantee the proper JSON serialization (the 'location_id' is a Pandas internal type)
                    self.location_id = int(location_history.loc[
                        (reference_time >= location_history['from_dt']) &
                        ((reference_time < location_history['to_dt']) |
                         location_history['to_dt'].isnull())]['location_id'].values[0])



    def to_dict(self):
        # Here 'dict' is required to copy the dictionary of the object and avoid the overwriting done by following
        # statements

        output_vars = { 'episode_id': self.episode_id,
                        'stroke': self.stroke_episode,
                        'correct': self.correct,
                        'suspicious': self.suspicious,
                        'left_censored': self.left_censored,
                        'right_censored': self.right_censored,
                        'bad_endpoint': self.bad_endpoint }

        # result = dict(vars(self))
        result = output_vars
        result['event_list'] = [vars(evt) for evt in self.event_list]
        return result

    def to_activity_dict(self):
        result = []
        for evt in self.event_list:
            result = result + evt.to_activity_dict(self.episode_id)
        return result


    def linked_events(self, prev_event: Event, current_event: Event):

        result = False

        if (prev_event.start_time.date() < current_event.start_time.date()) and \
                (prev_event.end_time.date() > current_event.start_time.date()):
            result = False
        else:

            if prev_event.event_type == 'HOSP' and current_event.event_type == 'HOSP':

                # This comparison has been >= previously, now ==
                if prev_event.end_time.date() == current_event.start_time.date():

                    if prev_event.discharge_code in [2, 20, 5, 50]:
                        result = True

                        if prev_event.discharge_code in [5, 50]:
                            current_event.long_stay_hospital = True

                    else:
                        self.bad_endpoint = True

            elif prev_event.event_type == 'HOSP' and current_event.event_type == 'URG':
                # A priori, urgent care after hospitalisation will be treated as a different episode
                if prev_event.end_time.date() == current_event.start_time.date():
                    #print("HOSP " + str(prev_event.event_id) + " -> URG (" + str(current_event.event_id) +
                    #                                         ") with same end_time", end = '')

                    if prev_event.discharge_code in [2, 20]:
                        result = True
                        #print(" LINKED!")
                    else:
                        #print("")
                        pass


            elif prev_event.event_type == 'URG' and current_event.event_type == 'HOSP':

                # General case, with 1 day gap
                if (prev_event.end_time.date() == current_event.start_time.date() or
                        prev_event.end_time.date() + timedelta(days=1) == current_event.start_time.date()):
                    result = True

                # Special check derived from urgent care event '44664323'. End time (exit) was the day after hospital
                # admission. Check second to last time in the event

                if (prev_event.end_time.date() > current_event.start_time.date() and
                        prev_event.second_to_last_time().date() == current_event.start_time.date()):
                    result = True

                if result is True:

                    if prev_event.urgent_care_facility_code == current_event.hospital_code and prev_event.discharge_code != 6:
                        result = False
                        self.bad_endpoint = True

                    if prev_event.urgent_care_facility_code != current_event.hospital_code and prev_event.discharge_code != 2:
                        result = False
                        self.bad_endpoint = True

                # Comparison of previous version of the log generator
                # if (current_event.end_time.date() == prev_event.start_time.date() or
                #         current_event.end_time.date() + timedelta(days=1) == prev_event.start_time.date() or
                #         current_event.discharge_time.date() == prev_event.start_time.date()):

            elif prev_event.event_type == 'URG' and current_event.event_type == 'URG':


                if (prev_event.end_time == current_event.start_time or
                        (prev_event.end_time + timedelta(hours=3) >= current_event.start_time and
                            current_event.start_time > prev_event.end_time)):
                    result = True


                if result is True:

                    if prev_event.urgent_care_facility_code != current_event.urgent_care_facility_code and prev_event.discharge_code != 11:
                        result = False
                        self.bad_endpoint = True

                # if (current_event.end_time == prev_event.start_time or
                #         (current_event.end_time + timedelta(hours=3) >= prev_event.start_time and
                #          prev_event.start_time > current_event.end_time)):

        return result;

    # def event_continuity(self, current_event, next_event=None):
    #
    #     result = True
    #
    #     if (next_event is None):
    #         if current_event.event_type == 'HOSP':
    #             if current_event.discharge_code in [2, 20, 5, 50]:
    #                 result = False
    #                 self.bad_hospital_link = True
    #         elif current_event.event_type == 'URG':
    #             if current_event.discharge_code in [2, 6, 11]:
    #                 result = False
    #                 self.bad_urgent_care_link = True
    #     else:
    #         if current_event.event_type == 'HOSP' and next_event.event_type == 'HOSP':
    #
    #             if current_event.discharge_code not in [2, 20, 5,  50]:
    #                 result = False
    #                 self.bad_hospital_link = True
    #
    #             if current_event.discharge_code in [5, 50]:
    #                 next_event.long_stay_hospital = True
    #
    #         elif current_event.event_type == 'HOSP' and next_event.event_type == 'URG':
    #             pass
    #
    #         elif current_event.event_type == 'URG' and next_event.event_type == 'HOSP':
    #
    #             if current_event.hospital_code == next_event.hospital_code and current_event.discharge_code != 6:
    #                 result = False
    #                 self.bad_urgent_care_link = True
    #
    #             if current_event.hospital_code != next_event.hospital_code and current_event.discharge_code != 2:
    #                 result = False
    #                 self.bad_urgent_care_link = True
    #
    #         elif current_event.event_type == 'URG' and next_event.event_type == 'URG':
    #
    #             if current_event.discharge_code != 11:
    #                 result = False
    #                 self.bad_urgent_care_link = True
    #
    #     return result
