# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

import json
import random
from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from utils.actions import avg_lengths


class ActionSetUserFeats(Action):

    def name(self) -> Text:
        return "action_set_user_feats"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_message = tracker.latest_message['text']
        entities = tracker.latest_message['entities']
        entity_length = sum([len(e['value'].split()) for e in entities])

        intent = tracker.latest_message['intent'].get('name')
        l = len(user_message.split()) - entity_length + len(entities) # count each entity as one word
        if l > avg_lengths[intent]:
            is_talkative = True
        else:
            is_talkative = False
        return [SlotSet("is_talkative", is_talkative)]


class ActionSearchPlaces(Action):

    def name(self) -> Text:
        return "action_search_places"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        entity_to = next(tracker.get_latest_entity_values(entity_type="location_type"), None)

        # Here should be a call to a maps API searching for entity_to
        options = ['option1', 'option2', 'option3']
        if len(options) == 1:
            dispatcher.utter_message(text='One option found: ' + options[0])
        else:
            dispatcher.utter_message(text='Options found: ' + ' and '.join(options))

        return [SlotSet("search_results", options), SlotSet("search_results_count", len(options) == 1)]


class ActionSelectPlace(Action):

    def name(self) -> Text:
        return "action_select_place"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        options = tracker.get_slot('search_results')
        option = options[0]

        entity_number = next(tracker.get_latest_entity_values(entity_type="number"), None)
        if entity_number == 'one':
            option = options[0]
        elif entity_number == 'two':
            option = options[1]
        elif entity_number == 'three':
            option = options[2]

        entity_to = tracker.get_slot('main_destination')
        slot_include_point = tracker.get_slot('include-point')

        if slot_include_point is None:
            slot_include_point = []

        if entity_to is not None:
            slot_include_point.append(option)
            dispatcher.utter_message(text='Stop added: ' + option)
            return [SlotSet("include-point", option)]

        else:
            dispatcher.utter_message(text='Navigating to ' + option)
            return [SlotSet("main_destination", option)]


class ActionFindDestinaton(Action):

    def name(self) -> Text:
        return "action_find_destination"
        
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        entity_to = next(tracker.get_latest_entity_values(entity_type="location", entity_role="to"), None)
        entity_from = next(tracker.get_latest_entity_values(entity_type="location", entity_role="from"), None)
        entity_include_point = next(tracker.get_latest_entity_values(entity_type="location", entity_role="include-point"), None)
        entity_exclude_point = next(tracker.get_latest_entity_values(entity_type="location", entity_role="exclude-point"), None)
        entity_road_type = next(tracker.get_latest_entity_values("road-type"), None)
        entity_route_type = next(tracker.get_latest_entity_values("route-type"), None)
        
        slot_main_destination = tracker.get_slot('main_destination')
        slot_include_point = tracker.get_slot('include-point')

        if entity_from is None:
            entity_from = tracker.get_slot('from')

        if slot_include_point is not None:
            entity_include_point = slot_include_point.append(entity_include_point)

        with open('utils/database.json', 'r', encoding = 'utf-8') as db:
            database = json.load(db)

        if entity_to in database:
            entity_to = database[entity_to]

        if slot_main_destination is None:
            return [SlotSet("main_destination", entity_to), SlotSet("from", entity_from), SlotSet("include-point", entity_include_point), SlotSet("exclude-point", entity_exclude_point), SlotSet("route-type", entity_route_type), SlotSet("road-type", entity_road_type)]
        else:
            return [SlotSet("include-point", entity_to), SlotSet("from", entity_from), SlotSet("exclude-point", entity_exclude_point), SlotSet("route-type", entity_route_type), SlotSet("road-type", entity_road_type)]


class ActionCheckDistance(Action):

    def name(self) -> Text:
        return "action_check_distance_to_destination"
        
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return []

class ActionCheckTime(Action):

    def name(self) -> Text:
        return "action_check_time_to_destination"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return []

class ActionStartNavigation(Action):

    def name(self) -> Text:
        return "action_start_navigation"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        return []


class ActionExcludeStop(Action):

    def name(self) -> Text:
        return "action_exclude_stop"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return []
        
class ActionReprompt(Action):
    """Executes the fallback action and goes back to the previous state
    of the dialogue"""

    def name(self) -> Text:
        return 'action_reprompt'

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
    
        reprompts = ["I'm sorry, I didn't quite understand that. Could you rephrase?",
                     "Sorry, I didn't catch that, can you rephrase?",
                     "Apologies, I didn't understand. Could you please rephrase it?"]
        
        last_reprompt = tracker.get_slot('last_reprompt')
        if last_reprompt in reprompts:
            reprompts.remove(last_reprompt)
        reprompt = random.choice(reprompts)
        
        dispatcher.utter_message(text=reprompt)

        # Revert user message which led to fallback.
        return [SlotSet("last_reprompt", reprompt)]  # , UserUtteranceReverted()

class ActionAddToDatabase(Action):

    def name(self) -> Text:
        return "action_add_to_database"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        entity_location = next(tracker.get_latest_entity_values(entity_type="location"), None)
        entity_db_item_name = next(
            tracker.get_latest_entity_values(entity_type="location", entity_role="to_database"), None)

        with open('utils/database.json', 'r', encoding = 'utf-8') as db:
            database = json.load(db)

        database.update({entity_db_item_name: entity_location})

        with open('utils/database.json', 'w', encoding = 'utf-8') as db:
            json.dump(database, db)

        return []