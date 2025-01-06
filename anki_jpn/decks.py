"""Functions/classes for adding notes to target decks with conjugations"""
from typing import List, Dict, Tuple, Optional, Union
from copy import deepcopy

import anki.notes
import anki.collection
from anki.models import NotetypeDict

from anki_jpn.enums import Form, Formality, VerbClass, AdjectiveClass, ModelType
from anki_jpn.models import combo_to_field_name
from anki_jpn.verbs import generate_verb_forms
from anki_jpn.adjectives import generate_adjective_forms
from anki_jpn.config import ConfigManager

class DeckUpdater: # pylint: disable=R0903
    """Class object for updating a target deck with content from source notes

    Parameters
    ----------
    col : anki.collection.Collection
        Collection to which the target deck belongs
    deck_id : int
        ID of the deck where notes will be added/updated
    model : NotetypeDict
        Model (a.k.a. Note Type) to be used for any new cards
    field_map : Dict[str, int]
        Mapping of relevant field names to indices for the source notes
    """

    def __init__(self, col: anki.collection.Collection, deck_id: int, model: NotetypeDict,
                 model_type: ModelType, config: ConfigManager):
        self._col = col
        self._deck_id = deck_id
        self._deck_name = self._col.decks.get(did=self._deck_id)['name']
        self._model = model
        self._model_type = model_type
        self._model_field_map = self._col.models.field_map(self._model)
        self._cfg = config

        self._new = 0
        self._modified = 0
        self._unchanged = 0

    def add_note_to_deck(self, source_note: anki.notes.Note,
                         word_type: Union[VerbClass, AdjectiveClass]) -> None:
        """Add a note to a deck, updating an existing note if a match is found

        Parameters
        ----------
        source_note: anki.notes.Note
            Source note which is being used to generate the conjugation note
        """

        source_model = self._col.models.get(source_note.mid)
        source_model_fields = self._col.models.field_map(source_model)
        relevant_fields = self._cfg.get_model_fields(source_model['name'])

        expression = source_note.fields[source_model_fields[relevant_fields['expression']][0]]
        meaning = source_note.fields[source_model_fields[relevant_fields['meaning']][0]]
        reading = source_note.fields[source_model_fields[relevant_fields['reading']][0]].split('<')[0].strip()

        query = f'"Expression:{expression}" "Meaning:{meaning}"' + \
            f' "Reading:{reading}" "deck:{self._deck_name}" mid:{self._model["id"]}'
        existing_notes = self._col.find_notes(query)
        if existing_notes:
            note = self._col.get_note(existing_notes[0])
            existing_fields = deepcopy(note.fields)
        else:
            note = anki.notes.Note(self._col, self._model)
            note.fields[self._model_field_map['Expression'][0]] = expression
            note.fields[self._model_field_map['Meaning'][0]] = meaning
            note.fields[self._model_field_map['Reading'][0]] = reading

        for t in source_note.tags:
            note.add_tag(t)

        if self._model_type == ModelType.ADJECTIVE:
            conjugations = generate_adjective_forms(reading, word_type)
        else: # ModelType.VERB
            conjugations = generate_verb_forms(reading, word_type)

        self._expand_note(note, conjugations)

        if existing_notes:
            if existing_fields != note.fields:
                self._modified += 1
            else:
                self._unchanged += 1
            self._col.update_note(note)
        else:
            self._new += 1
            self._col.add_note(note, self._deck_id)

    def _expand_note(self, note: anki.notes.Note,
                    forms: List[Tuple[str, Optional[Formality], Form]]) -> None:
        """Expand a note with the provided conjugations

        Parameters
        ----------
        note : anki.notes.Note
            Note to be expanded with conjugations
        forms : List[Tuple[str, Optional[Formality], Form]]
            List of conjugations and their corresponding formality and form information.
        """

        for conjugation, form, formality in forms:
            field_name = combo_to_field_name(form, formality)
            if field_name in self._model_field_map:
                field_index = self._model_field_map[field_name][0]
                note.fields[field_index] = conjugation

class DeckSearcher:
    """Class for searching a source deck for relevant notes and models"""

    def __init__(self, col: anki.collection.Collection, deck_id: int):
        self._col = col
        self._deck_id = deck_id
        self._deck_name = self._col.decks.get(did=self._deck_id)['name']

    def find_verbs(self, config: ConfigManager) -> Tuple[Dict[VerbClass, List[int]], List[str]]:
        results = {}
    
    def find_adjectives(self, config: ConfigManager) -> Tuple[Dict[AdjectiveClass, List[int]], List[str]]:
        results = {}
        relevant_model_names = set()
        notes, model_names = self.find_notes(config.get_tags(self._deck_name, AdjectiveClass.I))
        if notes:
            results[AdjectiveClass.I] = notes
            relevant_model_names.update(model_names)
        notes, model_names = self.find_notes(config.get_tags(self._deck_name, AdjectiveClass.NA))
        if notes:
            results[AdjectiveClass.NA] = notes
            relevant_model_names.update(model_names)
        notes, model_names = self.find_notes(config.get_tags(self._deck_name, AdjectiveClass.GENERAL))
        if notes:
            results[AdjectiveClass.GENERAL] = notes
            relevant_model_names.update(model_names)

        return results, list(relevant_model_names)


    def find_notes(self, tags: List[str]) -> Tuple[List[int], List[str]]:
        if len(tags) == 0:
            return [], []
        elif len(tags) > 1:
            tag_query = "(" + " OR ".join(f"tag:{tag_str}" for tag_str in tags) + ")"
        else:
            tag_query = f"tag:{tags[0]}"
        query = f'{tag_query} "deck:{self._deck_name}"'
        note_ids = self._col.find_notes(query)

        model_ids = set()
        for nid in note_ids:
            note = self._col.get_note(nid)
            model_ids.add(note.mid)
        model_names = [self._col.models.get(mid)['name'] for mid in model_ids]

        return note_ids, model_names